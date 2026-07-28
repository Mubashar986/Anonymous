import api from './axios';

/**
 * Request password reset email.
 * @param {string} email
 */
export const requestPasswordReset = async (email) => {
  const response = await api.post(`/auth/forgot-password?email=${encodeURIComponent(email)}`);
  return response.data;
};

/**
 * Reset password with token.
 * @param {string} token
 * @param {string} newPassword
 */
export const resetPassword = async (token, newPassword) => {
  const response = await api.post('/auth/reset-password', {
    token,
    new_password: newPassword,
  });
  return response.data;
};

/**
 * Resend account verification email.
 * @param {string} email
 */
export const resendVerificationEmail = async (email) => {
  const response = await api.post(`/auth/resend-verification?email=${encodeURIComponent(email)}`);
  return response.data;
};

/**
 * Verify account email token.
 * @param {string} token
 */
export const verifyEmailToken = async (token) => {
  const response = await api.get(`/auth/verify-email?token=${encodeURIComponent(token)}`);
  return response.data;
};
