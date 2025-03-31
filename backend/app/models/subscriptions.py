# app/models.py
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, ARRAY, MetaData, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from .base import Base

# Create a MetaData instance with schema naming convention
metadata = MetaData(schema='billing')

class SubscriptionStatus(str, enum.Enum):
    INCOMPLETE = 'incomplete'
    INCOMPLETE_EXPIRED = 'incomplete_expired'
    TRIALING = 'trialing'
    ACTIVE = 'active'
    PAST_DUE = 'past_due'
    CANCELED = 'canceled'
    UNPAID = 'unpaid'

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    price = Column(Float)
    features = Column(ARRAY(String))
    stripe_price_id = Column(String, unique=True, index=True)
    stripe_product_id = Column(String, unique=True) 
    billing_interval = Column(String, default='month')
    is_active = Column(Boolean, default=True)

class ScheduledChangeType(str, enum.Enum):
    CANCEL = 'cancel'
    UPGRADE = 'upgrade'
    DOWNGRADE = 'downgrade'

class CustomerSubscription(Base):
    __tablename__ = "customer_subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, nullable=False)
    stripe_subscription_id = Column(String, index=True)
    plan_id = Column(Integer, ForeignKey('billing.subscription_plans.id', ondelete='RESTRICT'))
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.INCOMPLETE)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    scheduled_change_type = Column(SQLEnum(ScheduledChangeType), nullable=True)
    scheduled_change_date = Column(DateTime(timezone=True), nullable=True)
    scheduled_plan_id = Column(Integer, ForeignKey('billing.subscription_plans.id', ondelete='RESTRICT'), nullable=True)
    last_metadata_sync = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plan = relationship("SubscriptionPlan", foreign_keys=[plan_id], backref="subscriptions")
    scheduled_plan = relationship("SubscriptionPlan", foreign_keys=[scheduled_plan_id])

