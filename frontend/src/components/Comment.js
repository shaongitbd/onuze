'use client';

import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import CommentForm from './CommentForm';
import { useAuth } from '../lib/auth';

export default function Comment({ comment, postId, postPath }) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState(comment.replies || []);
  const { isAuthenticated } = useAuth();
  
  // Format the date in a user-friendly way
  const formatDate = (dateString) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'some time ago';
    }
  };
  
  const handleReplyAdded = (newReply) => {
    setReplies(prevReplies => [newReply, ...prevReplies]);
    setShowReplyForm(false);
    setShowReplies(true);
  };
  
  const handleVote = async (voteType) => {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/comments/${comment.id}/votes/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `JWT ${token}`
        },
        body: JSON.stringify({ vote_type: voteType })
      });

      if (response.ok) {
        // Handle successful vote
      } else {
        // Handle error
      }
    } catch (error) {
      console.error('Error voting:', error);
    }
  };
  
  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          {comment.user?.profile_image ? (
            <img 
              src={comment.user.profile_image} 
              alt={comment.user.username} 
              className="w-8 h-8 rounded-full"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-white">
              {comment.user?.username?.charAt(0).toUpperCase() || '?'}
            </div>
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center mb-1">
            <a href={`/user/${comment.user?.username || '[deleted]'}`} className="text-sm font-medium text-gray-900 hover:underline mr-2">
              {comment.user?.username || '[deleted]'}
            </a>
            <span className="text-xs text-gray-500">
              {formatDate(comment.created_at)}
            </span>
          </div>
          
          <div className="text-sm text-gray-800 whitespace-pre-wrap mb-2">
            {comment.content}
          </div>
          
          <div className="flex items-center text-xs space-x-4">
            {isAuthenticated && (
              <button 
                onClick={() => setShowReplyForm(!showReplyForm)} 
                className="text-gray-500 hover:text-indigo-600"
              >
                Reply
              </button>
            )}
            
            {replies.length > 0 && (
              <button 
                onClick={() => setShowReplies(!showReplies)} 
                className="text-gray-500 hover:text-indigo-600 flex items-center"
              >
                <span>{showReplies ? 'Hide' : 'Show'} {replies.length} {replies.length === 1 ? 'reply' : 'replies'}</span>
              </button>
            )}
          </div>
          
          {showReplyForm && (
            <div className="mt-3 ml-8">
              <CommentForm 
                postId={postId}
                parentId={comment.id}
                postPath={`posts/${postId}`}
                onCommentAdded={handleReplyAdded} 
              />
            </div>
          )}
          
          {showReplies && replies.length > 0 && (
            <div className="mt-3 ml-8 space-y-3">
              {replies.map(reply => (
                <Comment 
                  key={reply.id} 
                  comment={reply} 
                  postId={postId}
                  postPath={postPath} 
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 