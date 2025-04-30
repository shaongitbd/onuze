'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { formatDistanceToNow } from 'date-fns';
import { markNotificationAsRead } from '@/lib/api';
import notificationService from '@/lib/websocket';

const NotificationItem = ({ notification, onStatusChange, isConnected = false }) => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  
  // Parse notification data
  const { id, message, created_at, is_read, link_url, notification_type, sender } = notification;

  // Handle clicking on a notification
  const handleClick = async () => {
    // Skip if already loading
    if (isLoading) return;
    
    // If notification has a URL, navigate to that URL
    if (link_url) {
      // Only mark as read if not already read
      if (!is_read) {
        setIsLoading(true);
        try {
          // Call REST API for marking as read (for compatibility and fallback)
          await markNotificationAsRead(id);
          
          // Also mark as read via WebSocket for real-time sync if connected
          if (isConnected) {
            notificationService.markAsRead(id);
          }
          
          // Update parent component's state
          onStatusChange && onStatusChange(id, true);
        } catch (error) {
          console.error('Failed to mark notification as read:', error);
        } finally {
          setIsLoading(false);
        }
      }
      
      // Navigate to the URL
      router.push(link_url);
    }
  };

  // Format the timestamp to be human-readable
  const formattedTime = formatDistanceToNow(new Date(created_at), { addSuffix: true });

  // Determine icon based on notification type
  const getIconByType = (type) => {
    switch (type) {
      case 'comment':
      case 'comment_reply':
        return '/icons/comment.svg';
      case 'like':
        return '/icons/heart.svg';
      case 'follow':
        return '/icons/user-plus.svg';
      case 'mention':
        return '/icons/at-sign.svg';
      default:
        return '/icons/bell.svg';
    }
  };

  const iconSrc = getIconByType(notification_type);
  
  // Get sender avatar or default avatar
  const getAvatarSrc = () => {
    if (sender?.avatar) {
      return sender.avatar;
    }
    
   
    
    return null;
  };
  
  const avatarSrc = getAvatarSrc();

  return (
    <div 
      className={`p-4 border-b cursor-pointer transition duration-200 hover:bg-gray-50 ${!is_read ? 'bg-blue-50' : ''}`}
      onClick={handleClick}
    >
      <div className="flex items-start">
        {/* Icon or user avatar */}
        <div className="mr-3 mt-1">
          {avatarSrc ? (
            <Image 
              src={avatarSrc} 
              alt={sender?.username || 'User'} 
              width={40} 
              height={40} 
              className="rounded-full"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
              <Image 
                src={iconSrc} 
                alt={notification_type} 
                width={20} 
                height={20} 
              />
            </div>
          )}
        </div>
        
        {/* Notification content */}
        <div className="flex-1">
          <div className="text-sm">
            {isLoading ? (
              <span className="text-gray-400">Marking as read...</span>
            ) : (
              <span className={!is_read ? 'font-medium' : ''}>{message}</span>
            )}
          </div>
          <div className="text-xs text-gray-500 mt-1">{formattedTime}</div>
        </div>
        
        {/* Unread indicator */}
        {!is_read && (
          <div className="ml-2 w-2 h-2 bg-blue-500 rounded-full"></div>
        )}
      </div>
    </div>
  );
};

export default NotificationItem; 