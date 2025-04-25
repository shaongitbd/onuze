'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getUserProfile, getUserComments, getPostByPath } from '../../../lib/api';
import { useAuth } from '../../../lib/auth';
import Spinner from '../../../components/Spinner';
import { formatDistanceToNow } from 'date-fns';
import InfinitePosts from '../../../components/InfinitePosts';
import InfiniteUserComments from '../../../components/InfiniteUserComments';

// Basic component to display a user comment preview
const UserCommentPreview = ({ comment }) => {
  // State to hold fetched post details
  const [postDetails, setPostDetails] = useState({ 
    title: comment.post_title || null, // Start with comment data if available
    communityPath: comment.community_path || null 
  });
  const [loadingPost, setLoadingPost] = useState(!comment.post_title || !comment.community_path); // Only load if needed
  const [fetchError, setFetchError] = useState(false);

  const initialPostPath = comment.post_path || '';

  useEffect(() => {
    // Only fetch if we don't have the details and have a path
    if ((!postDetails.title || !postDetails.communityPath) && initialPostPath) {
      setLoadingPost(true);
      setFetchError(false);
      getPostByPath(initialPostPath)
        .then(data => {
          setPostDetails({ 
            title: data?.title || '[post unavailable]', 
            communityPath: data?.community?.path || 'unknown' 
          });
        })
        .catch(err => {
          console.error(`Error fetching post details for path ${initialPostPath}:`, err);
          setPostDetails({ title: '[post unavailable]', communityPath: 'unknown' });
          setFetchError(true);
        })
        .finally(() => {
          setLoadingPost(false);
        });
    } else if (!initialPostPath) {
        // Handle case where comment has no post_path
        setPostDetails({ title: '[post unavailable]', communityPath: 'unknown' });
        setLoadingPost(false);
    }
  }, [initialPostPath, postDetails.title, postDetails.communityPath]); // Re-run if path changes

  // Use state variables for rendering
  const displayCommunityPath = postDetails.communityPath || 'unknown';
  const displayPostTitle = postDetails.title || '[post unavailable]';
  const postUrl = initialPostPath ? `/c/${displayCommunityPath}/post/${initialPostPath}` : '#';

  return (
    <div className="border-b border-gray-100 pb-3 mb-3">
      <div className="text-xs text-gray-500 mb-1">
        <span>Commented on </span>
        {loadingPost ? (
          <span className="italic text-gray-400">Loading post title...</span>
        ) : (
          <Link href={postUrl} className="hover:underline font-medium text-gray-700">
            {displayPostTitle} 
          </Link>
        )}
        <span> in </span>
        {loadingPost ? (
            <span className="italic text-gray-400">c/...</span>
        ) : (
            <Link href={`/c/${displayCommunityPath}`} className="hover:underline font-medium text-gray-700">
                c/{displayCommunityPath}
            </Link>
        )}
        <span className="mx-1">•</span>
        <span>{formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}</span>
      </div>
      <div className="text-sm text-gray-800 whitespace-pre-wrap pl-2 border-l-2 border-gray-200">
        {comment.content}
      </div>
      <div className="text-xs text-gray-500 mt-1 pl-2">
         {comment.score} points
      </div>
    </div>
  );
};

