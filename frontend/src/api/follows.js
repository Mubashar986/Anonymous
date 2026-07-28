import api from './axios';

/**
 * Follow a target user account.
 * @param {string} targetUserId - UUID of user to follow
 */
export const followUser = async (targetUserId) => {
  const response = await api.post('/follows', { target_user_id: targetUserId });
  return response.data;
};

/**
 * Unfollow a target user account.
 * @param {string} targetUserId - UUID of user to unfollow
 */
export const unfollowUser = async (targetUserId) => {
  const response = await api.delete(`/follows/${targetUserId}`);
  return response.data;
};

/**
 * Fetch list of accounts followed by current user.
 */
export const getFollowing = async (skip = 0, limit = 20) => {
  const response = await api.get(`/follows/following?skip=${skip}&limit=${limit}`);
  return response.data;
};

/**
 * Fetch list of accounts following current user.
 */
export const getFollowers = async (skip = 0, limit = 20) => {
  const response = await api.get(`/follows/followers?skip=${skip}&limit=${limit}`);
  return response.data;
};

/**
 * Fetch discoverable accounts eligible to follow.
 */
export const getDiscoverableUsers = async (skip = 0, limit = 20) => {
  const response = await api.get(`/users/discover?skip=${skip}&limit=${limit}`);
  return response.data;
};
