# models/stripe.py
import stripe
from typing import Optional
import os
from fastapi import HTTPException


class StripeServiceError(Exception):
    pass

class StripeService:
    def __init__(self):
        self.stripe = stripe
        stripe_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe_key:
            raise ValueError("STRIPE_SECRET_KEY must be set")
        self.stripe.api_key = stripe_key

    def create_checkout_session(
        self,
        email: str,
        user_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout session for subscription"""
        try:
            # First, check if customer exists
            customers = self.stripe.Customer.list(email=email)
            
            if customers.data:
                customer = customers.data[0]
            else:
                # Create a new customer if one doesn't exist
                customer = self.stripe.Customer.create(
                    email=email,
                    metadata={'clerk_user_id': user_id}
                )

            # Create the checkout session
            session = self.stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                mode='subscription',
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'clerk_user_id': user_id
                },
                subscription_data={
                    'metadata': {
                        'clerk_user_id': user_id
                    }
                }
            )

            return session

        except self.stripe.error.StripeError as e:
            raise StripeServiceError(f"Stripe error: {str(e)}")
        except Exception as e:
            raise StripeServiceError(f"Unexpected error: {str(e)}")

    def verify_webhook(self, payload: bytes, signature: str) -> stripe.Event:
        """Verify Stripe webhook signature and return the event"""
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            raise StripeServiceError("Webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise StripeServiceError("Invalid signature")
        except Exception as e:
            raise StripeServiceError(f"Could not verify Webhook, error: {str(e)}")

    def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Retrieve subscription details from Stripe"""
        try:
            return self.stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            raise StripeServiceError(f"Error retrieving subscription: {str(e)}")
        
    def create_portal_session(self, customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create a Stripe Billing Portal session for a customer"""
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session
        except self.stripe.error.StripeError as e:
            raise StripeServiceError(f"Error creating billing portal session: {str(e)}")
        except Exception as e:
            raise StripeServiceError(f"Unexpected error: {str(e)}")

# Create a singleton instance
stripe_service = StripeService()