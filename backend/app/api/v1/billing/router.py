from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.db.session import get_db
from app.models.billing import CustomerSubscription, SubscriptionStatus
from app.models.stripe import stripe_service, StripeServiceError
from app.crud.billing import (
    get_subscription_plans,
    get_subscription_plan_by_id,
    get_subscription_plan_id_from_stripe_price_id,
    upsert_customer_subscription
)
from app.schemas.billing import (
    Plan,
    CheckoutSessionResponse,
    SubscriptionResponse,
    CreateCheckoutSessionRequest
)
from app.api.deps import get_current_user
from app.config.settings import settings
from app.utils.clerk import clerk_client

router = APIRouter()
logger = logging.getLogger(__name__)

# ----- PUBLIC ROUTES

@router.get("/")
def read_root():
    return {"message": "Billing Service Running"}

@router.get("/plans/", response_model=list[Plan])
def get_plans(db: Session = Depends(get_db)):
    plans = get_subscription_plans(db)
    return plans

@router.get("/plans/{plan_id}", response_model=Plan)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get details of a specific plan"""
    plan = get_subscription_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

# ----- PROTECTED ROUTES

@router.post("/subscription/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Checkout session for subscription"""
    try:
        user_email = user_data.get("email")
        user_id = user_data.get("sub")  # Clerk user ID
        
        plan = get_subscription_plan_by_id(db, request.plan_id)
        
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid plan selected")
        
        if not plan.stripe_price_id:
            raise HTTPException(
                status_code=500, 
                detail="Plan not properly configured with Stripe"
            )

        session = stripe_service.create_checkout_session(
            email=user_email,
            user_id=user_id,
            price_id=plan.stripe_price_id,
            success_url=f"{settings.FRONTEND_URL}/dashboard/billing?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/billing"
        )

        return {"checkout_url": session.url}

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to create checkout session"
        )

@router.get("/subscription/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription status"""
    user_id = user_data.get("sub")

    subscription = db.query(CustomerSubscription).filter(
        and_(
            CustomerSubscription.user_id == user_id,
            CustomerSubscription.status != SubscriptionStatus.CANCELED
        )
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return subscription

@router.get("/subscription/portal-session", response_model=dict)
async def get_portal_session(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a Stripe Billing Portal URL for the user"""
    try:
        user_id = user_data.get("sub")
        subscription = db.query(CustomerSubscription).filter(
            and_(
                CustomerSubscription.user_id == user_id,
                CustomerSubscription.status != SubscriptionStatus.CANCELED
            )
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")

        billing_portal_session = stripe_service.create_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/dashboard/billing"
        )
        
        return JSONResponse(
            content={"billing_portal_url": billing_portal_session.url},
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error generating billing portal URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate billing portal URL")
    
@router.post("/subscription/update-metadata")
async def update_subscription_metadata(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Clerk metadata with subscription details"""
    print("Updating subscription metadata")
    user_id = user_data.get("sub")
    print(f"User ID: {user_id}")
    subscription = db.query(CustomerSubscription).filter(
        CustomerSubscription.user_id == user_id
    ).first()
    
    if not subscription:
        print("No active subscription found")
        raise HTTPException(status_code=404, detail="No active subscription found")

    metadata = {
        "subscription_status": subscription.status,
        "subscription_plan": subscription.plan.name,
        "subscription_end": subscription.current_period_end.isoformat(),
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "last_checked": datetime.utcnow().isoformat()
    }
    print(f"Metadata to update: {metadata}")
    await clerk_client.update_user_metadata(user_id, metadata)
    print("Clerk metadata updated successfully")

    return JSONResponse(content={"message": "Metadata updated successfully"}, status_code=200)

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    try:
        body = await request.body()
        stripe_signature = request.headers.get("stripe-signature")
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Stripe-Signature header missing")

        event = stripe_service.verify_webhook(body, stripe_signature)
        
        if event.type == "checkout.session.completed":
            await handle_checkout_completed(event.data.object, db)
        elif event.type == "customer.subscription.updated":
            print("Received webhook for subscription update")
        elif event.type == "customer.subscription.deleted":
            await handle_subscription_cancelled(event.data.object, db)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def handle_checkout_completed(session: dict, db: Session):
    """Handle successful checkout completion"""
    user_id = session.metadata.get("clerk_user_id")
    if not user_id:
        logger.error("No user_id in session metadata")
        return

    subscription_id = session.get("subscription")
    if not subscription_id:
        return

    try:
        subscription = stripe_service.get_subscription(subscription_id)
        plan_id = get_subscription_plan_id_from_stripe_price_id(db, subscription.plan.id)
        
        plan = get_subscription_plan_by_id(db, plan_id)
        if not plan:
            logger.error(f"Plan not found for price ID: {subscription.plan.id}")
            return

        # Update database
        subscription_data = {
            'user_id': user_id,
            'stripe_customer_id': session.customer,
            'stripe_subscription_id': subscription_id,
            'plan_id': plan_id,
            'status': SubscriptionStatus.ACTIVE,
            'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'cancel_at_period_end': subscription.cancel_at_period_end
        }
        upsert_customer_subscription(db, subscription_data)
        # Update Clerk metadata
        metadata = {
            "subscription_status": subscription.status,
            "subscription_plan": plan.name,
            "subscription_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "last_checked": datetime.utcnow().isoformat()
        }
        
        await clerk_client.update_user_metadata(user_id, metadata)
        logger.info(f"Subscription and Clerk metadata updated for user {user_id}")

    except Exception as e:
        logger.error(f"Error handling checkout completed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_subscription_updated(subscription: dict, db: Session):
    """Handle subscription updates from Stripe"""
    try:
        subscription_data = {
            'stripe_subscription_id': subscription.id,
            'status': subscription.status,
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'cancel_at_period_end': subscription.cancel_at_period_end
        }
        
        upsert_customer_subscription(db, subscription_data)
        logger.info(f"Subscription {subscription.id} updated")

    except Exception as e:
        logger.error(f"Error handling subscription update: {str(e)}")

async def handle_subscription_cancelled(subscription: dict, db: Session):
    """Handle subscription cancellations from Stripe"""
    try:
        subscription_data = {
            'stripe_subscription_id': subscription.id,
            'status': SubscriptionStatus.CANCELED
        }
        
        upsert_customer_subscription(db, subscription_data)
        logger.info(f"Subscription {subscription.id} cancelled")

    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {str(e)}")