'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getMembers, banUser, removeMember } from '../../../../../lib/modapi';
import Link from 'next/link';
import Spinner from '../../../../../components/Spinner';
import BanUserModal from '../../../../../components/BanUserModal';

export default function MembersPage() {
  const { communityName } = useParams();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingMembers, setProcessingMembers] = useState({});
  const [selectedMember, setSelectedMember] = useState(null);
  const [showBanModal, setShowBanModal] = useState(false);
  const [banTargetUser, setBanTargetUser] = useState(null);
  const [banLoading, setBanLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchMembers() {
      try {
        setLoading(true);
        const response = await getMembers(communityName);
        setMembers(response.members || response);
      } catch (err) {
        console.error('Failed to fetch members:', err);
        setError('Failed to load members. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchMembers();
  }, [communityName]);

  const handleBanUser = async (username) => {
    if (processingMembers[username]) return;
    
    setBanTargetUser(username);
    setShowBanModal(true);
  };

  const confirmBanUser = async (reason, durationDays) => {
    try {
      if (!banTargetUser) {
        console.error('Missing username for ban');
        return;
      }
      
      setBanLoading(true);
      setProcessingMembers(prev => ({ ...prev, [banTargetUser]: true }));
      
      // Prepare ban options
      const options = {
        reason: reason,
        duration_days: durationDays
      };
      
      await banUser(communityName, banTargetUser, options);
      
      // Remove the user from the list
      setMembers(prev => prev.filter(member => member.user_details.username !== banTargetUser));
      
      // Close the modal
      setShowBanModal(false);
      setBanTargetUser(null);
      
      alert(`User ${banTargetUser} has been banned from ${communityName}`);
    } catch (err) {
      console.error('Failed to ban user:', err);
      alert(`Failed to ban user: ${err.message || 'Unknown error'}`);
    } finally {
      if (banTargetUser) {
        setProcessingMembers(prev => ({ ...prev, [banTargetUser]: false }));
        setBanLoading(false);
      }
    }
  };

  const handleRemoveMember = async (username) => {
    if (processingMembers[username]) return;
    
    if (!confirm(`Are you sure you want to remove ${username} from ${communityName}?`)) {
      return;
    }
    
    try {
      setProcessingMembers(prev => ({ ...prev, [username]: true }));
      await removeMember(communityName, username);
      
      // Remove the member from the list
      setMembers(prev => prev.filter(member => member.user_details.username !== username));
    } catch (err) {
      console.error('Failed to remove member:', err);
      alert(`Failed to remove member: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingMembers(prev => ({ ...prev, [username]: false }));
    }
  };

  const filteredMembers = searchTerm 
    ? members.filter(member => 
        member.user_details.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (member.user_details.email && member.user_details.email.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    : members;

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Community Members</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Community Members</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold">Community Members</h1>
          <p className="text-gray-600 mt-1">
            Manage members of your community.
          </p>
        </div>

        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="max-w-md">
            <div className="relative">
              <input
                type="text"
                placeholder="Search members..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {filteredMembers.length === 0 ? (
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
            <h3 className="mt-2 text-lg font-medium text-gray-900">No members found</h3>
            <p className="mt-1 text-gray-500">
              {searchTerm ? 'No members match your search criteria.' : 'There are currently no members in this community.'}
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
                    Joined At
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredMembers.map((member) => (
                  <tr key={member.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full overflow-hidden bg-gray-100 mr-4">
                          {member.user_details.avatar ? (
                            <img 
                              src={member.user_details.avatar} 
                              alt={`${member.user_details.username}'s avatar`}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="h-full w-full flex items-center justify-center bg-indigo-100 text-indigo-500 font-bold text-lg">
                              {member.user_details.username.charAt(0).toUpperCase()}
                            </div>
                          )}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {member.user_details.username}
                          </div>
                          <div className="text-sm text-gray-500">
                            {member.user_details.email}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(member.joined_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        member.is_banned 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {member.is_banned ? 'Banned' : 'Active'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-3">
                        {!member.is_banned && (
                          <>
                            <button
                              onClick={() => handleBanUser(member.user_details.username)}
                              disabled={processingMembers[member.user_details.username]}
                              className={`ml-2 inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 ${processingMembers[member.user_details.username] ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                              {processingMembers[member.user_details.username] ? 'Banning...' : 'Ban'}
                            </button>
                            <button
                              onClick={() => handleRemoveMember(member.user_details.username)}
                              disabled={processingMembers[member.user_details.username]}
                              className="text-gray-600 hover:text-gray-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                            >
                              {processingMembers[member.user_details.username] ? 'Processing...' : 'Remove'}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Ban User Modal */}
      <BanUserModal
        isOpen={showBanModal}
        onClose={() => {
          setShowBanModal(false);
          setBanTargetUser(null);
        }}
        onConfirmBan={confirmBanUser}
        username={banTargetUser}
        isLoading={banLoading}
      />
    </>
  );
} 