'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../lib/auth';
import { upvotePost, downvotePost } from '../lib/api';
import { formatDistanceToNow } from 'date-fns';

// PostCard component for displaying post summaries on community and home pages
export default function PostCard({ post }) {
    const { isAuthenticated, user } = useAuth();
    const [currentPost, setCurrentPost] = useState(post); // Local state for optimistic updates
    
    // Get the community path from the post data
    const communityPath = currentPost.community?.path || currentPost.community?.name || 'unknown';

    const handleVote = async (voteDirection) => {
        if (!isAuthenticated || !currentPost) {
            // Optionally redirect to login or show message
            return;
        }

        const action = voteDirection === 'UP' ? upvotePost : downvotePost;
        
        try {
            // Store previous state for potential revert
            const previousPost = currentPost;

            // Optimistic UI update
            setCurrentPost(prevPost => {
                if (!prevPost) return null;
                const voteValue = voteDirection === 'UP' ? 1 : -1;
                const currentVote = prevPost.user_vote;
                let scoreChange = 0;

                if (voteValue === 1) { // Upvoting
                    scoreChange = currentVote === 'upvote' ? -1 : (currentVote === 'downvote' ? 2 : 1);
                } else { // Downvoting (-1)
                    scoreChange = currentVote === 'downvote' ? 1 : (currentVote === 'upvote' ? -2 : -1);
                }

                return {
                    ...prevPost,
                    score: (prevPost.score ?? 0) + scoreChange,
                    user_vote: voteValue === 1 ? (currentVote === 'upvote' ? null : 'upvote') : (currentVote === 'downvote' ? null : 'downvote')
                };
            });

            // Call the API
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_BASE_URL}/posts/${currentPost.id}/votes/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `JWT ${token}`
                },
                body: JSON.stringify({ vote_type: voteDirection === 'UP' ? 'upvote' : 'downvote' })
            });

            if (response.ok) {
                // Optional: Refetch post data after successful vote for consistency
                // const updatedPostData = await getPostById(currentPost.id); // Requires importing getPostById
                // setCurrentPost(updatedPostData);
            } else {
                console.error('Error voting on post:', response.statusText);
            }

        } catch (err) {
            console.error(`Error ${voteDirection === 'UP' ? 'upvoting' : 'downvoting'} post:`, err);
            // Revert optimistic update on error
            setCurrentPost(previousPost);
            // Optionally show error message to user
        }
    };

    if (!currentPost) return null;

    return (
        <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200 hover:border-red-200 transition-colors">
            <div className="flex">
                {/* Left sidebar for votes */}
                <div className="bg-gray-50 px-2 py-3 flex flex-col items-center justify-start gap-1 border-r border-gray-100">
                    <button 
                        onClick={() => handleVote('UP')}
                        className={`p-1 rounded-full hover:bg-gray-100 ${
                            currentPost.user_vote === 'upvote' ? 'text-red-500' : 'text-gray-400'
                        }`}
                        disabled={!isAuthenticated}
                        title={!isAuthenticated ? "Log in to vote" : "Upvote"}
                        aria-label="Upvote post"
                    >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 4L4 15h16L12 4z" />
                        </svg>
                    </button>
                    
                    <span className={`text-xs font-bold ${
                        currentPost.user_vote === 'upvote' 
                            ? 'text-red-500' 
                            : currentPost.user_vote === 'downvote' 
                                ? 'text-blue-500' 
                                : 'text-gray-800'
                    }`}>
                        {currentPost.score ?? 0}
                    </span>
                    
                    <button 
                        onClick={() => handleVote('DOWN')}
                        className={`p-1 rounded-full hover:bg-gray-100 ${
                            currentPost.user_vote === 'downvote' ? 'text-blue-500' : 'text-gray-400'
                        }`}
                        disabled={!isAuthenticated}
                        title={!isAuthenticated ? "Log in to vote" : "Downvote"}
                        aria-label="Downvote post"
                    >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 20l8-11H4l8 11z" />
                        </svg>
                    </button>
                </div>

                {/* Main content */}
                <div className="flex-1 p-4">
                    {/* Post metadata */}
                    <div className="flex items-center text-xs text-gray-500 mb-2">
                        {/* Community icon */}
                        <div className="w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center mr-1 text-xs font-bold">
                            {currentPost.community?.name?.charAt(0).toUpperCase() || 'C'}
                        </div>
                        
                        {/* Community link */}
                        <Link href={`/c/${communityPath}`} className="font-medium text-red-600 hover:underline mr-2">
                            c/{currentPost.community?.name || 'unknown'}
                        </Link>
                        
                        <span className="mx-1 text-gray-400">•</span>
                        
                        <span>Posted by</span>
                        
                        {/* User link */}
                        <Link href={`/users/${currentPost.user?.username || '[deleted]'}`} className="ml-1 hover:underline">
                            u/{currentPost.user?.username || '[deleted]'}
                        </Link>
                        
                        <span className="mx-1 text-gray-400">•</span>
                        
                        <span>{formatDistanceToNow(new Date(currentPost.created_at || Date.now()), { addSuffix: true })}</span>
                    </div>
                    
                    {/* Post title and content */}
                    <Link href={`/c/${communityPath}/post/${currentPost.path}`} className="block">
                        <h2 className="text-lg font-semibold mb-2 hover:text-red-600 transition-colors">
                            {currentPost.title}
                        </h2>
                        
                        {currentPost.content && (
                            <p className="text-sm text-gray-700 line-clamp-3 mb-3">
                                {currentPost.content}
                            </p>
                        )}
                    </Link>
                    
                    {/* Post actions */}
                    <div className="flex items-center mt-2 text-xs text-gray-500">
                        {/* Comments */}
                        <Link href={`/c/${communityPath}/post/${currentPost.path}#comments`} 
                            className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full mr-2">
                            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                            </svg>
                            <span>{currentPost.comment_count ?? 0} Comments</span>
                        </Link>
                        
                        {/* Share button */}
                        <button className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full mr-2">
                            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
                            </svg>
                            <span>Share</span>
                        </button>
                        
                        {/* Save button */}
                        <button className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
                            <span>Save</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
} 