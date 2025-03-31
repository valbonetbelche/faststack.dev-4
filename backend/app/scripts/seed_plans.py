import os
import time
import traceback
import stripe
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

# Set up proper imports from your current project
from app.db.session import get_db, engine
from app.models.billing import SubscriptionPlan, Base
from app.config.settings import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY must be set")

SUBSCRIPTION_PLANS = [
    {
        'name': 'Starter',
        'description': 'Perfect for small projects and individuals',
        'price': 9.99,
        'features': [
            'Up to 1,000 API calls/month',
            'Basic support',
            'Core features',
            'Email support'
        ]
    },
    {
        'name': 'Professional',
        'description': 'Ideal for growing businesses',
        'price': 29.99,
        'features': [
            'Up to 10,000 API calls/month',
            'Priority support',
            'Advanced features',
            'Email + Chat support',
            'Advanced analytics'
        ]
    },
    {
        'name': 'Enterprise',
        'description': 'For large-scale operations',
        'price': 99.99,
        'features': [
            'Unlimited API calls',
            'Dedicated support',
            'All features included',
            '24/7 Priority support',
            'Custom integrations',
            'Advanced security features'
        ]
    }
]

def wait_for_table(db: Session, max_retries: int = 5) -> bool:
    """Wait for the subscription_plans table to be ready"""
    for i in range(max_retries):
        inspector = inspect(engine)
        if 'subscription_plans' in inspector.get_table_names():
            print("Table found!")
            return True
        print(f"Table not found, attempt {i+1}/{max_retries}")
        if i < max_retries - 1:
            time.sleep(2)
    return False

def create_stripe_product_and_price(plan_data: dict):
    """Create Stripe product and price for a plan"""
    try:
        product = stripe.Product.create(
            name=plan_data['name'],
            description=plan_data['description'],
            metadata={'plan_tier': plan_data['name'].lower()}
        )
        
        price = stripe.Price.create(
            product=product.id,
            currency='usd',
            unit_amount=int(plan_data['price'] * 100),  # Convert to cents
            recurring={'interval': 'month'}
        )
        
        return product, price
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

def seed_plans():
    """Seed the subscription plans in both Stripe and the local database"""
    db = next(get_db())
    try:
        # Wait for table or create it
        if not wait_for_table(db):
            print("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            
        print("Clearing existing data...")
        db.execute(text('TRUNCATE TABLE customer_subscriptions CASCADE'))
        db.execute(text('TRUNCATE TABLE subscription_plans CASCADE'))
        db.commit()
        
        print("Inserting new plans...")
        for plan_data in SUBSCRIPTION_PLANS:
            try:
                product, price = create_stripe_product_and_price(plan_data)
                
                plan = SubscriptionPlan(
                    name=plan_data['name'],
                    description=plan_data['description'],
                    price=plan_data['price'],
                    features=plan_data['features'],
                    stripe_price_id=price.id,
                    stripe_product_id=product.id,
                    billing_interval='month',
                    is_active=True
                )
                
                db.add(plan)
                print(f"Added plan: {plan_data['name']} (Stripe Price ID: {price.id})")
            
            except Exception as e:
                print(f"Error setting up plan {plan_data['name']}: {str(e)}")
                continue
        
        db.commit()
        print("Successfully seeded subscription plans!")
    
    except Exception as e:
        print(f"Error seeding plans: {str(e)}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_plans()