"""
Centralized Stripe Client Initialization.

Configures the official Stripe Python SDK with API keys from application settings.
Exposes safety check helper functions to prevent unconfigured API calls.
"""

import logging
import stripe
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize global API key for stripe SDK
stripe.api_key = settings.STRIPE_SECRET_KEY


def is_stripe_configured() -> bool:
    """
    Check if valid Stripe secret keys are configured in environment settings.
    """
    return bool(settings.STRIPE_SECRET_KEY and not settings.STRIPE_SECRET_KEY.endswith("placeholder"))


def get_stripe_client():
    """
    Return configured stripe module instance with up-to-date API key.
    """
    if not is_stripe_configured():
        logger.warning("Stripe API key is unconfigured or set to placeholder!")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe
