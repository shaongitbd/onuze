'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getNotificationCount } from '@/lib/api';

const NotificationBadge = () => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  // Fetch unread notification count on component mount and periodically
  useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        setLoading(true);
        const data = await getNotificationCount();
        console.log('Notification count data:', data);
        setUnreadCount(data.unread_count || 0);
      } catch (error) {
        console.error('Failed to fetch notification count:', error);
      } finally {
        setLoading(false);
      }
    };

    // Fetch initially
    fetchUnreadCount();

    // Set up interval to fetch every minute
    const intervalId = setInterval(fetchUnreadCount, 60000);

    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, []);

  return (
    <Link
      href="/notifications"
      className="relative inline-flex items-center p-2 text-gray-500 hover:text-red-600 rounded-full hover:bg-gray-100 transition-colors mr-2"
      aria-label="Notifications"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      
      {!loading && unreadCount > 0 && (
        <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </Link>
  );
};

export default NotificationBadge; 