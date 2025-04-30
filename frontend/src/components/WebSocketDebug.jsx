'use client';

import { useState, useEffect } from 'react';
import notificationService from '@/lib/websocket';

/**
 * WebSocket debug component to show connection status and message activity
 * Add this to any page to verify WebSocket functionality
 */
const WebSocketDebug = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState({});
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Check connection status immediately
    setIsConnected(notificationService.isConnected());
    updateStatus();

    // Add listener for WebSocket messages
    const removeListener = notificationService.addListener(data => {
      // Update connection status
      if (data.type === 'connection_status') {
        setIsConnected(data.status === 'connected');
      }
      
      // Add message to list
      setMessages(prev => {
        const newMessages = [...prev, {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          data
        }];
        
        // Keep last 10 messages
        if (newMessages.length > 10) {
          return newMessages.slice(-10);
        }
        return newMessages;
      });
      
      updateStatus();
    });
    
    // Update status every second
    const intervalId = setInterval(updateStatus, 1000);
    
    return () => {
      removeListener();
      clearInterval(intervalId);
    };
  }, []);
  
  const updateStatus = () => {
    setStatus(notificationService.getStatus());
  };
  
  const sendPing = () => {
    notificationService.sendPing();
  };
  
  const reconnect = () => {
    notificationService.connect();
  };

  if (!isExpanded) {
    return (
      <div 
        className="fixed bottom-4 right-4 bg-gray-800 text-white p-2 rounded-full shadow-lg cursor-pointer z-50"
        onClick={() => setIsExpanded(true)}
        title="WebSocket Debug"
      >
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white p-4 rounded-lg shadow-lg w-80 z-50 border border-gray-300">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold text-gray-800">WebSocket Debug</h3>
        <button
          onClick={() => setIsExpanded(false)}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>
      
      <div className="mb-2 flex items-center">
        <span className="font-medium mr-2">Status:</span>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      
      <div className="mb-2">
        <span className="font-medium text-sm">Ready State: </span>
        <span className="text-sm">{status.readyState}</span>
      </div>
      
      <div className="mb-2">
        <span className="font-medium text-sm">Messages: </span>
        <span className="text-sm">{status.messageCount || 0}</span>
      </div>
      
      <div className="flex space-x-2 mb-2">
        <button
          onClick={sendPing}
          className="bg-blue-500 hover:bg-blue-600 text-white text-xs px-2 py-1 rounded"
        >
          Send Ping
        </button>
        <button
          onClick={reconnect}
          className="bg-gray-500 hover:bg-gray-600 text-white text-xs px-2 py-1 rounded"
        >
          Reconnect
        </button>
      </div>
      
      <div className="text-xs font-medium mb-1">Recent Messages:</div>
      <div className="bg-gray-100 p-2 rounded-md h-32 overflow-y-auto text-xs">
        {messages.length === 0 ? (
          <div className="text-gray-500 italic">No messages yet</div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className="mb-1 pb-1 border-b border-gray-200">
              <div className="font-medium">
                {new Date(msg.timestamp).toLocaleTimeString()} - {msg.data.type}
              </div>
              <div className="truncate">
                {JSON.stringify(msg.data)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default WebSocketDebug; 