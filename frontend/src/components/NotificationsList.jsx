'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { markAllNotificationsAsRead, notificationEvents } from '@/lib/api';
import NotificationItem from './NotificationItem';
import notificationService from '@/lib/websocket';
import { useInfiniteNotifications } from '@/hooks/useInfiniteScroll';

const NotificationsList = () => {
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'unread', 'read'
  const [isConnected, setIsConnected] = useState(false);
  const loadMoreRef = useRef(null);

  // Prepare query params based on active tab
  const getQueryParams = useCallback(() => {
    const params = { limit: 10 }; // Fetch 10 notifications per page
    
    if (activeTab === 'unread') {
      params.is_read = false;
    } else if (activeTab === 'read') {
      params.is_read = true;
    }
    
    return params;
  }, [activeTab]);

  // Use the useInfiniteNotifications hook
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
    refetch
  } = useInfiniteNotifications(getQueryParams(), {
    enabled: true,
    refetchOnWindowFocus: true,
    staleTime: 30000 // 30 seconds
  });

  // Set up intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0]?.isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    const currentRef = loadMoreRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [loadMoreRef, fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Subscribe to notification events for real-time updates
  useEffect(() => {
    // Subscribe to notification events for real-time updates
    const unsubscribe = notificationEvents.subscribe(() => {
      console.log('🔄 Notification event received, refreshing notifications');
      refetch();
    });
    
    // Set up WebSocket listener for real-time notification updates
    const removeListener = notificationService.addListener(data => {
      // Connection status updates
      if (data.type === 'connection_status') {
        setIsConnected(data.status === 'connected');
        
        // On reconnect, refetch data
        if (data.status === 'connected') {
          refetch();
        }
      }
      
      // If we receive a new notification or a read status change, refresh the list
      if (data.type === 'notification' || data.type === 'new_notification' || 
          data.type === 'notification_read' || data.type === 'notification_read_all') {
        refetch();
      }
    });
    
    // Check initial connection status
    setIsConnected(notificationService.isConnected());
    
    return () => {
      unsubscribe();
      removeListener();
    };
  }, [refetch]);

  // Update notification read status in the local state
  const handleNotificationStatusChange = (notificationId, isRead) => {
    // Mark as read via WebSocket for real-time sync if connected
    if (isRead && isConnected) {
      notificationService.markAsRead(notificationId);
    }
    
    // Instead of modifying state locally, refetch to get the latest data
    // This ensures the UI stays in sync with the database
    setTimeout(refetch, 300); // Small delay to allow the backend to process
  };

  // Mark all notifications as read
  const handleMarkAllAsRead = async () => {
    try {
      // Call REST API (for compatibility and fallback)
      await markAllNotificationsAsRead();
      
      // Also mark all as read via WebSocket for real-time sync if connected
      if (isConnected) {
        notificationService.markAllAsRead();
      }
      
      // Refetch to get the updated list
      setTimeout(refetch, 300); // Small delay to allow the backend to process
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  // Calculate unread count from all loaded notifications
  const calculateUnreadCount = () => {
    if (!data) return 0;
    
    return data.pages.flatMap(page => page.results || [])
      .filter(notification => !notification.is_read).length;
  };

  const unreadCount = calculateUnreadCount();

  // Get all notifications from all pages
  const notifications = data ? data.pages.flatMap(page => page.results || []) : [];

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="flex justify-between items-center p-4 border-b">
        <div className="text-lg font-semibold">
          Notifications
          {isConnected && (
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
              Real-time
            </span>
          )}
        </div>
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
        <button 
          className={`flex-1 py-2 text-center text-sm font-medium ${activeTab === 'read' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('read')}
        >
          Read
        </button>
      </div>
      
      <div className="max-h-[70vh] overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center p-8">
            <div className="w-8 h-8 border-4 border-t-blue-500 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin"></div>
          </div>
        ) : isError ? (
          <div className="p-4 text-center text-red-500">
            {error?.message || 'Failed to load notifications. Please try again later.'}
          </div>
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
                isConnected={isConnected}
              />
            ))}
            
            {/* Loading indicator for next page */}
            {hasNextPage && (
              <div 
                ref={loadMoreRef} 
                className="py-4 text-center"
              >
                {isFetchingNextPage ? (
                  <div className="w-6 h-6 mx-auto border-2 border-t-blue-500 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin"></div>
                ) : (
                  <span className="text-sm text-gray-500">Scroll to load more</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsList; 