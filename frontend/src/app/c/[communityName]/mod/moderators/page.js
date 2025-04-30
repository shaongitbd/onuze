'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { fetchAPI } from '../../../../../lib/api';
import Spinner from '../../../../../components/Spinner';

export default function ModeratorsPage() {
  const { communityName } = useParams();
  const [moderators, setModerators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingUsers, setProcessingUsers] = useState({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [username, setUsername] = useState('');
  const [usernameError, setUsernameError] = useState(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchModerators();
  }, [communityName]);

  const fetchModerators = async () => {
    try {
      setLoading(true);
      const response = await fetchAPI(`/communities/${communityName}/moderators/`);
      setModerators(response.results || response);
    } catch (err) {
      console.error('Failed to fetch moderators:', err);
      setError('Failed to load community moderators. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveModerator = async (moderatorId, username) => {
    if (processingUsers[username]) return;
    if (!confirm(`Are you sure you want to remove ${username} as a moderator?`)) return;
    
    try {
      setProcessingUsers(prev => ({ ...prev, [username]: true }));
      await fetchAPI(`/communities/${communityName}/moderators/${moderatorId}/`, {
        method: 'DELETE'
      });
      
      // Update the local state
      setModerators(prev => prev.filter(mod => mod.id !== moderatorId));
    } catch (err) {
      console.error(`Failed to remove moderator ${username}:`, err);
      alert(`Failed to remove moderator: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingUsers(prev => ({ ...prev, [username]: false }));
    }
  };

  const handleAddModerator = async (e) => {
    e.preventDefault();
    if (processing) return;
    
    // Validate username
    if (!username.trim()) {
      setUsernameError('Username is required');
      return;
    }
    
    try {
      setProcessing(true);
      setUsernameError(null);
      
      // First get the user ID by username
      const userSearchResponse = await fetchAPI(`/user/?username=${username}`);
      if (!userSearchResponse.results || userSearchResponse.results.length === 0) {
        setUsernameError('User not found');
        return;
      }
      
      const userId = userSearchResponse.results[0].id;
      
      // Get the community ID
      const communityResponse = await fetchAPI(`/communities/${communityName}/`);
      const communityId = communityResponse.id;
      
      // Add the moderator
      const response = await fetchAPI(`/communities/${communityName}/moderators/`, {
        method: 'POST',
        body: JSON.stringify({
          community: communityId,
          user: userId,
          permissions: {} // Default permissions
        })
      });
      
      // Add the new moderator to the list
      setModerators(prev => [...prev, response]);
      
      // Reset form and close modal
      setUsername('');
      setShowAddModal(false);
    } catch (err) {
      console.error('Failed to add moderator:', err);
      if (err.data && err.data.detail) {
        setUsernameError(err.data.detail);
      } else {
        setUsernameError(err.message || 'Failed to add moderator');
      }
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Community Moderators</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Community Moderators</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">Community Moderators</h1>
              <p className="text-gray-600 mt-1">
                Manage moderators for your community.
              </p>
            </div>
            <button 
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Add Moderator
            </button>
          </div>
        </div>

        {moderators.length === 0 ? (
          <div className="p-6 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">No moderators</h3>
            <p className="mt-1 text-gray-500">
              Get started by adding your first community moderator.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Moderator
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Since
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {moderators.map((moderator) => (
                  <tr key={moderator.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full overflow-hidden bg-gray-100 mr-4">
                          {moderator.user_details?.avatar ? (
                            <img 
                              src={moderator.user_details.avatar} 
                              alt={`${moderator.user_details.username}'s avatar`}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="h-full w-full flex items-center justify-center bg-indigo-100 text-indigo-500 font-bold text-lg">
                              {moderator.user_details?.username.charAt(0).toUpperCase()}
                            </div>
                          )}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {moderator.user_details?.username}
                          </div>
                          <div className="text-sm text-gray-500">
                            {moderator.user_details?.email}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(moderator.appointed_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        moderator.is_owner 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {moderator.is_owner ? 'Owner' : 'Moderator'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {!moderator.is_owner && (
                        <button
                          onClick={() => handleRemoveModerator(moderator.id, moderator.user_details.username)}
                          disabled={processingUsers[moderator.user_details.username]}
                          className="text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                        >
                          {processingUsers[moderator.user_details.username] ? 'Removing...' : 'Remove'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Moderator Modal */}
      {showAddModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleAddModerator}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="sm:flex sm:items-start">
                    <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-indigo-100 sm:mx-0 sm:h-10 sm:w-10">
                      <svg className="h-6 w-6 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                      </svg>
                    </div>
                    <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                      <h3 className="text-lg leading-6 font-medium text-gray-900">
                        Add Moderator
                      </h3>
                      <div className="mt-4">
                        <div>
                          <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                            Username
                          </label>
                          <div className="mt-1">
                            <input
                              type="text"
                              id="username"
                              name="username"
                              value={username}
                              onChange={(e) => setUsername(e.target.value)}
                              className={`shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md ${
                                usernameError ? 'border-red-300' : ''
                              }`}
                              placeholder="Enter username of the user to add as moderator"
                            />
                          </div>
                          {usernameError && (
                            <p className="mt-2 text-sm text-red-600" id="username-error">
                              {usernameError}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    disabled={processing}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {processing ? 'Adding...' : 'Add Moderator'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddModal(false);
                      setUsername('');
                      setUsernameError(null);
                    }}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
} 