'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getPostByPath, updatePost } from '../../../../../../lib/api';
import { useAuth } from '../../../../../../lib/auth';
import Spinner from '../../../../../../components/Spinner';

export default function EditPostPage() {
  const params = useParams();
  const router = useRouter();
  const { communityName, postPath } = params;
  
  const [post, setPost] = useState(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isNsfw, setIsNsfw] = useState(false);
  const [isSpoiler, setIsSpoiler] = useState(false);
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  const { user, isAuthenticated, isLoading } = useAuth();

  // Fetch post data
  useEffect(() => {
    async function fetchPost() {
      try {
        setLoading(true);
        const postData = await getPostByPath(postPath);
        setPost(postData);
        
        // Check if user is authorized to edit this post
        if (!user || postData.user.id !== user.id) {
          router.push(`/c/${communityName}/post/${postPath}`);
          return;
        }
        
        // Set form data
        setTitle(postData.title || '');
        setContent(postData.content || '');
        setIsNsfw(postData.is_nsfw || false);
        setIsSpoiler(postData.is_spoiler || false);
      } catch (err) {
        console.error('Error fetching post:', err);
        setError('Post not found or you do not have access.');
      } finally {
        setLoading(false);
      }
    }

    if (postPath && user && !isLoading) {
      fetchPost();
    }
  }, [postPath, user, isLoading, router, communityName]);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    
    // Ensure we have a post ID
    if (!post || !post.path) {
      setError('Cannot update post: Post data is missing.');
      return;
    }
    
    setSubmitting(true);
    setError(null);
    
    try {
      const updatedPost = await updatePost(post.path, {
        title,
        content,
        is_nsfw: isNsfw,
        is_spoiler: isSpoiler
      });
      
      // Redirect back to the post
      router.push(`/c/${communityName}/post/${postPath}`);
    } catch (err) {
      console.error('Error updating post:', err);
      setError(err.message || 'Failed to update post. Please try again.');
      setSubmitting(false);
    }
  };

  if (loading || isLoading) {
    return (
      <div className="p-4 flex justify-center items-center min-h-[300px]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <div className="bg-white rounded-md shadow-sm p-6 mb-6">
        <h1 className="text-2xl font-bold mb-6">Edit Post</h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Title"
              maxLength={300}
              required
              disabled={submitting}
            />
            <p className="mt-1 text-xs text-gray-500 text-right">
              {title.length}/300
            </p>
          </div>
          
          <div className="mb-4">
            <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
              Content
            </label>
            <textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows="8"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Text"
              disabled={submitting}
            />
          </div>
          
          <div className="mb-4 flex items-center space-x-4">
            <div className="flex items-center">
              <input
                id="is_nsfw"
                type="checkbox"
                checked={isNsfw}
                onChange={(e) => setIsNsfw(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                disabled={submitting}
              />
              <label htmlFor="is_nsfw" className="ml-2 block text-sm text-gray-700">
                NSFW
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="is_spoiler"
                type="checkbox"
                checked={isSpoiler}
                onChange={(e) => setIsSpoiler(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                disabled={submitting}
              />
              <label htmlFor="is_spoiler" className="ml-2 block text-sm text-gray-700">
                Spoiler
              </label>
            </div>
          </div>
          
          <div className="flex justify-end space-x-3">
            <Link
              href={`/c/${communityName}/post/${postPath}`}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className={`px-4 py-2 text-white rounded-md ${
                submitting
                  ? 'bg-indigo-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
              }`}
            >
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 