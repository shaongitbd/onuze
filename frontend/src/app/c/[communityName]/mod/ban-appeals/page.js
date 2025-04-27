'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { 
  getBanAppeals, 
  getBanAppeal, 
  approveBanAppeal, 
  rejectBanAppeal 
} from '../../../../../lib/modapi';
import Spinner from '../../../../../components/Spinner';
import { format } from 'date-fns';

export default function BanAppealsPage() {
  const { communityName } = useParams();
  const [appeals, setAppeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAppeal, setSelectedAppeal] = useState(null);
  const [processingAction, setProcessingAction] = useState(false);
  const [statusFilter, setStatusFilter] = useState('pending'); // pending, approved, rejected, all

  useEffect(() => {
    async function fetchAppeals() {
      try {
        setLoading(true);
        const response = await getBanAppeals(communityName, statusFilter);
        
        // Handle the paginated response format and map the data structure
        if (!response) {
          setAppeals([]);
        } else if (response.results && Array.isArray(response.results)) {
          // Map the response structure to the expected structure
          const mappedAppeals = response.results.map(appeal => ({
            id: appeal.id,
            username: appeal.user?.username || 'Unknown User',
            status: appeal.status || 'pending',
            created_at: appeal.created_at,
            updated_at: appeal.reviewed_at,
            appeal_reason: appeal.reason || '',
            ban_reason: appeal.original_ban_reason || '',
            rejection_reason: appeal.response_to_user || '',
            // Add any other required fields
          }));
          setAppeals(mappedAppeals);
        } else if (Array.isArray(response)) {
          setAppeals(response);
        } else if (response.data && Array.isArray(response.data)) {
          setAppeals(response.data);
        } else if (response.appeals && Array.isArray(response.appeals)) {
          setAppeals(response.appeals);
        } else {
          console.warn('Unexpected response format from getBanAppeals:', response);
          setAppeals([]);
        }
      } catch (err) {
        console.error('Failed to fetch ban appeals:', err);
        setError('Failed to load ban appeals. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchAppeals();
  }, [communityName, statusFilter]);

  const handleSelectAppeal = async (appealId) => {
    if (selectedAppeal?.id === appealId) {
      setSelectedAppeal(null);
      return;
    }
    
    try {
      setProcessingAction(true);
      const response = await getBanAppeal(communityName, appealId);
      
      // Transform the API response to match the expected structure
      const appeal = {
        id: response.id,
        username: response.user?.username || 'Unknown User',
        status: response.status || 'pending',
        created_at: response.created_at,
        updated_at: response.reviewed_at,
        appeal_reason: response.reason || '',
        ban_reason: response.original_ban_reason || '',
        rejection_reason: response.response_to_user || '',
        // Add any other required fields
      };
      
      setSelectedAppeal(appeal);
    } catch (err) {
      console.error('Failed to get ban appeal details:', err);
      alert(`Failed to load appeal details: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleApproveAppeal = async (appealId) => {
    if (!confirm('Are you sure you want to approve this ban appeal? The user will be unbanned from the community.')) {
      return;
    }
    
    try {
      setProcessingAction(true);
      await approveBanAppeal(communityName, appealId);
      
      // Update the local state
      setAppeals(prev => 
        prev.map(appeal => 
          appeal.id === appealId 
            ? { ...appeal, status: 'approved', updated_at: new Date().toISOString() } 
            : appeal
        )
      );
      
      if (selectedAppeal?.id === appealId) {
        setSelectedAppeal(prev => ({ ...prev, status: 'approved', updated_at: new Date().toISOString() }));
      }
    } catch (err) {
      console.error('Failed to approve ban appeal:', err);
      alert(`Failed to approve ban appeal: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleRejectAppeal = async (appealId, reason, internalNotes) => {
    if (!confirm('Are you sure you want to reject this ban appeal? The user will remain banned from the community.')) {
      return;
    }
    
    try {
      setProcessingAction(true);
      await rejectBanAppeal(communityName, appealId, reason);
      
      // Update the local state
      setAppeals(prev => 
        prev.map(appeal => 
          appeal.id === appealId 
            ? { 
                ...appeal, 
                status: 'rejected', 
                rejection_reason: reason, 
                internal_notes: internalNotes,
                updated_at: new Date().toISOString() 
              } 
            : appeal
        )
      );
      
      if (selectedAppeal?.id === appealId) {
        setSelectedAppeal(prev => ({ 
          ...prev, 
          status: 'rejected', 
          rejection_reason: reason,
          internal_notes: internalNotes,
          updated_at: new Date().toISOString() 
        }));
      }
    } catch (err) {
      console.error('Failed to reject ban appeal:', err);
      alert(`Failed to reject ban appeal: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleSubmitRejection = (e) => {
    e.preventDefault();
    const reason = e.target.elements.rejectionReason.value;
    const internalNotes = e.target.elements.internalNotes.value || '';
    
    if (!reason) {
      alert('Please provide a reason for rejection');
      return;
    }
    
    handleRejectAppeal(selectedAppeal.id, reason, internalNotes);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Ban Appeals</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Ban Appeals</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold">Ban Appeals</h1>
        <p className="text-gray-600 mt-1">
          Manage ban appeals for your community.
        </p>
      </div>

      <div className="p-6">
        <div className="mb-6">
          <label htmlFor="statusFilter" className="block text-sm font-medium text-gray-700 mb-1">Filter by status</label>
          <select
            id="statusFilter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="all">All</option>
          </select>
        </div>

        {appeals.length === 0 ? (
          <div className="text-center p-8">
            <p className="text-gray-500">No ban appeals found.</p>
          </div>
        ) : (
          <div className="flex flex-col lg:flex-row space-y-6 lg:space-y-0 lg:space-x-6">
            <div className="w-full lg:w-1/2">
              <h3 className="text-lg font-medium mb-3">Appeals List</h3>
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
                <ul role="list" className="divide-y divide-gray-200">
                  {appeals.map((appeal) => (
                    <li 
                      key={appeal.id}
                      className={`hover:bg-gray-50 cursor-pointer ${selectedAppeal?.id === appeal.id ? 'bg-gray-50' : ''}`}
                      onClick={() => handleSelectAppeal(appeal.id)}
                    >
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-indigo-600 truncate">
                            {appeal.username}
                          </p>
                          <div className="ml-2 flex-shrink-0 flex">
                            <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                              ${appeal.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                                appeal.status === 'approved' ? 'bg-green-100 text-green-800' : 
                                'bg-red-100 text-red-800'}`}>
                              {appeal.status.charAt(0).toUpperCase() + appeal.status.slice(1)}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="flex items-center text-sm text-gray-500">
                              Submitted: {format(new Date(appeal.created_at), 'MMM d, yyyy')}
                            </p>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="w-full lg:w-1/2">
              {selectedAppeal ? (
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                  <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">Appeal Details</h3>
                  </div>
                  <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                    <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">User</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedAppeal.username}</dd>
                      </div>
                      <div className="sm:col-span-1">
                        <dt className="text-sm font-medium text-gray-500">Status</dt>
                        <dd className={`mt-1 text-sm ${
                          selectedAppeal.status === 'pending' ? 'text-yellow-700' : 
                          selectedAppeal.status === 'approved' ? 'text-green-700' : 
                          'text-red-700'
                        }`}>
                          {selectedAppeal.status.charAt(0).toUpperCase() + selectedAppeal.status.slice(1)}
                        </dd>
                      </div>
                      <div className="sm:col-span-2">
                        <dt className="text-sm font-medium text-gray-500">Ban Reason</dt>
                        <dd className="mt-1 text-sm text-gray-900">{selectedAppeal.ban_reason || 'No reason provided'}</dd>
                      </div>
                      <div className="sm:col-span-2">
                        <dt className="text-sm font-medium text-gray-500">Appeal Reason</dt>
                        <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                          {selectedAppeal.appeal_reason}
                        </dd>
                      </div>
                      <div className="sm:col-span-2">
                        <dt className="text-sm font-medium text-gray-500">Submitted On</dt>
                        <dd className="mt-1 text-sm text-gray-900">
                          {format(new Date(selectedAppeal.created_at), 'MMMM d, yyyy h:mm a')}
                        </dd>
                      </div>
                      
                      {selectedAppeal.status === 'rejected' && (
                        <>
                          <div className="sm:col-span-2">
                            <dt className="text-sm font-medium text-gray-500">Rejection Reason</dt>
                            <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                              {selectedAppeal.rejection_reason || 'No reason provided'}
                            </dd>
                          </div>
                          {selectedAppeal.internal_notes && (
                            <div className="sm:col-span-2">
                              <dt className="text-sm font-medium text-gray-500">Internal Notes</dt>
                              <dd className="mt-1 text-sm text-gray-900 bg-yellow-50 p-2 rounded whitespace-pre-wrap">
                                {selectedAppeal.internal_notes}
                              </dd>
                            </div>
                          )}
                        </>
                      )}
                      
                      {selectedAppeal.status === 'pending' && (
                        <div className="sm:col-span-2 mt-2">
                          <div className="flex space-x-3">
                            <button
                              onClick={() => handleApproveAppeal(selectedAppeal.id)}
                              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                              disabled={processingAction}
                            >
                              {processingAction ? 'Processing...' : 'Approve & Unban'}
                            </button>
                            <button
                              type="button"
                              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                              data-bs-toggle="modal" 
                              data-bs-target="#rejectModal"
                              disabled={processingAction}
                            >
                              Reject
                            </button>
                          </div>
                          
                          <div className="mt-4 bg-gray-50 p-4 rounded-md">
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Reject Appeal</h4>
                            <form onSubmit={handleSubmitRejection}>
                              <div className="mb-3">
                                <label htmlFor="rejectionReason" className="block text-sm font-medium text-gray-700">
                                  Response to user (required)
                                </label>
                                <textarea
                                  id="rejectionReason"
                                  name="rejectionReason"
                                  rows={3}
                                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 mt-1 block w-full sm:text-sm border border-gray-300 rounded-md"
                                  placeholder="Message sent to the user explaining why their appeal was rejected..."
                                  required
                                ></textarea>
                              </div>
                              <div className="mb-3">
                                <label htmlFor="internalNotes" className="block text-sm font-medium text-gray-700">
                                  Internal notes (optional)
                                </label>
                                <textarea
                                  id="internalNotes"
                                  name="internalNotes"
                                  rows={2}
                                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 mt-1 block w-full sm:text-sm border border-gray-300 rounded-md"
                                  placeholder="Notes visible only to moderators and admins..."
                                ></textarea>
                              </div>
                              <button
                                type="submit"
                                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                                disabled={processingAction}
                              >
                                {processingAction ? 'Processing...' : 'Submit Rejection'}
                              </button>
                            </form>
                          </div>
                        </div>
                      )}
                    </dl>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 border-2 border-dashed border-gray-300 rounded-lg">
                  <p className="text-gray-500 text-center">
                    Select an appeal from the list to view details
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 