import api from './axios';

/**
 * List active community rooms.
 */
export async function listRooms(skip = 0, limit = 50) {
  const res = await api.get('/rooms', { params: { skip, limit } });
  return res.data;
}

/**
 * Submit a room creation request.
 */
export async function submitRoomRequest(data) {
  const res = await api.post('/rooms/requests', data);
  return res.data;
}

/**
 * Fetch current user's submitted room requests.
 */
export async function getMyRoomRequests() {
  const res = await api.get('/rooms/requests/me');
  return res.data;
}

/**
 * Join a public or private community room.
 */
export async function joinRoom(roomId) {
  const res = await api.post(`/rooms/${roomId}/join`);
  return res.data;
}

/**
 * Voluntarily leave a community room.
 */
export async function leaveRoom(roomId) {
  const res = await api.delete(`/rooms/${roomId}/leave`);
  return res.data;
}

/**
 * List active members of a room.
 */
export async function listRoomMembers(roomId) {
  const res = await api.get(`/rooms/${roomId}/members`);
  return res.data;
}

/**
 * Fetch room chat history.
 */
export async function getRoomHistory(roomId, limit = 50, before = null) {
  const params = { limit };
  if (before) params.before = before;
  const res = await api.get(`/rooms/${roomId}/messages`, { params });
  return res.data;
}

/**
 * [Admin] List room requests for review.
 */
export async function listRoomRequestsAdmin() {
  const res = await api.get('/admin/rooms/requests');
  return res.data;
}

/**
 * [Admin] Approve a room request with optional final_name override.
 */
export async function approveRoomRequestAdmin(requestId, finalName = null) {
  const payload = finalName ? { final_name: finalName } : {};
  const res = await api.post(`/admin/rooms/requests/${requestId}/approve`, payload);
  return res.data;
}

/**
 * [Admin] Reject a room request.
 */
export async function rejectRoomRequestAdmin(requestId) {
  const res = await api.post(`/admin/rooms/requests/${requestId}/reject`);
  return res.data;
}

/**
 * [Admin] Directly create a community room.
 */
export async function createRoomDirectAdmin(data) {
  const res = await api.post('/admin/rooms', data);
  return res.data;
}

/**
 * [Admin] Archive or unarchive a community room.
 */
export async function archiveRoomAdmin(roomId) {
  const res = await api.patch(`/admin/rooms/${roomId}/archive`);
  return res.data;
}

/**
 * [Admin] Remove a member from a community room.
 */
export async function removeRoomMemberAdmin(roomId, userId) {
  const res = await api.delete(`/admin/rooms/${roomId}/members/${userId}`);
  return res.data;
}
