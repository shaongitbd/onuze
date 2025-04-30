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

            // Call the API function
            await action(currentPost.path);

        } catch (err) {
            console.error(`Error ${voteDirection === 'UP' ? 'upvoting' : 'downvoting'} post:`, err);
            // Revert optimistic update on error
            setCurrentPost(previousPost);
            // Optionally show error message to user
        }
    };

    if (!currentPost) return null;

    // Check if post has media using the new `media_display` array
    const hasMedia = currentPost.media_display && currentPost.media_display.length > 0;
    // Get first media item for card preview
    const firstMedia = hasMedia ? currentPost.media_display[0] : null;
    // Determine media type from the first item
    const isImage = firstMedia && firstMedia.media_type === 'image';
    const isVideo = firstMedia && firstMedia.media_type === 'video';

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
                        <div className="w-5 h-5 rounded-full bg-gray-700 text-white flex items-center justify-center mr-1 text-xs font-bold">
                            {currentPost.community?.name?.charAt(0).toUpperCase() || 'C'}
                        </div>
                        
                        {/* Community link */}
                        <Link href={`/c/${communityPath}`} className="font-medium text-gray-800 hover:underline mr-2">
                            c/{currentPost.community?.name || 'unknown'}
                        </Link>
                        
                        <span className="mx-1 text-gray-400">•</span>
                        
                        <span>Posted by</span>
                        
                        {/* User link */}
                        <Link href={`/user/${currentPost.user?.username || '[deleted]'}`} className="ml-1 hover:underline">
                            u/{currentPost.user?.username || '[deleted]'}
                        </Link>
                        
                        <span className="mx-1 text-gray-400">•</span>
                        
                        <span>{formatDistanceToNow(new Date(currentPost.created_at || Date.now()), { addSuffix: true })}</span>
                        
                        {/* Pinned post indicator */}
                        {currentPost.is_pinned && (
                            <>
                                <span className="mx-1 text-gray-400">•</span>
                                <span className="text-green-600 flex items-center" title="Pinned by moderator">
                                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M5 5a2 2 0 012-2h6a2 2 0 012 2v2a2 2 0 01-2 2H7a2 2 0 01-2-2V5z" />
                                        <path d="M10 12a2 2 0 100 4 2 2 0 000-4z" />
                                        <path fillRule="evenodd" d="M10 10a1 1 0 100-2V5.5a.5.5 0 01.5-.5h4a.5.5 0 01.5.5v4a.5.5 0 01-.5.5H10z" clipRule="evenodd" />
                                    </svg>
                                    <span className="font-medium">Pinned</span>
                                </span>
                            </>
                        )}
                    </div>
                    
                    {/* Post title */}
                    <Link href={`/c/${communityPath}/post/${currentPost.path}`} className="block">
                        <h2 className="text-lg font-semibold mb-2 hover:text-red-600 transition-colors">
                            {currentPost.title}
                        </h2>
                    </Link>
                    
                    {/* Media Content or Text Content */}
                    <Link href={`/c/${communityPath}/post/${currentPost.path}`} className="block mb-3">
                        {hasMedia && firstMedia ? (
                            <div className="relative overflow-hidden rounded-md">
                                {isImage ? (
                                    <div className="flex justify-start">
                                        <img 
                                            src={firstMedia.media_url} 
                                            alt={currentPost.title}
                                            className="max-h-96 w-auto rounded-md object-contain"
                                        />
                                    </div>
                                ) : isVideo ? (
                                    <div className="flex justify-start">
                                        <video 
                                            controls
                                            poster={firstMedia.thumbnail_url || undefined}
                                            className="max-h-96 w-auto rounded-md bg-black object-contain"
                                        >
                                            <source src={firstMedia.media_url} type={`video/${firstMedia.media_url?.split('.').pop() || 'mp4'}`} />
                                            Your browser does not support the video tag.
                                        </video>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center p-4 bg-gray-100 rounded-md">
                                        <svg className="w-6 h-6 text-gray-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0v12h8V4H6z" clipRule="evenodd" />
                                        </svg>
                                        <span className="text-sm font-medium text-gray-500">View attachment</span>
                                    </div>
                                )}
                                
                                {hasMedia && currentPost.media_display.length > 1 && (
                                    <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded-md">
                                        +{currentPost.media_display.length - 1} more
                                    </div>
                                )}
                            </div>
                        ) : currentPost.content ? (
                            <p className="text-sm text-gray-700 line-clamp-3">
                                {currentPost.content}
                            </p>
                        ) : null}
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
                        
                        
                    </div>
                </div>
            </div>
        </div>
    );
} 