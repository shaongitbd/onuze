'use client';

import React, { useState } from 'react';
import { useAuth } from '../lib/auth';

export default function CommentForm({ postId, parentId, postPath, onCommentAdded }) {
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const { isAuthenticated, user } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!content.trim()) {
      setError('Comment cannot be empty');
      return;
    }
    
    if (!isAuthenticated) {
      setError('You must be logged in to comment');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        throw new Error('Authentication token not found');
      }
      
      // Create payload with required fields
      const payload = {
        content,
        post: postId,
        parent: parentId || "" // Always include parent, even if empty string
      };
      
      console.log('Submitting comment:', payload);
      console.log('API endpoint:', `${API_BASE_URL}/comments/`);
      
      const response = await fetch(`${API_BASE_URL}/comments/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `JWT ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.errors.detail ||'Failed to post comment');
      }
      
      const newComment = await response.json();
      
      // Reset form
      setContent('');
      
      // Notify parent component
      if (onCommentAdded) {
        onCommentAdded(newComment);
      }
    } catch (err) {
      console.error('Error posting comment:', err);
      setError(err.message || 'Failed to post comment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  if (!isAuthenticated) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg text-center">
        <p className="text-gray-600">You need to be logged in to comment.</p>
        <a href="/login" className="text-indigo-600 hover:text-indigo-800 font-medium mt-2 inline-block">
          Log in
        </a>
      </div>
    );
  }
  
  return (
    <form onSubmit={handleSubmit} className="mb-6">
      <div className="mb-4">
        <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
          Add a comment
        </label>
        <textarea
          id="comment"
          rows="4"
          className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-2"
          placeholder="What are your thoughts?"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          disabled={isSubmitting}
        ></textarea>
      </div>
      
      {error && (
        <div className="mb-4 text-red-600 text-sm">
          {error}
        </div>
      )}
      
      <button
        type="submit"
        disabled={isSubmitting || !content.trim()}
        className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
          isSubmitting || !content.trim() 
            ? 'bg-indigo-400 cursor-not-allowed' 
            : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
        }`}
      >
        {isSubmitting ? 'Posting...' : 'Post Comment'}
      </button>
    </form>
  );
} 