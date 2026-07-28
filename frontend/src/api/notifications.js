import client from './axios';

export const fetchUnreadCount = async () => {
  const res = await client.get('/notifications/unread-count');
  return res.data;
};

export const fetchNotifications = async (page = 1, size = 20, unreadOnly = false) => {
  const res = await client.get('/notifications', {
    params: { page, size, unread_only: unreadOnly },
  });
  return res.data;
};

export const markNotificationRead = async (notificationId) => {
  const res = await client.patch(`/notifications/${notificationId}/read`);
  return res.data;
};

export const markAllNotificationsRead = async () => {
  const res = await client.post('/notifications/read-all');
  return res.data;
};
