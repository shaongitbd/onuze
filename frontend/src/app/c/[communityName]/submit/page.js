'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '../../../../lib/auth';
import Link from 'next/link';
import Spinner from '../../../../components/Spinner';

export default function SubmitPost() {
  const { communityName } = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  // Form state
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [url, setUrl] = useState('');
  const [postType, setPostType] = useState('text'); // 'text' or 'link'
  
  // Fetch community data to verify it exists and user has permission
  useEffect(() => {
    async function fetchCommunityData() {
      try {
        setLoading(true);
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
        
        // Fetch community data
        const response = await fetch(`${API_BASE_URL}/communities/${communityName}/`);
        
        if (!response.ok) {
          throw new Error('Community not found');
        }
        
        const communityData = await response.json();
        setCommunity(communityData);
      } catch (err) {
        console.error('Failed to fetch community data:', err);
        setError('Failed to load community data. Please try again later.');
      } finally {
        setLoading(false);
      }
    }
    
    if (communityName) {
      fetchCommunityData();
    }
  }, [communityName]);
  
  // Redirect if not logged in
  useEffect(() => {
    if (!isAuthenticated && !loading) {
      router.push('/login?next=' + encodeURIComponent(`/c/${communityName}/submit`));
    }
  }, [isAuthenticated, loading, router, communityName]);
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    
    if (postType === 'text' && !content.trim()) {
      setError('Content is required for text posts');
      return;
    }
    
    if (postType === 'link' && !url.trim()) {
      setError('URL is required for link posts');
      return;
    }
    
    setSubmitting(true);
    setError(null);
    
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('Authentication token not found');
      }
      
      const postData = {
        title,
        ...(postType === 'text' ? { content } : { url })
      };
      
      const response = await fetch(`${API_BASE_URL}/communities/${communityName}/posts/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `JWT ${token}`
        },
        body: JSON.stringify(postData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create post');
      }
      
      const newPost = await response.json();
      
      // Redirect to the new post
      router.push(`/c/${communityName}/post/${newPost.id}`);
    } catch (err) {
      console.error('Error creating post:', err);
      setError(err.message || 'Failed to create post. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="large" />
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">You need to be logged in to create a post.</span>
        </div>
      </div>
    );
  }
  
  if (error && !community) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-4">
        <Link href={`/c/${communityName}`} className="text-indigo-600 hover:text-indigo-800">
          &larr; Back to c/{communityName}
        </Link>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-6">Create a post in c/{communityName}</h1>
        
        <div className="mb-6">
          <div className="flex border-b border-gray-200">
            <button
              type="button"
              onClick={() => setPostType('text')}
              className={`py-2 px-4 text-sm font-medium ${
                postType === 'text'
                  ? 'border-b-2 border-indigo-600 text-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Text Post
            </button>
            <button
              type="button"
              onClick={() => setPostType('link')}
              className={`py-2 px-4 text-sm font-medium ${
                postType === 'link'
                  ? 'border-b-2 border-indigo-600 text-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Link Post
            </button>
          </div>
        </div>
        
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div className="mb-4">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Title
            </label>
            <input
              type="text"
              id="title"
              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={submitting}
              required
            />
          </div>
          
          {postType === 'text' ? (
            <div className="mb-4">
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
                Content
              </label>
              <textarea
                id="content"
                rows="8"
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
                placeholder="Text (optional)"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                disabled={submitting}
              ></textarea>
            </div>
          ) : (
            <div className="mb-4">
              <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                URL
              </label>
              <input
                type="url"
                id="url"
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={submitting}
                required
              />
            </div>
          )}
          
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                submitting
                  ? 'bg-indigo-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
              }`}
            >
              {submitting ? (
                <>
                  <Spinner size="small" className="mr-2" />
                  Posting...
                </>
              ) : (
                'Post'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 