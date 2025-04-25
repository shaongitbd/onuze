'use client';

import { useState, useEffect } from 'react';
import { getNotifications, markAllNotificationsAsRead } from '@/lib/api';
import NotificationItem from './NotificationItem';

const NotificationsList = () => {
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'unread', 'read'

  // Fetch notifications on component mount
  useEffect(() => {
    fetchNotifications();
  }, [activeTab]);

  // Fetch notifications with filter based on active tab
  const fetchNotifications = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = {};
      if (activeTab === 'unread') {
        params.is_read = false;
      } else if (activeTab === 'read') {
        params.is_read = true;
      }
      
      const data = await getNotifications(params);
      setNotifications(data.results || []);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      setError('Failed to load notifications. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  // Update notification read status in the local state
  const handleNotificationStatusChange = (notificationId, isRead) => {
    setNotifications(prevNotifications => 
      prevNotifications.map(notification => 
        notification.id === notificationId 
          ? { ...notification, is_read: isRead } 
          : notification
      )
    );
  };

  // Mark all notifications as read
  const handleMarkAllAsRead = async () => {
    try {
      await markAllNotificationsAsRead();
      // Update local state to reflect all notifications as read
      setNotifications(prevNotifications => 
        prevNotifications.map(notification => ({ ...notification, is_read: true }))
      );
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  // Filter for counting unread notifications
  const unreadCount = notifications.filter(notification => !notification.is_read).length;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="flex justify-between items-center p-4 border-b">
        <div className="text-lg font-semibold">Notifications</div>
        {unreadCount > 0 && (
          <button 
            onClick={handleMarkAllAsRead}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Mark all as read
          </button>
        )}
      </div>
      
      <div className="flex border-b">
        <button 
          className={`flex-1 py-2 text-center text-sm font-medium ${activeTab === 'all' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('all')}
        >
          All
        </button>
        <button 
          className={`flex-1 py-2 text-center text-sm font-medium ${activeTab === 'unread' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('unread')}
        >
          Unread {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>
      
      <div className="max-h-96 overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center p-8">
            <div className="w-8 h-8 border-4 border-t-blue-500 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin"></div>
          </div>
        ) : error ? (
          <div className="p-4 text-center text-red-500">{error}</div>
        ) : notifications.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {activeTab === 'unread' 
              ? 'You have no unread notifications.' 
              : activeTab === 'read' 
                ? 'You have no read notifications.' 
                : 'You have no notifications yet.'}
          </div>
        ) : (
          <div>
            {notifications.map(notification => (
              <NotificationItem 
                key={notification.id} 
                notification={notification}
                onStatusChange={handleNotificationStatusChange}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsList; 