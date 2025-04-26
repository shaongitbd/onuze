'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getSubredditDetail, joinCommunity, leaveCommunity } from '../../../lib/api';
import Link from 'next/link';
import Spinner from '../../../components/Spinner';
import { useAuth } from '../../../lib/auth';
import SortTimeControls from '../../../components/SortTimeControls';
import InfinitePosts from '../../../components/InfinitePosts';

export default function CommunityPage() {
  const { communityName } = useParams();
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();
  const [sort, setSort] = useState('hot');
  const [time, setTime] = useState('all');
  const [isProcessingJoin, setIsProcessingJoin] = useState(false);
  const [joinError, setJoinError] = useState(null);

  useEffect(() => {
    async function fetchCommunityData() {
      try {
        setLoading(true);
        setError(null);
        const communityData = await getSubredditDetail(communityName);
        setCommunity(communityData);
      } catch (err) {
        console.error('Failed to fetch community data:', err);
        if (err.response && err.response.status === 404) {
            setError('Community not found.');
            setCommunity(null);
        } else {
        setError('Failed to load community data. Please try again later.');
        }
      } finally {
        setLoading(false);
      }
    }

    if (communityName) {
      fetchCommunityData();
    }
  }, [communityName]);

  const showTimeFilter = sort === 'top' || sort === 'controversial';

  useEffect(() => {
    if (!showTimeFilter && time !== 'all') {
      setTime('all');
    }
  }, [sort, showTimeFilter, time]);

  const handleJoin = async () => {
    if (!community || isProcessingJoin) return;
    setIsProcessingJoin(true);
    setJoinError(null);
    try {
      await joinCommunity(community.id);
      setCommunity(prev => ({
        ...prev,
        is_member: true,
        member_count: (prev.member_count || 0) + 1
      }));
    } catch (err) {
      console.error("Failed to join community:", err);
      const message = err.response?.data?.detail || 'Failed to join community. Please try again.';
      setJoinError(message);
    } finally {
      setIsProcessingJoin(false);
    }
  };

  const handleLeave = async () => {
    if (!community || isProcessingJoin) return;
    setIsProcessingJoin(true);
    setJoinError(null);
    try {
      await leaveCommunity(community.id);
      setCommunity(prev => ({
        ...prev,
        is_member: false,
        member_count: Math.max(0, (prev.member_count || 1) - 1)
      }));
    } catch (err) {
      console.error("Failed to leave community:", err);
      const message = err.response?.data?.detail || 'Failed to leave community. Please try again.';
      setJoinError(message);
    } finally {
      setIsProcessingJoin(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative my-4" role="alert">
        <span className="block sm:inline">{error}</span>
      </div>
    );
  }

  if (!community) {
    return (
      <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative my-4" role="alert">
        <span className="block sm:inline">Community not found.</span>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 min-h-screen">
      {/* Hero Banner with Community Image */}
      <div className="h-48 bg-gradient-to-r from-red-700 via-red-600 to-red-500 relative overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-30"></div>
        {community.banner_image ? (
          <div className="absolute inset-0 bg-cover bg-center mix-blend-overlay" style={{ backgroundImage: `url(${community.banner_image})` }}></div>
        ) : (
        <div className="absolute inset-0 bg-[url('https://picsum.photos/1920/300')] bg-cover bg-center mix-blend-overlay"></div>
        )}
        <div className="container mx-auto px-4 h-full flex items-end">
          <div className="flex items-center mb-6 z-10">
            <div className="w-20 h-20 rounded-full bg-white border-4 border-white shadow-md mr-4 flex-shrink-0 overflow-hidden">
              {community.icon_image ? (
                <img src={community.icon_image} alt={`${community.name} icon`} className="w-full h-full object-cover" />
              ) : (
              <div className="w-full h-full bg-red-500 flex items-center justify-center text-white text-2xl font-bold">
                {community.name ? community.name.charAt(0).toUpperCase() : 'C'}
              </div>
              )}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white drop-shadow-md flex items-center">
                c/{community.name}
                {community.verified && (
                  <svg className="w-5 h-5 ml-2 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
              </h1>
              <p className="text-gray-200 text-sm drop-shadow-md">
                Community since {community.createdAt ? new Date(community.createdAt).toLocaleDateString('en-US', {year: 'numeric', month: 'short', day: 'numeric'}) : 'recently'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Community Action Bar */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-20 shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            <div className="flex space-x-6">
              <button className="text-gray-500 hover:text-red-600 flex items-center h-full border-b-2 border-transparent hover:border-red-600 px-2 transition-all">
                <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                </svg>
                Overview
              </button>
              <button className="text-gray-500 hover:text-red-600 flex items-center h-full border-b-2 border-transparent hover:border-red-600 px-2 transition-all">
                <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
                About
              </button>
            </div>
            {user && (
              <Link 
                href={`/submit`}
                className="bg-red-600 hover:bg-red-700 text-white font-medium py-1.5 px-4 rounded-full text-sm shadow-sm transition-all duration-200 flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create Post
              </Link>
            )}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Main Content */}
          <div className="lg:w-8/12">
            {/* Sort Controls */}
            <div className="bg-white rounded-lg shadow-sm mb-4 p-3">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 4a1 1 0 00-2 0v7.268a2 2 0 000 3.464V16a1 1 0 102 0v-1.268a2 2 0 000-3.464V4zM11 4a1 1 0 10-2 0v1.268a2 2 0 000 3.464V16a1 1 0 102 0V8.732a2 2 0 000-3.464V4zM16 3a1 1 0 011 1v7.268a2 2 0 010 3.464V16a1 1 0 11-2 0v-1.268a2 2 0 010-3.464V4a1 1 0 011-1z" />
                </svg>
                <div className="flex-1">
                  <SortTimeControls 
                    sort={sort} 
                    setSort={setSort} 
                    time={time} 
                    setTime={setTime} 
                  />
                </div>
              </div>
            </div>

            {/* Posts - Replaced with InfinitePosts */}
            <InfinitePosts
              key={`${communityName}-${sort}-${showTimeFilter ? time : 'all'}`}
              initialParams={{
                communityPath: communityName,
                sort: sort,
                ...(showTimeFilter ? { t: time } : {})
              }}
              emptyMessage={`Looks like there are no posts in c/${community?.name || communityName} yet${sort !== 'hot' || (showTimeFilter && time !== 'all') ? ' matching these filters' : ''}.`}
            />
          </div>

          {/* Sidebar */}
          <div className="lg:w-4/12">
            {/* About Community */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden mb-4 sticky top-16">
              <div className="px-6 py-4 bg-red-600 text-white">
                <h3 className="text-lg font-bold flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  About Community
                </h3>
              </div>
              <div className="p-6">
                <p className="text-gray-700 mb-6">{community.description || 'No description available for this community.'}</p>
                
                <div className="flex items-center justify-around mb-6 pb-6 border-b border-gray-200">
                  <div className="text-center px-2">
                    <span className="block text-2xl font-bold text-red-600">{community.member_count || 0}</span>
                    <span className="text-sm text-gray-500">Members</span>
                  </div>
                  <div className="text-center px-2">
                    <span className="block text-2xl font-bold text-gray-700">
                      {community.created_at ? Math.floor((new Date() - new Date(community.created_at)) / (1000 * 60 * 60 * 24)) : 0}
                    </span>
                    <span className="text-sm text-gray-500">Days Old</span>
                  </div>
                </div>
                
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-500 uppercase mb-3">Community Rules</h4>
                  <ul className="space-y-3 text-sm">
                    <li className="flex items-start">
                      <span className="bg-red-100 text-red-600 font-bold rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">1</span>
                      <span>Be respectful to others</span>
                    </li>
                    <li className="flex items-start">
                      <span className="bg-red-100 text-red-600 font-bold rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">2</span>
                      <span>No spamming or self-promotion</span>
                    </li>
                    <li className="flex items-start">
                      <span className="bg-red-100 text-red-600 font-bold rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">3</span>
                      <span>Posts must be relevant to the community</span>
                    </li>
                  </ul>
                </div>
                
                {/* --- Join/Leave Button --- */}
                {user && community && (
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    {isProcessingJoin ? (
                      <button 
                        disabled
                        className="block w-full py-2 bg-gray-300 text-gray-500 font-medium rounded text-center cursor-not-allowed"
                      >
                        Processing...
                      </button>
                    ) : community.is_member ? (
                      <button 
                        onClick={handleLeave}
                        className="block w-full py-2 bg-red-100 text-red-700 border border-red-200 font-medium rounded text-center hover:bg-red-200 hover:border-red-300 transition-colors duration-200"
                      >
                        Leave Community
                      </button>
                    ) : (
                      <button 
                        onClick={handleJoin}
                        className="block w-full py-2 bg-red-600 text-white font-medium rounded text-center hover:bg-red-700 transition-colors duration-200"
                      >
                        Join Community
                      </button>
                    )}
                  </div>
                )}
                {/* Display Join/Leave Errors */} 
                {joinError && (
                  <div className="mt-2 text-xs text-red-600 text-center">
                    {joinError}
                  </div>
                )}
                {/* -------------------------- */}
                
                {user && (
                  <Link 
                    href={`/submit`}
                    className="block w-full py-2 bg-red-600 text-white font-medium rounded text-center hover:bg-red-700 transition-colors duration-200"
                  >
                    Create Post
                  </Link>
                )}
              </div>
              <div className="px-6 py-3 bg-gray-50 text-xs text-gray-500">
                Created {community.createdAt ? new Date(community.createdAt).toLocaleDateString('en-US', {year: 'numeric', month: 'long', day: 'numeric'}) : 'recently'}
              </div>
            </div>
            
            {/* Community Tags */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-4">
              <h3 className="text-md font-bold text-gray-700 mb-3">Popular Tags</h3>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs">#trending</span>
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">#popular</span>
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">#new</span>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">#featured</span>
                <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs">#discussion</span>
              </div>
            </div>
            
            {/* Footer */}
            <div className="text-xs text-gray-500 mb-6">
              <ul className="flex flex-wrap gap-x-2 gap-y-1">
                <li><a href="#" className="hover:underline hover:text-red-600">Help</a> •</li>
                <li><a href="#" className="hover:underline hover:text-red-600">About</a> •</li>
                <li><a href="#" className="hover:underline hover:text-red-600">Terms</a> •</li>
                <li><a href="#" className="hover:underline hover:text-red-600">Privacy</a></li>
              </ul>
              <p className="mt-2">© 2023 RedditClone, Inc. All rights reserved.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 