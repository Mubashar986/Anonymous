import api from './axios';

/**
 * Fetch public profile details for a selected target user or writer.
 * 
 * @param {string} userId - UUID of the target user/writer profile to fetch.
 * @param {number} [skip=0] - Offset pagination index for writer articles.
 * @param {number} [limit=10] - Page size limit for writer articles.
 * @returns {Promise<Object>} Safe UserProfileResponse payload.
 */
export const getUserProfile = async (userId, skip = 0, limit = 10) => {
  const response = await api.get(`/users/${userId}/profile`, {
    params: { skip, limit },
  });
  return response.data;
};
