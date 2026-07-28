import api from './axios';

/**
 * Fetch capability status roster for a target user.
 */
export const getUserPermissions = async (userId) => {
  const response = await api.get(`/users/${userId}/permissions`);
  return response.data;
};

/**
 * Set an explicit permission override (ALLOW, DENY, or INHERIT) on a target user.
 */
export const updateUserPermission = async (userId, data) => {
  const response = await api.put(`/users/${userId}/permissions`, data);
  return response.data;
};

/**
 * Fetch immutable audit log history for permission changes on a target user.
 */
export const getUserPermissionAudit = async (userId) => {
  const response = await api.get(`/users/${userId}/permissions/audit`);
  return response.data;
};
