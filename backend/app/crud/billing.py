from sqlalchemy.orm import Session
from ..models.billing import CustomerSubscription, SubscriptionPlan

def get_subscription_plans(db: Session):
    return db.query(SubscriptionPlan).all()

def get_subscription_plan_by_id(db: Session, plan_id: int):
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()

def get_subscription_plan_id_from_stripe_price_id(db: Session, stripe_price_id: str) -> int:
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.stripe_price_id == stripe_price_id).first()
    if not plan:
        raise ValueError(f"No subscription plan found for Stripe price ID: {stripe_price_id}")
    return plan.id

def upsert_customer_subscription(db: Session, subscription_data: dict):
    db_subscription = db.query(CustomerSubscription).filter(
        CustomerSubscription.user_id == subscription_data['user_id']
    ).first()

    if not db_subscription:
        db_subscription = CustomerSubscription(**subscription_data)
        db.add(db_subscription)
    else:
        for key, value in subscription_data.items():
            setattr(db_subscription, key, value)

    db.commit()
    return db_subscription