'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getUserProfile, getUserPosts } from '../../../lib/api';
import { useAuth } from '../../../lib/auth';
import Spinner from '../../../components/Spinner';
import { formatDistanceToNow } from 'date-fns';

export default function UserProfilePage() {
  const params = useParams();
  const { username } = params;
  
  const [profile, setProfile] = React.useState(null);
  const [posts, setPosts] = React.useState([]);
  const [loadingProfile, setLoadingProfile] = React.useState(true);
  const [loadingPosts, setLoadingPosts] = React.useState(true);
  const [error, setError] = React.useState('');
  const { user } = useAuth();

  React.useEffect(() => {
    async function fetchProfile() {
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

    if (username) {
      fetchProfile();
    }
  }, [username]);

  React.useEffect(() => {
    async function fetchPosts() {
      if (!profile || !profile.id) return;
      
      try {
        setLoadingPosts(true);
        const postsData = await getUserPosts(profile.id);
        if (postsData && postsData.results) {
          setPosts(postsData.results);
        } else {
          setPosts([]);
        }
      } catch (err) {
        console.error('Error fetching user posts:', err);
      } finally {
        setLoadingPosts(false);
      }
    }
    
    fetchPosts();
  }, [profile]);

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

  return (
    <div className="p-4 max-w-3xl mx-auto">
      {/* User Profile Card */}
      <div className="bg-white rounded-md shadow-sm p-6 mb-6">
        <div className="flex items-center mb-4">
          <div className="h-16 w-16 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-xl font-bold">
            {profile.username.charAt(0).toUpperCase()}
          </div>
          <div className="ml-4">
            <h1 className="text-2xl font-bold">u/{profile.username}</h1>
            <p className="text-gray-500">
              Member since {new Date(profile.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        
        {profile.bio && (
          <div className="mb-4 p-4 bg-gray-50 rounded-md">
            <h3 className="font-semibold mb-2">About</h3>
            <p className="text-gray-700">{profile.bio}</p>
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex space-x-4">
            <div className="text-center">
              <div className="font-semibold text-lg">{posts.length}</div>
              <div className="text-gray-500 text-sm">Posts</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-lg">{profile.karma || 0}</div>
              <div className="text-gray-500 text-sm">Karma</div>
            </div>
          </div>
          
          {user && user.username === profile.username && (
            <Link 
              href="/settings" 
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
            >
              Edit Profile
            </Link>
          )}
        </div>
      </div>
      
      {/* User Posts */}
      <div className="bg-white rounded-md shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">
          Posts by u/{profile.username}
        </h2>
        
        {loadingPosts ? (
          <div className="flex justify-center py-8">
             <Spinner />
          </div>
        ) : posts.length === 0 ? (
          <p className="text-gray-500">This user hasn't posted anything yet.</p>
        ) : (
          <ul className="space-y-4">
            {posts.map(post => (
              <li key={post.id} className="border-b border-gray-100 pb-4 last:border-0 last:pb-0">
                <Link 
                  href={`/r/${post.community.name}/post/${post.id}`}
                  className="block hover:bg-gray-50 p-2 -mx-2 rounded-md transition"
                >
                  <div className="flex items-center mb-2">
                    <Link href={`/r/${post.community.name}`} className="font-medium text-indigo-600 hover:underline">
                      r/{post.community.name}
                    </Link>
                    <span className="mx-2 text-gray-400">•</span>
                    <span className="text-sm text-gray-500">
                      {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  
                  <h3 className="text-lg font-medium">{post.title}</h3>
                  
                  {post.content && (
                    <p className="text-gray-600 mt-1 line-clamp-2">{post.content}</p>
                  )}
                  
                  <div className="flex items-center mt-2 text-sm text-gray-500">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 11l5-5m0 0l5 5m-5-5v12"></path>
                      </svg>
                      {post.score} votes
                    </div>
                    <span className="mx-2">•</span>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                      </svg>
                      {post.comment_count || 0} comments
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
} 