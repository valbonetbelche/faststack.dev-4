from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.db.session import get_db
from app.models.billing import CustomerSubscription, SubscriptionStatus, ScheduledChangeType
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
from app.utils.redis import cached
from app.api.middleware.rate_limiter import get_limit

router = APIRouter()
logger = logging.getLogger(__name__)

# ----- PUBLIC ROUTES

@router.get("/")
def read_root():
    return {"message": "Billing Service Running"}

@router.get("/plans/", response_model=list[Plan])
@cached(ttl=3600, key_prefix="billing_plans")
def get_plans(request: Request, db: Session = Depends(get_db)):
    plans = get_subscription_plans(db)
    return plans

@router.get("/plans/{plan_id}", response_model=Plan)
@cached(ttl=3600, key_prefix="billing:plan:{plan_id}")
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
@cached(ttl=60, key_prefix="user:{user_id}:subscription")
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
        "last_checked": datetime.now(datetime.timezone.utc).isoformat()
    }
    print(f"Metadata to update: {metadata}")
    await clerk_client.update_user_metadata(user_id, metadata)
    print("Clerk metadata updated successfully")

    return JSONResponse(content={"message": "Metadata updated successfully"}, status_code=200)

@router.post("/webhook/stripe", dependencies=[Depends(get_limit("webhooks"))])
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events"""
    try:
        body = await request.body()
        stripe_signature = request.headers.get("stripe-signature")
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Stripe-Signature header missing")

        event = stripe_service.verify_webhook(body, stripe_signature)
        
        if event.type == "customer.subscription.created":
            await handle_subscription_created(event.data.object, db)
        elif event.type == "customer.subscription.updated":
            await handle_subscription_updated(event.data.object, db)
        elif event.type == "customer.subscription.deleted":
            await handle_subscription_deleted(event.data.object, db)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        if isinstance(e, StripeServiceError):  # Example: Stripe-specific error
            raise HTTPException(status_code=400, detail="Invalid Stripe request")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def handle_subscription_created(subscription: dict, db: Session):
    """Handle successful checkout completion"""
    try:
        # Try to get user_id from subscription metadata first
        user_id = subscription.metadata.get("clerk_user_id")
        print(f"User ID from metadata: {user_id}")
        # If not found in subscription, try to look up via customer ID
        if not user_id:
            customer_id = subscription.customer
            existing_sub = db.query(CustomerSubscription).filter(
                CustomerSubscription.stripe_customer_id == customer_id
            ).first()
            
            if existing_sub:
                user_id = existing_sub.user_id
            else:
                logger.error("No user_id found in subscription metadata or existing records")
                return  # Don't raise error since Stripe will retry
                
        # Rest of your handling logic...
        plan_id = get_subscription_plan_id_from_stripe_price_id(db, subscription.plan.id)
        plan = get_subscription_plan_by_id(db, plan_id)
        print(f"Plan ID: {plan_id}, Plan: {plan}")
        # Update database
        subscription_data = {
            'user_id': user_id,
            'stripe_customer_id': subscription.customer,
            'stripe_subscription_id': subscription.id,
            'plan_id': plan_id,
            'status': SubscriptionStatus(subscription.status),
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

    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to handle subscription creation")

async def handle_subscription_updated(subscription: dict, db: Session):
    """Handle subscription updates from Stripe including cancellations"""
    try:
        # First try to get the user_id from metadata (like in created handler)
        user_id = subscription.metadata.get("clerk_user_id")
        # If not in metadata, look up via subscription ID
        if not user_id:
            existing_sub = db.query(CustomerSubscription).filter(
                CustomerSubscription.stripe_subscription_id == subscription.id
            ).first()
            if existing_sub:
                user_id = existing_sub.user_id
            else:
                logger.error(f"No existing subscription found for {subscription.id}")
                return False  # Trigger retry

        # Prepare base update data
        subscription_data = {
            'user_id': user_id,  # Ensure user_id is included
            'status': SubscriptionStatus(subscription.status),
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'stripe_subscription_id': subscription.id  # Ensure we're updating the right record
        }

        # Determine the actual cancellation scenario
        is_cancelling = subscription.cancel_at is not None
        is_period_end_cancellation = is_cancelling and subscription.cancel_at_period_end
        is_custom_date_cancellation = is_cancelling and not subscription.cancel_at_period_end

        if is_cancelling:
            # All cancellations (both period-end and custom date)
            subscription_data.update({
                'cancel_at': datetime.fromtimestamp(subscription.cancel_at),
                'scheduled_change_type': 'cancel',
                'scheduled_change_date': datetime.fromtimestamp(subscription.cancel_at),
            })

            if is_period_end_cancellation:
                subscription_data.update({
                    'cancel_at_period_end': True,
                })
                logger.info(f"Period-end cancellation scheduled for {subscription.id}")
            else:
                subscription_data.update({
                    'cancel_at_period_end': False,
                })
                logger.info(f"Custom date cancellation scheduled for {subscription.id} at {subscription.cancel_at}")
        else:
            # No cancellation scheduled
            subscription_data.update({
                'cancel_at': None,
                'cancel_at_period_end': False,
                'scheduled_change_type': None,
                'scheduled_change_date': None
            })
            logger.info(f"Subscription {subscription.id} cancellation removed")


        # Update database
        upsert_customer_subscription(db, subscription_data)
        logger.info(f"Subscription {subscription.id} updated in database")
        
        # Update Clerk metadata
        plan = get_subscription_plan_by_id(db, subscription_data.get('plan_id'))
        metadata = {
            "subscription_status": subscription.status,
            "subscription_plan": plan.name if plan else "Unknown",
            "subscription_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "last_checked": datetime.utcnow().isoformat()
        }
        
        await clerk_client.update_user_metadata(user_id, metadata)
        logger.info(f"Subscription {subscription.id} updated for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error handling subscription update: {str(e)}")
        return False  # Trigger retry

async def handle_subscription_deleted(subscription: dict, db: Session):
    """Handle subscription deletion (final cancellation) from Stripe"""
    try:
        # Get user_id from metadata or existing record
        user_id = subscription.metadata.get("clerk_user_id")
        if not user_id:
            existing_sub = db.query(CustomerSubscription).filter(
                CustomerSubscription.stripe_subscription_id == subscription.id
            ).first()
            if existing_sub:
                user_id = existing_sub.user_id
            else:
                logger.error(f"No user found for deleted subscription {subscription.id}")
                return False

        # Update database - mark as fully canceled
        subscription_data = {
            'user_id': user_id,
            'stripe_subscription_id': subscription.id,
            'status': SubscriptionStatus.CANCELED,
            'canceled_at': datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
            'ended_at': datetime.fromtimestamp(subscription.ended_at) if subscription.ended_at else None,
            'cancel_at_period_end': False,
            'cancel_at': None,
            'scheduled_change_type': None,
            'scheduled_change_date': None
        }

        upsert_customer_subscription(db, subscription_data)
        
        # Get plan info for metadata
        plan = get_subscription_plan_by_id(db, subscription_data.get('plan_id'))

        # Update Clerk metadata
        metadata = {
            "subscription_status": "",
            "subscription_plan": "",
            "subscription_end": "",
            "cancel_at_period_end": "",
            "cancel_at": "",
            "last_checked": datetime.utcnow().isoformat()
        }
        
        await clerk_client.update_user_metadata(user_id, metadata)
        logger.info(f"Subscription {subscription.id} fully canceled for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error handling subscription deletion: {str(e)}", exc_info=True)
        return False