export default function UserProfilePage() {
  const params = useParams();
  const { username } = params;
  
  const [profile, setProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('posts');
  
  // State for post filtering
  const [postSortOption, setPostSortOption] = useState('new');
  const [postTimeFilter, setPostTimeFilter] = useState('all');
  const [showPostTimeFilter, setShowPostTimeFilter] = useState(false);
  
  // State for comment filtering
  const [commentSortOption, setCommentSortOption] = useState('new');
  const [commentTimeFilter, setCommentTimeFilter] = useState('all');
  const [showCommentTimeFilter, setShowCommentTimeFilter] = useState(false);

  // Fetch Profile
  useEffect(() => {
    async function fetchProfile() {
      if (!username) return;
      try {
        setLoadingProfile(true);
        const profileData = await getUserProfile(username);
        setProfile(profileData);
        setError('');
      } catch (err) {
        console.error('Error fetching user profile:', err);
        setError('User profile not found or an error occurred.');
        setProfile(null);
      } finally {
        setLoadingProfile(false);
      }
    }
      fetchProfile();
  }, [username]);

  if (loadingProfile) {
    return (
      <div className="p-4 flex justify-center items-center min-h-[300px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-4 max-w-3xl mx-auto">
        <div className="bg-red-50 p-4 rounded-md text-red-700">
          {error || 'User not found.'}
        </div>
        <div className="mt-4">
          <Link href="/" className="text-indigo-600 hover:underline">
            Back to home
          </Link>
        </div>
      </div>
    );
  }

  const TabButton = ({ tabName, label }) => (
    <button
      type="button"
      onClick={() => setActiveTab(tabName)}
      className={`py-2 px-4 font-medium border-b-2 transition-colors duration-150 
        ${
          activeTab === tabName
            ? 'border-red-500 text-red-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        }`}
    >
      {label}
    </button>
  );

  // Handlers for POST filter changes
  const handlePostSortChange = (event) => {
    const newSort = event.target.value;
    setPostSortOption(newSort);
    // Show time filter only for top/controversial
    const showTime = newSort === 'top' || newSort === 'controversial';
    setShowPostTimeFilter(showTime);
    // Reset time filter if it's no longer shown
    if (!showTime) {
      setPostTimeFilter('all');
    }
  };

  const handlePostTimeFilterChange = (event) => {
    setPostTimeFilter(event.target.value);
  };

  // Handlers for COMMENT filter changes
  const handleCommentSortChange = (event) => {
    const newSort = event.target.value;
    setCommentSortOption(newSort);
    const showTime = newSort === 'top' || newSort === 'controversial';
    setShowCommentTimeFilter(showTime);
    if (!showTime) {
      setCommentTimeFilter('all');
    }
  };

  const handleCommentTimeFilterChange = (event) => {
    setCommentTimeFilter(event.target.value);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Profile Header Card - Redesigned */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6 border border-gray-200">
        <div className="p-6">
          <div className="flex items-center space-x-4 mb-4">
            {/* Avatar */}
            <div className="flex-shrink-0">
              <img src={profile.avatar} alt="User Avatar" className="w-16 h-16 rounded-full border-2 border-gray-200" />
          </div>
            
            {/* Username and Join Date */}
            <div className="flex-grow">
              <h1 className="text-xl font-bold text-gray-800">{profile.username}</h1>
              <p className="text-sm text-gray-500">
                Joined {new Date(profile.date_joined).toLocaleDateString()}
            </p>
          </div>
            
            {/* Edit Button */} 
            {user && user.username === profile.username && (
              <div className="flex-shrink-0">
                <Link 
                  href="/settings" 
                  className="px-3 py-1.5 bg-gray-100 rounded-md text-gray-700 hover:bg-gray-200 text-xs font-medium"
                >
                  Edit Profile
                </Link>
        </div>
            )}
          </div>
          
          {/* Bio */} 
          {profile.bio && (
            <p className="text-gray-700 text-sm mb-4">{profile.bio}</p>
          )}
          
          {/* Stats Section */}
          <div className="flex space-x-6 text-sm border-t border-gray-100 pt-3">
            <div>
              <span className="font-semibold text-red-600">{profile.karma || 0}</span>
              <span className="ml-1 text-gray-500">Karma</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">{profile.post_count || 0}</span>
              <span className="ml-1 text-gray-500">Posts</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Tabs Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <div className="flex space-x-4">
          <TabButton tabName="posts" label="Posts" />
          <TabButton tabName="comments" label="Comments" />
        </div>
      </div>
        
      {/* Tab Content Area */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 min-h-[200px]">
        {activeTab === 'posts' && (
          <div> 
            <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold">Posts</h2>
              {/* Post Filter Controls */}
              <div className="flex items-center space-x-2">
                <select 
                  value={postSortOption}
                  onChange={handlePostSortChange}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500"
                >
                  <option value="new">New</option>
                  <option value="hot">Hot</option>
                  <option value="top">Top</option>
                </select>
                {showPostTimeFilter && (
                  <select 
                    value={postTimeFilter}
                    onChange={handlePostTimeFilterChange}
                    className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500"
                  >
                    <option value="hour">Past Hour</option>
                    <option value="day">Past 24 Hours</option>
                    <option value="week">Past Week</option>
                    <option value="month">Past Month</option>
                    <option value="year">Past Year</option>
                    <option value="all">All Time</option>
                  </select>
                )}
              </div>
                  </div>
                  
            {/* Post List Area - Use InfinitePosts instead of static list */}
            <InfinitePosts 
              initialParams={{
                username,
                sort: postSortOption,
                ...(showPostTimeFilter ? { t: postTimeFilter } : {})
              }} 
              emptyMessage={`u/${profile?.username || 'User'} hasn't posted anything yet${postSortOption !== 'new' || postTimeFilter !== 'all' ? ' matching these filters' : ''}.`}
            />
          </div>
                  )}
                  
        {activeTab === 'comments' && (
          <div>
            {/* Comment Filters */}
            <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold">Comments</h2>
              <div className="flex items-center space-x-2">
                <select 
                  value={commentSortOption}
                  onChange={handleCommentSortChange}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500"
                >
                  <option value="new">New</option>
                  <option value="top">Top</option>
                  <option value="hot">Hot</option>
                </select>
                {showCommentTimeFilter && (
                  <select 
                    value={commentTimeFilter}
                    onChange={handleCommentTimeFilterChange}
                    className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500"
                  >
                    <option value="hour">Past Hour</option>
                    <option value="day">Past 24 Hours</option>
                    <option value="week">Past Week</option>
                    <option value="month">Past Month</option>
                    <option value="year">Past Year</option>
                    <option value="all">All Time</option>
                  </select>
                )}
                    </div>
                  </div>
            
            {/* Comment List Area */}
            <InfiniteUserComments 
              username={username}
              initialParams={{
                sort: commentSortOption,
                ...(showCommentTimeFilter ? { t: commentTimeFilter } : {})
              }}
              commentComponent={UserCommentPreview}
              emptyMessage={`u/${profile?.username || 'User'} hasn't commented anything yet${commentSortOption !== 'new' || commentTimeFilter !== 'all' ? ' matching these filters' : ''}.`}
            />
          </div>
        )}
      </div>
    </div>
  );
} 