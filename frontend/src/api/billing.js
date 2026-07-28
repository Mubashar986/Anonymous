import api from './axios';

/**
 * Create a Stripe Checkout Session for subscription upgrade.
 * @returns {Promise<{ checkout_url: string }>}
 */
export const createCheckoutSession = async () => {
  const response = await api.post('/billing/create-checkout-session');
  return response.data;
};

/**
 * Create a Stripe Customer Portal Session for managing active subscriptions.
 * @returns {Promise<{ portal_url: string }>}
 */
export const createPortalSession = async () => {
  const response = await api.post('/billing/create-portal-session');
  return response.data;
};

/**
 * Fetch subscription status details for the logged-in user.
 * @returns {Promise<{ plan: string, status: string, stripe_customer_id: string|null, stripe_subscription_id: string|null, current_period_end: string|null, cancel_at_period_end: boolean }>}
 */
export const getSubscriptionStatus = async () => {
  const response = await api.get('/billing/me');
  return response.data;
};
