'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import notificationService from '@/lib/websocket';
import { notificationEvents } from '@/lib/api';

/**
 * Provider component that initializes and manages WebSocket connections
 * This ensures WebSockets are connected when the app loads and a user is authenticated
 */
const WebSocketProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [lastConnectionState, setLastConnectionState] = useState(false);
  const [hasNotificationListeners, setHasNotificationListeners] = useState(false);

  // Check if notification listeners are properly setup 
  useEffect(() => {
    // Check current listeners count
    const checkListeners = () => {
      const listenerCount = notificationEvents.listeners.size;
      console.log(`📢 Current notification listener count: ${listenerCount}`);
      setHasNotificationListeners(listenerCount > 0);
    };
    
    // Subscribe to notification events to monitor when listeners change
    const unsubscribe = notificationService.addListener(data => {
      if (data.type === 'new_notification') {
        console.log('📣 WebSocketProvider detected new notification:', data);
        // Check listeners after a short delay to allow components to register
        setTimeout(checkListeners, 100);
      }
    });
    
    // Run initial check
    checkListeners();
    
    // Check listeners periodically
    const intervalId = setInterval(checkListeners, 5000);
    
    return () => {
      unsubscribe();
      clearInterval(intervalId);
    };
  }, []);

  // Initialize WebSocket when component mounts
  useEffect(() => {
    // Initialize the WebSocket service
    notificationService.initialize();
    
    console.log('WebSocketProvider mounted, initialized notification service');
    
    // Add connection status listener
    const removeListener = notificationService.addListener(data => {
      if (data.type === 'connection_status') {
        const isConnected = data.status === 'connected';
        console.log(`WebSocket connection status changed to: ${data.status}`);
        
        // Only log when state changes to avoid spam
        if (isConnected !== lastConnectionState) {
          setLastConnectionState(isConnected);
          console.log(`WebSocket is now ${isConnected ? 'connected' : 'disconnected'}`);
        }
      }
    });
    
    // Clean up function will be called when component unmounts
    return () => {
      removeListener();
      // No need to disconnect on unmount, as we want to keep the connection
      // across route changes. We'll let the beforeunload event handle cleanup.
    };
  }, [lastConnectionState]);

  // Reconnect when authentication status changes
  useEffect(() => {
    if (isAuthenticated && user) {
      console.log('User authenticated, ensuring WebSocket connection');
      // Make sure we're connected when user is authenticated
      notificationService.connect();
    }
  }, [isAuthenticated, user]);

  // Simply render children
  return children;
};

export default WebSocketProvider; 