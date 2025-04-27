'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getBannedUsers, unbanUser } from '../../../../../lib/modapi';
import Spinner from '../../../../../components/Spinner';

export default function BannedUsersPage() {
  const { communityName } = useParams();
  const [bannedUsers, setBannedUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [processingUsers, setProcessingUsers] = useState({});

  useEffect(() => {
    async function fetchBannedUsers() {
      try {
        setLoading(true);
        const response = await getBannedUsers(communityName);
        setBannedUsers(response.bannedUsers || response);
      } catch (err) {
        console.error('Failed to fetch banned users:', err);
        setError('Failed to load banned users. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchBannedUsers();
  }, [communityName]);

  const handleUnban = async (username) => {
    if (processingUsers[username]) return;
    
    if (!window.confirm(`Are you sure you want to unban ${username} from ${communityName}?`)) {
      return;
    }
    
    try {
      setProcessingUsers(prev => ({ ...prev, [username]: true }));
      await unbanUser(communityName, username);
      
      // Remove the user from the list
      setBannedUsers(prev => prev.filter(user => user.username !== username));
    } catch (err) {
      console.error('Failed to unban user:', err);
      alert(`Failed to unban user: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingUsers(prev => ({ ...prev, [username]: false }));
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Banned Users</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Banned Users</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold">Banned Users</h1>
        <p className="text-gray-600 mt-1">
          Manage users who are banned from participating in your community.
        </p>
      </div>

      {bannedUsers.length === 0 ? (
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
          <h3 className="mt-2 text-lg font-medium text-gray-900">No banned users</h3>
          <p className="mt-1 text-gray-500">
            There are currently no banned users in this community.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Banned Date
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ban Reason
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expiration
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {bannedUsers.map((bannedUser) => (
                <tr key={bannedUser.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-full overflow-hidden bg-gray-100 mr-4">
                        {bannedUser.user_details?.avatar ? (
                          <img 
                            src={bannedUser.user_details.avatar} 
                            alt={`${bannedUser.user_details.username}'s avatar`}
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="h-full w-full flex items-center justify-center bg-indigo-100 text-indigo-500 font-bold text-lg">
                            {bannedUser.user_details?.username.charAt(0).toUpperCase()}
                          </div>
                        )}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {bannedUser.user_details?.username}
                        </div>
                        <div className="text-sm text-gray-500">
                          {bannedUser.user_details?.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(bannedUser.banned_at || bannedUser.updated_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bannedUser.ban_reason || 'No reason provided'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bannedUser.banned_until 
                      ? new Date(bannedUser.banned_until).toLocaleDateString() 
                      : 'Permanent'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleUnban(bannedUser.user_details.username)}
                      disabled={processingUsers[bannedUser.user_details.username]}
                      className="text-indigo-600 hover:text-indigo-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                    >
                      {processingUsers[bannedUser.user_details.username] ? 'Unbanning...' : 'Unban'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 