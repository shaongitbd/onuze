'use client';

import React, { useState } from 'react';

export default function BanUserModal({ isOpen, onClose, onConfirmBan, username, isLoading }) {
  const [reason, setReason] = useState('');
  const [duration, setDuration] = useState(''); // Empty string for permanent, number for days

  const handleConfirm = () => {
    onConfirmBan(reason, duration === '' ? null : parseInt(duration));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Ban User: u/{username}</h3>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={isLoading}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="mb-4">
          <label htmlFor="banReason" className="block text-sm font-medium text-gray-700 mb-1">Reason for ban (required)</label>
          <textarea
            id="banReason"
            className="w-full px-3 py-2 text-gray-700 border rounded-md focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent"
            rows="3"
            placeholder="Enter the reason for banning this user..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={isLoading}
          ></textarea>
        </div>
        
        <div className="mb-6">
          <label htmlFor="banDuration" className="block text-sm font-medium text-gray-700 mb-1">Ban duration</label>
          <select 
            id="banDuration"
            className="w-full px-3 py-2 text-gray-700 border rounded-md focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent bg-white"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            disabled={isLoading}
          >
            <option value="">Permanent</option>
            <option value="1">1 Day</option>
            <option value="3">3 Days</option>
            <option value="7">7 Days</option>
            <option value="14">14 Days</option>
            <option value="30">30 Days</option>
            <option value="90">90 Days</option>
          </select>
        </div>

        <div className="mt-4 flex justify-end space-x-2">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 rounded hover:bg-gray-100 border border-gray-300"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button 
            onClick={handleConfirm}
            className={`px-4 py-2 text-sm text-white rounded ${isLoading || !reason.trim() ? 'bg-red-300 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'}`}
            disabled={isLoading || !reason.trim()}
          >
            {isLoading ? 'Banning...' : 'Confirm Ban'}
          </button>
        </div>
      </div>
    </div>
  );
} 