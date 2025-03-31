# schemas.py
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.billing import SubscriptionStatus

class PlanBase(BaseModel):
    name: str
    description: str
    price: float
    features: List[str]
    stripe_price_id: str
    stripe_product_id: str
    billing_interval: str
    is_active: bool

class PlanCreate(PlanBase):
    pass

class PlanUpdate(PlanBase):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    features: List[str] | None = None
    stripe_price_id: str | None = None
    stripe_product_id: str | None = None
    billing_interval: str | None = None
    is_active: bool | None = None

class Plan(PlanBase):
    id: int
    
    class Config:
        from_attributes = True  # Allows Pydantic to read data from SQLAlchemy models

class CreateCheckoutSessionRequest(BaseModel):
    plan_id: int

class CheckoutSessionResponse(BaseModel):
    checkout_url: str

class SubscriptionResponse(BaseModel):
    id: int
    user_id: str
    stripe_customer_id: str
    stripe_subscription_id: str
    plan_id: int
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubscriptionWebhookPayload(BaseModel):
    customer: str
    subscription: str
    status: str

class StripeWebhookRequest(BaseModel):
    body: dict
    stripe_signature: str