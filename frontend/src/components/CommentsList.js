'use client';

import React, { useState, useEffect } from 'react';
import Comment from './Comment';
import CommentForm from './CommentForm';
import Spinner from './Spinner';

export default function CommentsList({ postId, postPath }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch comments when component mounts
  useEffect(() => {
    async function fetchComments() {
      try {
        setLoading(true);
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/comments/`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch comments');
        }
        
        const data = await response.json();
        setComments(data.results || data); // Handle both paginated and non-paginated responses
      } catch (err) {
        console.error('Error fetching comments:', err);
        setError('Failed to load comments. Please try again later.');
      } finally {
        setLoading(false);
      }
    }
    
    if (postId) {
      fetchComments();
    }
  }, [postId]);

  // Handle adding a new comment
  const handleCommentAdded = (newComment) => {
    setComments(prevComments => {
      // Add the new comment to the beginning of the array
      return [newComment, ...prevComments];
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        {error}
      </div>
    );
  }

  return (
    <div>
      <CommentForm 
        postId={postId} 
        parentId="" 
        postPath={`posts/${postId}`} 
        onCommentAdded={handleCommentAdded} 
      />
      
      <div className="mt-6">
        {comments.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            No comments yet. Be the first to comment!
          </div>
        ) : (
          <div className="space-y-4">
            {comments.map(comment => (
              <Comment 
                key={comment.id} 
                comment={comment} 
                postId={postId}
                postPath={`posts/${postId}`} 
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 