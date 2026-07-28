import api from './axios';

/**
 * Initiate or retrieve a 1-to-1 conversation with targetUserId.
 */
export const startConversation = async (targetUserId) => {
  const response = await api.post('/conversations', { target_user_id: targetUserId });
  return response.data;
};

/**
 * Fetch active conversations for the authenticated user.
 */
export const getConversations = async (skip = 0, limit = 20) => {
  const response = await api.get(`/conversations?skip=${skip}&limit=${limit}`);
  return response.data;
};

/**
 * Send direct message over REST API.
 */
export const sendMessageREST = async (conversationId, clientMsgId, text) => {
  const response = await api.post(`/conversations/${conversationId}/messages`, {
    client_msg_id: clientMsgId,
    text,
  });
  return response.data;
};

/**
 * Fetch cursor-paginated chat history for a conversation.
 */
export const getMessageHistory = async (conversationId, beforeTimestamp = null, limit = 50) => {
  let url = `/conversations/${conversationId}/messages?limit=${limit}`;
  if (beforeTimestamp) {
    url += `&before_timestamp=${encodeURIComponent(beforeTimestamp)}`;
  }
  const response = await api.get(url);
  return response.data;
};
