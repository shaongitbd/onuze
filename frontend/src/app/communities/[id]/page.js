'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getSubredditDetail, getPosts, joinCommunity, leaveCommunity } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import Spinner from '@/components/Spinner';
import PostCard from '@/components/PostCard';

export default function CommunityDetailPage({ params }) {
  const { id } = params;
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  
  const [community, setCommunity] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [joining, setJoining] = useState(false);
  const [isMember, setIsMember] = useState(false);

  useEffect(() => {
    const fetchCommunity = async () => {
      setLoading(true);
      try {
        const communityData = await getSubredditDetail(id);
        setCommunity(communityData);
        
        // Check if user is a member using the field provided by the API
        if (isAuthenticated && communityData) {
          setIsMember(!!communityData.is_member); // Use is_member field from API
        }
        
        // Fetch community posts
        const postsData = await getPosts({ community_id: id });
        if (postsData && postsData.results) {
          setPosts(postsData.results);
        }
      } catch (err) {
        console.error('Error fetching community details:', err);
        setError(err.message || 'Failed to load community details');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchCommunity();
    }
  }, [id, isAuthenticated, user]);

  const handleJoinLeave = async () => {
    if (!isAuthenticated) {
      router.push(`/login?redirect=/communities/${id}`);
      return;
    }
    
    setJoining(true);
    try {
      if (isMember) {
        await leaveCommunity(id);
        setIsMember(false);
      } else {
        await joinCommunity(id);
        setIsMember(true);
      }
    } catch (err) {
      console.error(`Error ${isMember ? 'leaving' : 'joining'} community:`, err);
      alert(`Failed to ${isMember ? 'leave' : 'join'} community. ${err.message}`);
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );
  }

  if (error || !community) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-red-500 text-lg mb-4">
          {error || 'Community not found'}
        </p>
        <Link href="/communities" className="text-indigo-600 hover:text-indigo-800">
          Back to Communities
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Banner and community info */}
      <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
        {community.banner_image && (
          <div className="h-40 bg-cover bg-center w-full" 
               style={{ backgroundImage: `url(${community.banner_image})` }} />
        )}
        
        <div className="p-6">
          <div className="flex items-center">
            {community.icon_image ? (
              <img 
                src={community.icon_image} 
                alt={community.name}
                className="w-16 h-16 rounded-full mr-4 border-4 border-white shadow-sm"
              />
            ) : (
              <div className="w-16 h-16 rounded-full mr-4 bg-indigo-100 flex items-center justify-center">
                <span className="text-2xl font-bold text-indigo-800">
                  {community.name.charAt(0).toUpperCase()}
                </span>
              </div>
            )}
            
            <div>
              <div className="flex items-center flex-wrap">
                <h1 className="text-2xl font-bold mr-2">c/{community.name}</h1>
                {community.is_private && (
                  <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800 mr-2">
                    Private
                  </span>
                )}
                {community.is_nsfw && (
                  <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                    NSFW
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {community.member_count} {community.member_count === 1 ? 'member' : 'members'} 
                • Created {new Date(community.created_at).toLocaleDateString()}
              </p>
            </div>
            
            <div className="ml-auto">
              <button
                onClick={handleJoinLeave}
                disabled={joining}
                className={`px-4 py-2 rounded-full font-medium text-sm ${
                  isMember 
                    ? 'bg-gray-200 hover:bg-gray-300 text-gray-800' 
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }`}
              >
                {joining ? <Spinner /> : isMember ? 'Joined' : 'Join'}
              </button>
            </div>
          </div>
          
          {community.description && (
            <p className="mt-4 text-gray-700">
              {community.description}
            </p>
          )}
          
          {community.sidebar_content && (
            <div className="mt-4 p-4 bg-gray-50 rounded-md text-sm">
              <h3 className="font-medium mb-2">About Community</h3>
              <div className="text-gray-700">{community.sidebar_content}</div>
            </div>
          )}
        </div>
      </div>
      
      {/* Posts and actions */}
      <div className="flex flex-col md:flex-row gap-6">
        <div className="md:w-3/4">
          <div className="mb-4 flex justify-between items-center">
            <h2 className="text-xl font-semibold">Posts</h2>
            <Link 
              href={`/submit?community_id=${id}`}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Create Post
            </Link>
          </div>
          
          {posts.length > 0 ? (
            <div className="space-y-4">
              {posts.map(post => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg p-6 text-center">
              <p className="text-gray-500 mb-4">No posts yet.</p>
              <Link 
                href={`/submit?community_id=${id}`}
                className="text-indigo-600 hover:text-indigo-800"
              >
                Create the first post
              </Link>
            </div>
          )}
        </div>
        
        <div className="md:w-1/4">
          {/* Community rules, if available */}
          {community.rules && community.rules.length > 0 && (
            <div className="bg-white shadow rounded-lg p-4 mb-4">
              <h3 className="font-medium mb-2 text-sm uppercase tracking-wider">Community Rules</h3>
              <ol className="list-decimal list-inside text-sm space-y-2">
                {community.rules.map((rule, index) => (
                  <li key={rule.id || index}>
                    <span className="font-medium">{rule.title}</span>
                    {rule.description && (
                      <p className="text-gray-500 text-xs ml-5 mt-1">{rule.description}</p>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          )}
          
          {/* Moderators list, if available */}
          {community.moderators && community.moderators.length > 0 && (
            <div className="bg-white shadow rounded-lg p-4">
              <h3 className="font-medium mb-2 text-sm uppercase tracking-wider">Moderators</h3>
              <ul className="text-sm space-y-1">
                {community.moderators.map((mod, index) => (
                  <li key={mod.id || index}>
                    <Link href={`/user/${mod.user.username}`} className="text-indigo-600 hover:underline">
                      u/{mod.user.username}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 