'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import InfiniteScroll from 'react-infinite-scroll-component';
import { 
  getPostByPath, getComments, createComment, deletePost, deleteComment, 
  upvotePost, downvotePost, upvoteComment, downvoteComment, updateComment,
  joinCommunity, leaveCommunity,
  getCommunityDetails, lockPost, unlockPost, pinPost, unpinPost
} from '../../../../../lib/api';
import { useAuth } from '../../../../../lib/auth';
import Spinner from '../../../../../components/Spinner';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { LockClosedIcon, LockOpenIcon, MapPinIcon as PinIcon, TrashIcon, PencilIcon, FlagIcon, ShareIcon, LinkIcon } from '@heroicons/react/24/solid'; // Changed PinIcon to MapPinIcon

export default function PostDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { communityName, postPath } = params;
  
  const [post, setPost] = React.useState(null);
  const [comments, setComments] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [commentText, setCommentText] = React.useState('');
  const [submittingComment, setSubmittingComment] = React.useState(false);
  const [commentError, setCommentError] = React.useState('');
  const { user, isAuthenticated, isLoading } = useAuth();
  const [showShareMenu, setShowShareMenu] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const shareMenuRef = useRef(null);
  const [joiningCommunity, setJoiningCommunity] = useState(false);
  const [sortOption, setSortOption] = useState('new');
  const [timeFilter, setTimeFilter] = useState('all');
  const [showTimeFilter, setShowTimeFilter] = useState(false);
  const [isFiltering, setIsFiltering] = useState(false); // Loading state for filtering
  
  // Added for infinite comments scrolling
  const [nextCommentsUrl, setNextCommentsUrl] = useState(null);
  const [hasMoreComments, setHasMoreComments] = useState(false);
  const [loadingMoreComments, setLoadingMoreComments] = useState(false);
  const [totalCommentCount, setTotalCommentCount] = useState(0);

  // Moderator State
  const [isModerator, setIsModerator] = useState(false);
  const [communityDetails, setCommunityDetails] = useState(null); // To store community data
  const [showLockModal, setShowLockModal] = useState(false);
  const [lockReason, setLockReason] = useState('');
  const [moderatorActionLoading, setModeratorActionLoading] = useState(false);

  // Refetch post data helper
  const refetchPostData = async () => {
    if (!postPath) return;
    try {
      const postData = await getPostByPath(postPath);
      setPost(postData);
    } catch (err) {
      console.error("Error refetching post data:", err);
      // Handle error appropriately, maybe show a notification
    }
  };

  // Fetch post, comments, and community details
  useEffect(() => {
    async function fetchAllDetails() {
      try {
        setLoading(true);
        setError(''); // Reset error on new fetch
        const postData = await getPostByPath(postPath);
        setPost(postData);
        
        if (postData && postData.path) {
          await fetchComments(postData.path, 'new', 'all', true);
          
          // Fetch community details if we have a community path
          if (postData.community?.path) {
            try {
              const communityData = await getCommunityDetails(postData.community.path);
              setCommunityDetails(communityData);
              // Check if the current user is a moderator
              if (user && communityData?.moderators) {
                const isMod = communityData.moderators.some(mod => mod.user_id === user.id);
                setIsModerator(isMod);
              } else {
                setIsModerator(false);
              }
            } catch (communityErr) {
              console.error('Error fetching community details:', communityErr);
              // Handle community fetch error - maybe post can still be viewed
            }
          } else {
            setIsModerator(false); // No community path, cannot be moderator
          }

        } else {
          console.warn("Post data did not contain a path or community info.");
          setComments([]);
          setIsModerator(false);
        }
      } catch (err) {
        console.error('Error fetching post details:', err);
        setError('Post not found or an error occurred.');
        setPost(null); // Ensure post is null on error
        setIsModerator(false);
      } finally {
        setLoading(false);
      }
    }

    if (postPath && user !== undefined) { // Ensure auth state is resolved before fetching
      fetchAllDetails();
    } else if (!isLoading && user === null && postPath) {
      // Handle fetching public post data when not logged in
      fetchAllDetails(); 
    }

  }, [postPath, user, isLoading]); // Add user and isLoading dependency

  // Fetch comments with sorting and filtering
  const fetchComments = async (postPath, sort = sortOption, time = timeFilter, isInitialLoad = false, nextUrl = null) => {
    try {
      if (isInitialLoad) {
        // Already set by the parent fetchPostAndComments function
      } else if (!nextUrl) {
        setIsFiltering(true);
      } else {
        setLoadingMoreComments(true);
      }
      
      let commentsData;
      
      if (nextUrl) {
        // Fetch next page of comments using the URL
        try {
          const response = await fetch(nextUrl, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          });
          
          if (!response.ok) {
            throw new Error('Failed to fetch more comments');
          }
          
          commentsData = await response.json();
        } catch (err) {
          console.error('Error fetching next page of comments:', err);
          throw err;
        }
      } else {
        // Build query params for initial fetch
        let queryParams = '';
        if (sort && sort !== 'new') queryParams += `&sort=${sort}`;
        if (time && time !== 'all' && (sort === 'top' || sort === 'controversial' || sort === 'hot')) {
          queryParams += `&time=${time}`;
        }
        
        commentsData = await getComments(postPath, queryParams);
      }
      
      // Update the next URL and hasMore status
      setNextCommentsUrl(commentsData.next);
      setHasMoreComments(!!commentsData.next);
      setTotalCommentCount(commentsData.count || 0);
      
          if (commentsData && Array.isArray(commentsData.results)) {
            // Create a flat map of all comments by ID
            const commentsById = {};
            commentsData.results.forEach(comment => {
              commentsById[comment.id] = {...comment, replies: []};
            });
            
            // Build the comment tree
            const rootComments = [];
            commentsData.results.forEach(comment => {
              // If the comment has a parent and we have that parent in our map
              if (comment.parent && commentsById[comment.parent]) {
                // Add this comment as a reply to its parent
                commentsById[comment.parent].replies.push(commentsById[comment.id]);
              } else {
                // This is a top-level comment or has a parent we don't have data for
                rootComments.push(commentsById[comment.id]);
              }
            });
            
        // Custom sort based on selected option
            const sortComments = (comments) => {
          switch (sort) {
            case 'old':
              comments.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
              break;
            case 'top':
              comments.sort((a, b) => (b.score || 0) - (a.score || 0));
              break;
            case 'controversial':
              // For controversial, we're assuming backend handles this
              break;
            case 'hot':
              // For hot, we're assuming backend handles this
              break;
            case 'new':
            default:
              comments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
              break;
          }
          
          // Always sort replies by newest first (this could be customized further if needed)
              comments.forEach(comment => {
                if (comment.replies && comment.replies.length > 0) {
              comment.replies.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                  sortComments(comment.replies);
                }
              });
              return comments;
            };
            
        const sortedComments = sortComments(rootComments);
        
        // For initial load or filter change, replace comments
        // For infinite scroll (nextUrl exists), append new comments
        if (nextUrl) {
          setComments(prevComments => [...prevComments, ...sortedComments]);
          } else {
          setComments(sortedComments);
          }
        } else {
        console.warn("Comments data received in unexpected format:", commentsData);
        if (!nextUrl) {
          // Only reset for initial load
          setComments([]);
        }
        }
      } catch (err) {
      console.error('Error fetching comments:', err);
      } finally {
      setIsFiltering(false);
      setLoadingMoreComments(false);
    }
  };

  // Function to load more comments for infinite scrolling
  const loadMoreComments = () => {
    if (nextCommentsUrl && !loadingMoreComments && post?.path) {
      fetchComments(post.path, sortOption, timeFilter, false, nextCommentsUrl);
    }
  };

  // Handle sort option change
  const handleSortChange = (newSort) => {
    setSortOption(newSort);
    // Only show time filter for relevant sort options
    setShowTimeFilter(['top', 'controversial', 'hot'].includes(newSort));
    if (!['top', 'controversial', 'hot'].includes(newSort)) {
      setTimeFilter('all');
    }
    if (post && post.path) {
      // Reset comments and fetch with new sorting
      setComments([]);
      setNextCommentsUrl(null);
      setHasMoreComments(false);
      fetchComments(post.path, newSort, timeFilter);
    }
  };

  // Handle time filter change
  const handleTimeFilterChange = (newTime) => {
    setTimeFilter(newTime);
    if (post && post.path) {
      // Reset comments and fetch with new time filter
      setComments([]);
      setNextCommentsUrl(null);
      setHasMoreComments(false);
      fetchComments(post.path, sortOption, newTime);
    }
  };

  // Handle click outside to close share menu
  React.useEffect(() => {
    function handleClickOutside(event) {
      if (shareMenuRef.current && !shareMenuRef.current.contains(event.target)) {
        setShowShareMenu(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [shareMenuRef]);

  // Function to copy post URL to clipboard
  const copyToClipboard = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      alert('Link copied to clipboard!');
      setShowShareMenu(false);
    }).catch(err => {
      console.error('Could not copy text: ', err);
    });
  };

  // Function to share on social media
  const shareOn = (platform) => {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(post?.title || 'Check out this post');
    let shareUrl = '';
    
    switch(platform) {
      case 'twitter':
        shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
        break;
      case 'facebook':
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
        break;
      case 'whatsapp':
        shareUrl = `https://api.whatsapp.com/send?text=${title}%20${url}`;
        break;
      case 'reddit':
        shareUrl = `https://www.reddit.com/submit?url=${url}&title=${title}`;
        break;
      default:
        return;
    }
    
    window.open(shareUrl, '_blank', 'width=600,height=400');
    setShowShareMenu(false);
  };

  // Function to handle report
  const handleReport = () => {
    setReportModalOpen(true);
  };

  // Function to submit report
  const submitReport = (reason) => {
    alert(`Post reported for: ${reason}`);
    setReportModalOpen(false);
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    
    if (!commentText.trim()) {
      setCommentError('Comment text is required');
      return;
    }

    if (!user) {
      router.push('/login?redirect=' + encodeURIComponent(`/c/${communityName}/post/${postPath}`));
      return;
    }

    if (!post || !post.path) {
      setCommentError('Cannot submit comment: Post data is missing.');
      return;
    }

    try {
      setSubmittingComment(true);
      setCommentError('');

      const newComment = await createComment({
        content: commentText,
        post: post.id,
        parent: ""
      });

      // Add new comment to the list
      setComments([newComment, ...comments]);
      setCommentText(''); // Clear input
    } catch (err) {
      console.error('Error creating comment:', err);
      setCommentError(err.message || 'Failed to post comment. Please try again.');
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleVote = async (voteDirection) => {
    if (!isAuthenticated || !post) {
      router.push(`/login?redirect=${encodeURIComponent(window.location.pathname)}`);
      return;
    }
    
    // Determine which API function to call
    const action = voteDirection === 'UP' ? upvotePost : downvotePost;
    
    try {
      // Call the specific upvote/downvote API function
      await action(post.path);
      
      // Optimistic UI update (same logic as before, but now triggered after specific API call)
      setPost(prevPost => {
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
    } catch (err) {
      console.error(`Error ${voteDirection === 'UP' ? 'upvoting' : 'downvoting'} post:`, err);
      // Optionally revert optimistic update or show error to user
      // For now, just log the error
    }
  };

  // Handle deleting the post (updated for moderators)
  const handleDeletePost = async () => {
    const canDelete = (isAuthenticated && user && post?.user?.id === user.id) || isModerator;
    
    if (!canDelete) {
      alert('You are not authorized to delete this post.');
      return;
    }

    if (window.confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
      try {
        setModeratorActionLoading(true); // Show loading indicator
        await deletePost(post.path);
        alert('Post deleted successfully.');
        router.push(`/c/${communityName}`); 
      } catch (err) {
        console.error('Error deleting post:', err);
        setError(err.message || 'Failed to delete post.');
        setModeratorActionLoading(false); // Hide loading on error
      }
      // No finally setLoading(false) here, because we navigate away on success
    }
  };
  
  // Handle deleting a comment
  const handleDeleteComment = async (commentId) => {
    // Find comment recursively in the nested structure
    const findCommentById = (comments, id) => {
      for (const comment of comments) {
        if (comment.id === id) {
          return comment;
        }
        
        if (comment.replies && comment.replies.length > 0) {
          const found = findCommentById(comment.replies, id);
          if (found) return found;
        }
      }
      return null;
    };
    
    const commentToDelete = findCommentById(comments, commentId);
    
    if (!isAuthenticated || !user || commentToDelete?.user?.id !== user.id) {
      alert('You are not authorized to delete this comment.');
      return;
    }

    if (window.confirm('Are you sure you want to delete this comment?')) {
      try {
        await deleteComment(commentId);
        
        // Remove the comment from the local state (recursively)
        const removeCommentFromArray = (commentsArray, id) => {
          return commentsArray.filter(comment => {
            if (comment.id === id) {
              return false; // remove this comment
            }
            
            // Keep this comment but update its replies recursively
            if (comment.replies && comment.replies.length > 0) {
              comment.replies = removeCommentFromArray(comment.replies, id);
            }
            
            return true;
          });
        };
        
        setComments(prevComments => removeCommentFromArray(prevComments, commentId));
        alert('Comment deleted successfully.');
      } catch (err) {
        console.error('Error deleting comment:', err);
        alert(err.message || 'Failed to delete comment.'); // Show error to user
      }
    }
  };

  // Handle voting on a comment
  const handleCommentVote = async (commentId, voteDirection) => {
    if (!isAuthenticated) {
      router.push(`/login?redirect=${encodeURIComponent(window.location.pathname)}`);
      return;
    }
    
    const action = voteDirection === 'UP' ? upvoteComment : downvoteComment;
    
    try {
      await action(commentId);
      
      // Optimistic UI update for comments - ensuring deep nesting is handled
      setComments(prevComments => 
        updateNestedComments(prevComments, commentId, voteDirection)
      );
    } catch (err) {
      console.error(`Error ${voteDirection === 'UP' ? 'upvoting' : 'downvoting'} comment ${commentId}:`, err);
    }
  };
  
  // Helper function for updating nested comments with proper vote indicators
  const updateNestedComments = (comments, commentId, voteDirection) => {
    return comments.map(comment => {
          if (comment.id === commentId) {
            const voteValue = voteDirection === 'UP' ? 1 : -1;
        const currentVote = comment.user_vote; 
            let scoreChange = 0;

            if (voteValue === 1) { // Upvoting
                scoreChange = currentVote === 'upvote' ? -1 : (currentVote === 'downvote' ? 2 : 1);
            } else { // Downvoting (-1)
                scoreChange = currentVote === 'downvote' ? 1 : (currentVote === 'upvote' ? -2 : -1);
            }
            
            return {
              ...comment,
              score: (comment.score ?? 0) + scoreChange,
          user_vote: voteValue === 1 
            ? (currentVote === 'upvote' ? null : 'upvote') 
            : (currentVote === 'downvote' ? null : 'downvote')
        };
      }
      
      // Check if this comment has replies to update
      if (comment.replies && comment.replies.length > 0) {
        return {
          ...comment,
          replies: updateNestedComments(comment.replies, commentId, voteDirection)
        };
      }
      
      return comment;
    });
  };

  // Handle editing a comment
  const handleEditComment = async (commentId, updatedContent) => {
    try {
      // Update comment in the backend
      await updateComment(commentId, { content: updatedContent });
      
      // Update the comment in the local state
      setComments(prevComments => 
        prevComments.map(comment => 
          comment.id === commentId 
            ? { ...comment, content: updatedContent, isEditing: false } 
            : comment
        )
      );
    } catch (err) {
      console.error('Error updating comment:', err);
      // Update error state in the specific comment
      setComments(prevComments => 
        prevComments.map(comment => 
          comment.id === commentId 
            ? { ...comment, editError: err.message } 
            : comment
        )
      );
    }
  };

  // Handle joining a community
  const handleJoinCommunity = async () => {
    if (!isAuthenticated) {
      router.push(`/login?redirect=${encodeURIComponent(window.location.pathname)}`);
      return;
    }
    
    try {
      setJoiningCommunity(true);
      await joinCommunity(post.community.id);
      // Update the post with is_member set to true
      setPost(prevPost => ({
        ...prevPost,
        community: {
          ...prevPost.community,
          is_member: true
        }
      }));
    } catch (err) {
      console.error('Error joining community:', err);
      alert('Failed to join community. Please try again.');
    } finally {
      setJoiningCommunity(false);
    }
  };
  
  // Handle leaving a community
  const handleLeaveCommunity = async () => {
    if (!isAuthenticated) {
      return;
    }
    
    try {
      setJoiningCommunity(true);
      await leaveCommunity(post.community.id);
      // Update the post with is_member set to false
      setPost(prevPost => ({
        ...prevPost,
        community: {
          ...prevPost.community,
          is_member: false
        }
      }));
    } catch (err) {
      console.error('Error leaving community:', err);
      alert('Failed to leave community. Please try again.');
    } finally {
      setJoiningCommunity(false);
    }
  };

  // Moderator Actions Handlers
  const handlePin = async () => {
    if (!isModerator || !post || moderatorActionLoading) return;
    try {
      setModeratorActionLoading(true);
      await pinPost(post.path);
      await refetchPostData(); // Refetch to get updated pin status
    } catch (err) {
      console.error('Error pinning post:', err);
      alert('Failed to pin post.');
    } finally {
      setModeratorActionLoading(false);
    }
  };

  const handleUnpin = async () => {
    if (!isModerator || !post || moderatorActionLoading) return;
    try {
      setModeratorActionLoading(true);
      await unpinPost(post.path);
      await refetchPostData(); // Refetch to get updated pin status
    } catch (err) {
      console.error('Error unpinning post:', err);
      alert('Failed to unpin post.');
    } finally {
      setModeratorActionLoading(false);
    }
  };

  const openLockModal = () => {
    if (!isModerator || moderatorActionLoading) return;
    setLockReason(''); // Reset reason
    setShowLockModal(true);
  };

  const closeLockModal = () => {
    setShowLockModal(false);
    setLockReason('');
  };

  const handleLock = async () => {
    if (!isModerator || !post || moderatorActionLoading) return;
    try {
      setModeratorActionLoading(true);
      await lockPost(post.path, { reason: lockReason || null }); // Send reason if provided
      await refetchPostData(); // Refetch to get updated lock status
      closeLockModal();
    } catch (err) {
      console.error('Error locking post:', err);
      alert(`Failed to lock post: ${err.message || 'Unknown error'}`);
    } finally {
      setModeratorActionLoading(false);
    }
  };

  const handleUnlock = async () => {
    if (!isModerator || !post || moderatorActionLoading) return;
    try {
      setModeratorActionLoading(true);
      await unlockPost(post.path);
      await refetchPostData(); // Refetch to get updated lock status
    } catch (err) {
      console.error('Error unlocking post:', err);
      alert('Failed to unlock post.');
    } finally {
      setModeratorActionLoading(false);
    }
  };

  if (loading || isLoading || (postPath && !post && !error)) { // Added condition for initial load state
    return (
      <div className="p-4 flex justify-center items-center min-h-[300px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!post) {
    return (
      <div className="p-4 max-w-3xl mx-auto">
        <div className="bg-red-50 p-4 rounded-md text-red-700">
          {error || `Post not found.`}
        </div>
        <div className="mt-4">
          <Link href={`/c/${communityName}`} className="text-indigo-600 hover:underline">
            Back to c/{communityName}
          </Link>
        </div>
      </div>
    );
  }

  // Check if user owns the post
  const isOwner = isAuthenticated && user && post?.user?.id === user.id;
  const canEdit = isOwner; // Only owner can edit content
  const editUrl = `/c/${communityName}/post/${postPath}/edit`;

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Main content - Increased width */}
        <div className="lg:w-9/12">
          {/* Post */}
          <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
            <div className="flex">
              {/* Left sidebar for votes */}
              <div className="bg-gray-50 px-2 py-3 flex flex-col items-center justify-start gap-1">
                <button 
                  onClick={() => handleVote('UP')}
                  className={`p-1 rounded-full hover:bg-gray-100 ${
                    post.user_vote === 'upvote' ? 'text-red-500' : 'text-gray-400'
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
                  post.user_vote === 'upvote' 
                    ? 'text-red-500' 
                    : post.user_vote === 'downvote' 
                      ? 'text-blue-500' 
                      : 'text-gray-800'
                }`}>
                  {post?.score ?? 0}
                </span>
                
                <button 
                  onClick={() => handleVote('DOWN')}
                  className={`p-1 rounded-full hover:bg-gray-100 ${
                    post.user_vote === 'downvote' ? 'text-blue-500' : 'text-gray-400'
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
                    {communityName?.charAt(0).toUpperCase() || 'C'}
                  </div>
                  
                  {/* Community link */}
                  <Link href={`/c/${communityName}`} className="font-medium text-gray-800 hover:underline mr-2">
                    c/{communityName}
                  </Link>
                  
                  <span className="mx-1 text-gray-400">•</span>
                  
                  <span>Posted by</span>
                  
                  {/* User link */}
                  <Link href={`/users/${post?.user?.username || '[deleted]'}`} className="ml-1 hover:underline">
                    u/{post?.user?.username || '[deleted]'}
                  </Link>
                  
                  <span className="mx-1 text-gray-400">•</span>
                  
                  <span>{formatDistanceToNow(new Date(post?.created_at || Date.now()), { addSuffix: true })}</span>

                  {/* Pinned Icon */}
                  {post?.is_pinned && (
                    <span title="Pinned by moderator" className="ml-2 text-green-600 flex items-center">
                      <PinIcon className="w-4 h-4 mr-1" />
                      <span className="text-xs font-medium">Pinned</span>
                    </span>
                  )}
                  {/* Locked Icon */}
                  {post?.is_locked && (
                     <span 
                       title={post.locked_reason ? `Locked: ${post.locked_reason}` : "Locked by moderator"} 
                       className="ml-2 text-yellow-600 flex items-center"
                     >
                      <LockClosedIcon className="w-4 h-4 mr-1" />
                       <span className="text-xs font-medium">Locked</span>
                    </span>
                  )}
                </div>
                
                {/* Post Content */}
                <div className="px-4 pb-4">
                  {post.title && (
                    <h1 className="text-xl font-semibold mb-2 text-gray-800">
                      {post.title}
                    </h1>
                  )}
                  
                  {/* Media Display Section */}
                  {post.media_display && post.media_display.length > 0 ? (
                    <div className="space-y-2 mb-4">
                      {post.media_display.map((mediaItem, index) => (
                        <div key={mediaItem.id || index} className="max-w-full overflow-hidden">
                          {mediaItem.media_type === 'image' ? (
                            <img 
                              src={mediaItem.media_url} 
                              alt={`Post media ${index + 1}`}
                              className="max-h-[70vh] w-auto rounded-md object-contain"
                            />
                          ) : mediaItem.media_type === 'video' ? (
                            <video 
                              controls 
                              poster={mediaItem.thumbnail_url || undefined}
                              className="max-h-[70vh] w-auto rounded-md bg-black"
                            >
                              <source src={mediaItem.media_url} type={`video/${mediaItem.media_url.split('.').pop() || 'mp4'}`} />
                              Your browser does not support the video tag.
                            </video>
                          ) : (
                            <div className="p-4 bg-gray-100 rounded-md text-center text-gray-500">
                              Unsupported media type: {mediaItem.media_type}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : post.content ? (
                    // Only show content if there's no media_display
                    <div 
                      className="prose prose-sm max-w-none text-gray-700" 
                      dangerouslySetInnerHTML={{ __html: post.content }} 
                    />
                  ) : null}
                </div>
                
                {/* Post actions */}
                <div className="flex flex-wrap items-center mt-2 text-xs text-gray-500 gap-x-3 gap-y-1">
                  {/* Comments count */}
                  <div className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full cursor-pointer">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                      <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                    </svg>
                    <span>{comments.length} Comments</span>
                  </div>
                  
                  {/* Share button */}
                  <div className="relative" ref={shareMenuRef}>
                    <button 
                      onClick={() => setShowShareMenu(!showShareMenu)}
                      className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full mr-2 text-gray-500 hover:text-red-600"
                    >
                      <ShareIcon className="w-4 h-4 mr-1" />
                      <span>Share</span>
                    </button>
                    
                    {/* Share Popup Menu */}
                    {showShareMenu && (
                      <div className="absolute mt-2 w-48 bg-white rounded-md shadow-lg overflow-hidden z-20">
                        <button 
                          onClick={copyToClipboard}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <LinkIcon className="w-4 h-4 mr-2" /> {/* Changed icon */}
                          Copy Link
                        </button>
                        <button 
                          onClick={() => shareOn('twitter')}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <svg className="w-4 h-4 mr-2 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                          </svg>
                          Twitter
                        </button>
                        <button 
                          onClick={() => shareOn('facebook')}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <svg className="w-4 h-4 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                          </svg>
                          Facebook
                        </button>
                        <button 
                          onClick={() => shareOn('whatsapp')}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                          </svg>
                          WhatsApp
                        </button>
                        <button 
                          onClick={() => shareOn('reddit')}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <svg className="w-4 h-4 mr-2 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
                          </svg>
                          Reddit
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {/* Report button */}
                  <button 
                    onClick={handleReport}
                    className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full text-gray-500 hover:text-red-600"
                  >
                    <FlagIcon className="w-4 h-4 mr-1" /> {/* Changed icon */}
                    <span>Report</span>
                  </button>
                  
                  {/* Edit button (Owner only) */}
                  {canEdit && (
                      <Link href={editUrl} 
                      className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full text-gray-500 hover:text-red-600">
                       <PencilIcon className="w-4 h-4 mr-1" /> {/* Changed icon */}
                        <span>Edit</span>
                      </Link>
                  )}
                      
                  {/* Delete button (Owner or Moderator) */}
                  {(isOwner || isModerator) && (
                      <button 
                        onClick={handleDeletePost}
                        className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full text-gray-500 hover:text-red-600"
                      disabled={moderatorActionLoading} // Use moderator loading state
                    >
                       <TrashIcon className="w-4 h-4 mr-1" /> {/* Changed icon */}
                      <span>{moderatorActionLoading ? 'Deleting...' : 'Delete'}</span>
                      </button>
                  )}

                  {/* Moderator Actions */}
                  {isModerator && (
                    <>
                      {/* Pin/Unpin */}
                      {post?.is_pinned ? (
                        <button 
                          onClick={handleUnpin}
                          className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full text-green-600 hover:text-green-800"
                          disabled={moderatorActionLoading}
                          title="Unpin Post"
                        >
                           <PinIcon className="w-4 h-4 mr-1" /> 
                          <span>{moderatorActionLoading ? 'Unpinning...' : 'Unpin'}</span>
                        </button>
                      ) : (
                         <button 
                          onClick={handlePin}
                          className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full text-gray-500 hover:text-green-600"
                          disabled={moderatorActionLoading}
                          title="Pin Post"
                        >
                          <PinIcon className="w-4 h-4 mr-1" /> 
                          <span>{moderatorActionLoading ? 'Pinning...' : 'Pin'}</span>
                        </button>
                      )}

                       {/* Lock/Unlock */}
                      {post?.is_locked ? (
                         <button 
                          onClick={handleUnlock}
                          className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full text-yellow-600 hover:text-yellow-800"
                          disabled={moderatorActionLoading}
                          title="Unlock Post"
                        >
                          <LockOpenIcon className="w-4 h-4 mr-1" />
                          <span>{moderatorActionLoading ? 'Unlocking...' : 'Unlock'}</span>
                        </button>
                      ) : (
                        <button 
                          onClick={openLockModal}
                          className="flex items-center hover:bg-gray-100 px-2 py-1 rounded-full text-gray-500 hover:text-yellow-600"
                          disabled={moderatorActionLoading}
                           title="Lock Post"
                       >
                          <LockClosedIcon className="w-4 h-4 mr-1" />
                          <span>{moderatorActionLoading ? 'Locking...' : 'Lock'}</span>
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
          
          {/* Comments section with integrated comment form */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="p-4">
              <h2 className="text-lg font-semibold mb-4">
                Comments ({totalCommentCount})
              </h2>
              
              {/* Comment section */}
              <div className="mt-6">
                <h3 className="text-lg font-medium mb-2">Comments</h3>
                
                {/* Comment form */}
                <div className="mb-4 bg-white border border-gray-300 rounded-md p-4">
                  <textarea
                    className="w-full px-3 py-2 text-gray-700 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                    rows="4"
                    placeholder={isAuthenticated ? "What are your thoughts?" : "Login to comment"}
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    disabled={!isAuthenticated || submittingComment}
                  ></textarea>
                  
                  {commentError && (
                    <div className="text-red-500 text-sm mt-1">{commentError}</div>
                  )}
                  
                  <div className="flex justify-end mt-2">
                    <button
                      onClick={handleCommentSubmit}
                      disabled={!isAuthenticated || submittingComment || !commentText.trim()}
                      className={`px-4 py-2 font-medium rounded-md text-white ${
                        !isAuthenticated || submittingComment || !commentText.trim()
                          ? 'bg-gray-400 cursor-not-allowed'
                          : 'bg-indigo-600 hover:bg-indigo-700'
                      }`}
                    >
                      {submittingComment ? 'Submitting...' : 'Comment'}
                    </button>
                  </div>
                </div>
                
                {/* Lock Overlay for Comments */}
                {post?.is_locked && (
                   <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-800 text-sm flex items-center">
                     <LockClosedIcon className="w-4 h-4 mr-2 flex-shrink-0" />
                     <span>Comments on this post are locked. {post.locked_reason ? `Reason: ${post.locked_reason}` : ''}</span>
                  </div>
                )}
                
                {/* Comment sorting options */}
                <div className="flex flex-wrap items-center mb-4 border-b pb-2">
                  <div className="text-xs font-medium text-gray-500 mr-2">Sort comments by:</div>
                  <div className="flex flex-wrap gap-2">
                <button
                      className={`text-xs px-2 py-1 rounded ${sortOption === 'new' ? 'bg-gray-200 text-gray-800' : 'text-gray-500 hover:bg-gray-100'}`}
                      onClick={() => handleSortChange('new')}
                      disabled={isFiltering}
                    >
                      New
                    </button>
                    <button
                      className={`text-xs px-2 py-1 rounded ${sortOption === 'top' ? 'bg-gray-200 text-gray-800' : 'text-gray-500 hover:bg-gray-100'}`}
                      onClick={() => handleSortChange('top')}
                      disabled={isFiltering}
                    >
                      Top
                    </button>
                    <button
                      className={`text-xs px-2 py-1 rounded ${sortOption === 'controversial' ? 'bg-gray-200 text-gray-800' : 'text-gray-500 hover:bg-gray-100'}`}
                      onClick={() => handleSortChange('controversial')}
                      disabled={isFiltering}
                    >
                      Controversial
                    </button>
                    <button
                      className={`text-xs px-2 py-1 rounded ${sortOption === 'hot' ? 'bg-gray-200 text-gray-800' : 'text-gray-500 hover:bg-gray-100'}`}
                      onClick={() => handleSortChange('hot')}
                      disabled={isFiltering}
                    >
                      Hot
                    </button>
                    <button
                      className={`text-xs px-2 py-1 rounded ${sortOption === 'old' ? 'bg-gray-200 text-gray-800' : 'text-gray-500 hover:bg-gray-100'}`}
                      onClick={() => handleSortChange('old')}
                      disabled={isFiltering}
                    >
                      Old
                </button>
                  </div>
                  
                  {/* Time filter - only shown for relevant sort options */}
                  {showTimeFilter && (
                    <div className="flex items-center ml-4">
                      <div className="text-xs font-medium text-gray-500 mr-2">Time:</div>
                      <select
                        className="text-xs border rounded py-1 px-2 bg-white"
                        value={timeFilter}
                        onChange={(e) => handleTimeFilterChange(e.target.value)}
                        disabled={isFiltering}
                      >
                        <option value="all">All Time</option>
                        <option value="day">Today</option>
                        <option value="week">This Week</option>
                        <option value="month">This Month</option>
                        <option value="year">This Year</option>
                      </select>
            </div>
                    )}
                  
                  {/* Filtering indicator */}
                  {isFiltering && (
                    <div className="ml-2 flex items-center">
                      <div className="w-4 h-4 border-2 border-gray-400 border-t-blue-500 rounded-full animate-spin mr-1"></div>
                      <span className="text-xs text-gray-500">Updating...</span>
                  </div>
                  )}
          </div>
              
              {comments.length === 0 ? (
                <p className="text-gray-500">No comments yet. Be the first to comment!</p>
              ) : (
                  <InfiniteScroll
                    dataLength={comments.length}
                    next={loadMoreComments}
                    hasMore={hasMoreComments}
                    loader={
                      <div className="flex justify-center py-4">
                        <Spinner />
                      </div>
                    }
                    endMessage={
                      <p className="text-center text-sm text-gray-500 py-4">
                        {totalCommentCount > 0 
                          ? "You've seen all comments" 
                          : "No comments yet. Be the first to comment!"}
                      </p>
                    }
                  >
                <ul className="space-y-5">
                  {comments.map(comment => (
                    <CommentItem 
                      key={comment.id} 
                      comment={comment} 
                      post={post} 
                      handleDeleteComment={handleDeleteComment}
                      handleEditComment={handleEditComment}
                      handleCommentVote={handleCommentVote}
                      isAuthenticated={isAuthenticated}
                      user={user}
                      setComments={setComments}
                      createComment={createComment}
                      level={0}
                          isPostLocked={post?.is_locked} // Pass lock status down
                    />
                  ))}
                </ul>
                  </InfiniteScroll>
              )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Sidebar - Decreased width */}
        <div className="lg:w-3/12">
          {/* About Community */}
          <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
            <div className="px-4 py-3 bg-gray-50">
              <h2 className="text-base font-semibold">About Community</h2>
            </div>
            <div className="p-4">
               <Link href={`/c/${post?.community?.path}`}>
              <div className="flex items-center mb-4">
              <div className="w-20 h-20 rounded-full bg-white border-4 border-white shadow-md mr-4 flex-shrink-0 overflow-hidden">
              {post?.community?.icon_image ? (
                <img src={post?.community?.icon_image} alt={`${post?.community?.name} icon`} className="w-full h-full object-cover rounded-full" />
              ) : (
                <div className="w-full h-full bg-red-500 flex items-center justify-center text-white text-2xl font-bold rounded-full">
                  {post?.community?.name ? post?.community?.name.charAt(0).toUpperCase() : 'C'}
                </div>
              )}
              </div>
                
                <div>
                  <h3 className="font-bold text-lg">c/{communityName}</h3>
                  <p className="text-sm text-gray-500">Community page</p>
                </div>
              </div>
              </Link>
              
              {/* Community description */}
              {post?.community?.description && (
                <div className="mb-4 text-sm text-gray-700">
                  {post.community.description}
                </div>
              )}
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-gray-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/>
                  </svg>
                  <span>
                    Created {post?.community?.created_at ? 
                      formatDistanceToNow(new Date(post.community.created_at), { addSuffix: true }) : 
                      'some time ago'}
                  </span>
                </div>
                
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-gray-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
                  </svg>
                  <span>{post?.community?.member_count || 0} members</span>
                </div>
                
               
              </div>
              
              <div className="mt-4 pt-4">
                {isAuthenticated && post?.community ? (
                  post.community.is_member ? (
                    <div className="space-y-2">
                      <button
                        onClick={handleLeaveCommunity}
                        disabled={joiningCommunity}
                        className="block w-full border border-gray-300 text-gray-700 hover:bg-gray-100 text-center py-2 px-4 rounded-md transition-colors"
                      >
                        {joiningCommunity ? 'Leaving...' : 'Leave Community'}
                      </button>
                      <Link 
                        href={`/c/${communityName}`} 
                        className="block w-full bg-red-600 hover:bg-red-700 text-white text-center py-2 px-4 rounded-md transition-colors"
                      >
                        Visit Community
                      </Link>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <button
                        onClick={handleJoinCommunity}
                        disabled={joiningCommunity}
                        className="block w-full bg-red-600 hover:bg-red-700 text-white text-center py-2 px-4 rounded-md transition-colors"
                      >
                        {joiningCommunity ? 'Joining...' : 'Join Community'}
                      </button>
                      <Link 
                        href={`/c/${communityName}`} 
                        className="block w-full border border-gray-300 text-gray-700 hover:bg-gray-100 text-center py-2 px-4 rounded-md transition-colors"
                      >
                        Visit Community
                      </Link>
                    </div>
                  )
                ) : (
                  <Link 
                    href={`/c/${communityName}`} 
                    className="block w-full bg-red-600 hover:bg-red-700 text-white text-center py-2 px-4 rounded-md transition-colors"
                  >
                    Visit Community
                  </Link>
                )}
              </div>
            </div>
          </div>
          
          {/* Community Rules */}
          <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
            <div className="px-4 py-3 bg-gray-50">
              <h2 className="text-base font-semibold">Community Rules</h2>
            </div>
            <div className="p-4">
              <ul className="space-y-3 text-sm">
                <li className="flex items-start">
                  <span className="font-medium mr-2">1.</span>
                  <span>Be respectful to others</span>
                </li>
                <li className="flex items-start">
                  <span className="font-medium mr-2">2.</span>
                  <span>No spam or self-promotion</span>
                </li>
                <li className="flex items-start">
                  <span className="font-medium mr-2">3.</span>
                  <span>Posts must be relevant to the community</span>
                </li>
              </ul>
            </div>
          </div>
          
          {/* Related Communities */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-gray-50">
              <h2 className="text-base font-semibold">Related Communities</h2>
            </div>
            <div className="p-4">
              <ul className="space-y-3">
                <li>
                  <Link href="#" className="flex items-center hover:bg-gray-50 p-2 rounded-md transition-colors">
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center mr-2 text-sm font-bold text-gray-700">
                      S
                    </div>
                    <div>
                      <span className="font-medium block">c/similar</span>
                      <span className="text-xs text-gray-500">1.2k members</span>
                    </div>
                  </Link>
                </li>
                <li>
                  <Link href="#" className="flex items-center hover:bg-gray-50 p-2 rounded-md transition-colors">
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center mr-2 text-sm font-bold text-gray-700">
                      R
                    </div>
                    <div>
                      <span className="font-medium block">c/related</span>
                      <span className="text-xs text-gray-500">3.5k members</span>
                    </div>
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Report Modal */}
      {reportModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Report Post</h3>
              <button 
                onClick={() => setReportModalOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-gray-700 mb-4">Why are you reporting this post?</p>
            <div className="space-y-2">
              {["Spam", "Harassment", "Misinformation", "Hate speech", "Violence", "Other"].map((reason) => (
                <button 
                  key={reason}
                  onClick={() => submitReport(reason)}
                  className="w-full text-left px-4 py-2 rounded hover:bg-gray-50"
                >
                  {reason}
                </button>
              ))}
            </div>
            <div className="mt-6 flex justify-end">
              <button 
                onClick={() => setReportModalOpen(false)}
                className="px-4 py-2 text-sm text-gray-700 rounded hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

       {/* Lock Post Modal */}
      {showLockModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Lock Post</h3>
              <button 
                onClick={closeLockModal}
                className="text-gray-500 hover:text-gray-700"
                disabled={moderatorActionLoading}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-gray-700 mb-2">Optionally provide a reason for locking this post:</p>
            <textarea
              className="w-full px-3 py-2 text-gray-700 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent mb-4"
              rows="3"
              placeholder="Reason (optional)"
              value={lockReason}
              onChange={(e) => setLockReason(e.target.value)}
              disabled={moderatorActionLoading}
            ></textarea>
            <div className="mt-4 flex justify-end space-x-2">
              <button 
                onClick={closeLockModal}
                className="px-4 py-2 text-sm text-gray-700 rounded hover:bg-gray-100 border border-gray-300"
                disabled={moderatorActionLoading}
              >
                Cancel
              </button>
               <button 
                onClick={handleLock}
                className={`px-4 py-2 text-sm text-white rounded ${moderatorActionLoading ? 'bg-yellow-400 cursor-not-allowed' : 'bg-yellow-600 hover:bg-yellow-700'}`}
                disabled={moderatorActionLoading}
              >
                {moderatorActionLoading ? 'Locking...' : 'Lock Post'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 

// Comment item component for recursive rendering
const CommentItem = ({ 
  comment, 
  post, 
  handleDeleteComment, 
  handleEditComment, 
  handleCommentVote, 
  isAuthenticated, 
  user, 
  setComments, 
  createComment,
  level = 0,
  isPostLocked // New prop: receive lock status from parent
}) => {
  const DEFAULT_DISPLAY_LEVEL = 3; // Show comments up to this level by default
  const [showReplies, setShowReplies] = React.useState(level < DEFAULT_DISPLAY_LEVEL);
  const [showShareOptions, setShowShareOptions] = React.useState(false);
  const hasReplies = comment.replies && comment.replies.length > 0;
  const shareOptionsRef = React.useRef(null);
  
  // Calculate total number of all nested replies
  const countAllReplies = (comment) => {
    if (!comment.replies || comment.replies.length === 0) return 0;
    return comment.replies.length + 
      comment.replies.reduce((sum, reply) => sum + countAllReplies(reply), 0);
  };
  
  const totalReplyCount = countAllReplies(comment);

  // Determine if comment actions should be disabled due to post lock
  const actionsDisabled = isPostLocked || (isAuthenticated && user && comment?.user?.id !== user.id && comment.isEditing); // Disable edit/reply if locked or not owner during edit
  const voteDisabled = !isAuthenticated; // Voting disabled only if not logged in

  // Handle click outside to close share menu
  React.useEffect(() => {
    function handleClickOutside(event) {
      if (shareOptionsRef.current && !shareOptionsRef.current.contains(event.target)) {
        setShowShareOptions(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [shareOptionsRef]);

  // Function to copy comment URL to clipboard
  const copyCommentLinkToClipboard = () => {
    const url = `${window.location.href.split('#')[0]}#comment-${comment.id}`;
    navigator.clipboard.writeText(url).then(() => {
      alert('Comment link copied to clipboard!');
      setShowShareOptions(false);
    }).catch(err => {
      console.error('Could not copy text: ', err);
    });
  };
  
  return (
    <li className="pb-4 last:pb-0" id={`comment-${comment.id}`}>
      <div className="pb-2">
        {/* Comment header with profile pic and metadata */}
        <div className="flex items-center mb-2">
          {/* User avatar placeholder - wrapper div for positioning */}
          <div className="relative w-7 h-7 mr-2 flex-shrink-0">
            <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600">
              {comment?.user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            {/* Vertical thread line that aligns with avatar center */}
            {hasReplies && showReplies && (
              <div className="absolute w-[2px] bg-gray-400 left-1/2 -translate-x-1/2 top-full h-full"></div>
            )}
          </div>
          
          <span className="font-medium text-gray-800">{comment?.user?.username ?? '[deleted]'}</span>
          <span className="mx-2 text-gray-400">•</span>
          <span className="text-xs text-gray-500">
            {formatDistanceToNow(new Date(comment?.created_at || Date.now()), { addSuffix: true })}
          </span>
          <div className="flex-grow"></div>
          
          {/* Edit/Delete Buttons */}
          {isAuthenticated && user && comment?.user?.id === user.id && (
            <div className="flex items-center ml-auto">
              <button 
                onClick={() => {
                  // Toggle edit mode for this comment
                  setComments(prevComments => 
                    updateCommentInTree(prevComments, comment.id, c => ({
                      ...c, 
                      isEditing: true, 
                      editText: c.content
                    }))
                  );
                }} 
                className={`flex items-center px-2 py-1 rounded-full hover:bg-gray-100 text-gray-500 hover:text-red-600 text-xs mr-2 ${isPostLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={isPostLocked} // Disable edit button if post is locked
              >
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit
              </button>
              <button 
                onClick={() => handleDeleteComment(comment.id)} 
                className="flex items-center px-2 py-1 rounded-full hover:bg-gray-100 text-gray-500 hover:text-red-600 text-xs"
                disabled={actionsDisabled} // Disable delete button if post is locked or not owner
              >
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </div>
          )}
        </div>
        
        {/* Comment content */}
        <div className="mt-1 pl-9 text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
          {comment.isEditing ? (
            <div className="mb-4">
              {comment.editError && (
                <div className="mb-2 text-xs text-red-600">
                  {comment.editError}
                </div>
              )}
              <textarea
                value={comment.editText || ''}
                onChange={(e) => {
                  setComments(prevComments => 
                    updateCommentInTree(prevComments, comment.id, c => ({
                      ...c, 
                      editText: e.target.value
                    }))
                  );
                }}
                rows={3}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                placeholder="Edit your comment..."
              />
              <div className="flex justify-end mt-2">
                <button
                  type="button"
                  onClick={() => {
                    setComments(prevComments => 
                      updateCommentInTree(prevComments, comment.id, c => ({
                        ...c, 
                        isEditing: false, 
                        editText: null, 
                        editError: null
                      }))
                    );
                  }}
                  className="mr-2 px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                
                <button
                  type="button"
                  onClick={() => {
                    if (!comment.editText?.trim()) return;
                    handleEditComment(comment.id, comment.editText);
                  }}
                  disabled={!comment.editText?.trim()}
                  className={`px-3 py-1 text-xs text-white rounded-md ${
                    !comment.editText?.trim() 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  Save
                </button>
              </div>
            </div>
          ) : (
            comment.content
          )}
        </div>
        
        {/* Thread wrapper for reply + nested replies */}
        <div className="relative ml-[14px]">
          {/* Continuous vertical line */}
          <div className="absolute w-[2px] bg-gray-400 left-0 top-0 bottom-0 h-full"></div>

          <div className="pl-[14px]">
            {/* Comment Actions Bar - Reddit Style */}
            <div className="flex items-center mt-2 relative">
              {/* Voting Controls */}
              <div className="flex items-center mr-4">
                <button 
                  onClick={() => handleCommentVote(comment.id, 'UP')} 
                  className={`flex items-center justify-center w-6 h-6 rounded-sm hover:bg-gray-100 ${
                    comment.user_vote === 'upvote' ? 'text-red-500' : 'text-gray-400'
                  } ${voteDisabled ? 'opacity-50 cursor-not-allowed' : ''}`} // Apply disabled style
                  disabled={voteDisabled} // Use voteDisabled state
                  title={!isAuthenticated ? "Log in to vote" : "Upvote"}
                  aria-label="Upvote comment"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 4L4 15h16L12 4z" />
                  </svg>
                </button>
                
                <span className={`font-medium text-xs mx-1 ${
                  comment.user_vote === 'upvote' 
                    ? 'text-red-500' 
                    : comment.user_vote === 'downvote' 
                      ? 'text-blue-500' 
                      : 'text-gray-600'
                }`}>
                  {comment.score ?? 0}
                </span>
                
                <button 
                  onClick={() => handleCommentVote(comment.id, 'DOWN')} 
                  className={`flex items-center justify-center w-6 h-6 rounded-sm hover:bg-gray-100 ${
                    comment.user_vote === 'downvote' ? 'text-blue-500' : 'text-gray-400'
                   } ${voteDisabled ? 'opacity-50 cursor-not-allowed' : ''}`} // Apply disabled style
                  disabled={voteDisabled} // Use voteDisabled state
                  title={!isAuthenticated ? "Log in to vote" : "Downvote"}
                  aria-label="Downvote comment"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 20l8-11H4l8 11z" />
                  </svg>
                </button>
              </div>
              
              {/* Reply Button */}
              {isAuthenticated && (
                <button
                  onClick={() => {
                    setComments(prevComments => 
                      updateCommentInTree(prevComments, comment.id, c => ({
                        ...c, 
                        showReplyForm: !c.showReplyForm
                      }))
                    );
                  }}
                  className={`flex items-center mr-4 text-xs text-gray-500 hover:text-gray-700 ${actionsDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                  disabled={actionsDisabled} // Disable if post locked
                >
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Reply
                </button>
              )}
              
              {/* Share Comment Button */}
              <div className="relative" ref={shareOptionsRef}>
                <button
                  onClick={() => setShowShareOptions(!showShareOptions)}
                  className="flex items-center mr-4 text-xs text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
                  </svg>
                  Share
                </button>
                
                {/* Share Options Menu */}
                {showShareOptions && (
                  <div className="absolute left-0 mt-2 w-36 bg-white rounded-md shadow-lg overflow-hidden z-20">
                    <button 
                      onClick={copyCommentLinkToClipboard}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                        <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
                      </svg>
                      Copy Link
                    </button>
                  </div>
                )}
              </div>
              
              {/* Show/Hide toggle for replies */}
              {hasReplies && ( (!showReplies) || (showReplies && level >= DEFAULT_DISPLAY_LEVEL) ) && (
                <button 
                  onClick={() => setShowReplies(!showReplies)} 
                  className={`text-xs ${!showReplies ? 'text-red-600 font-medium' : 'text-gray-500'} hover:underline`}
                >
                  {!showReplies ? (
                    <>View {totalReplyCount} {totalReplyCount === 1 ? 'reply' : 'replies'}</>
                  ) : (
                    <>Hide replies</>
                  )}
                </button>
              )}
            </div>

            {/* Deep-level comments view */}
            {hasReplies && level >= DEFAULT_DISPLAY_LEVEL && !showReplies && (
              <div className="mt-3 ml-2 pl-2">
                <button 
                  onClick={() => setShowReplies(true)} 
                  className="text-xs text-red-600 font-medium hover:underline flex items-center"
                >
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  Load {totalReplyCount} more {totalReplyCount === 1 ? 'reply' : 'replies'}
                </button>
              </div>
            )}

            {/* Reply form */}
            {comment.showReplyForm && (
              <div className="mt-3">
                <form onSubmit={(e) => {
                  e.preventDefault();
                  if (!comment.replyText?.trim()) return;
                  
                  const handleReply = async () => {
                    try {
                      setComments(prevComments => 
                        updateCommentInTree(prevComments, comment.id, c => ({
                          ...c, 
                          isSubmittingReply: true
                        }))
                      );
                      
                      const reply = await createComment({
                        content: comment.replyText,
                        post: post.id,
                        parent: comment.id
                      });
                      
                      // Add the reply to the parent comment's replies and ensure replies are shown
                      setComments(prevComments => 
                        updateCommentInTree(prevComments, comment.id, c => ({
                          ...c, 
                          showReplyForm: false,
                          replyText: '',
                          isSubmittingReply: false,
                          replies: [reply, ...(c.replies || [])]
                        }))
                      );
                      
                      // Ensure replies are shown after posting a new one
                      setShowReplies(true);
                      
                    } catch (err) {
                      console.error('Error posting reply:', err);
                      setComments(prevComments => 
                        updateCommentInTree(prevComments, comment.id, c => ({
                          ...c,
                          replyError: err.message,
                          isSubmittingReply: false
                        }))
                      );
                    }
                  };
                  
                  handleReply();
                }}>
                  {comment.replyError && (
                    <div className="mb-2 text-xs text-red-600">
                      {comment.replyError}
                    </div>
                  )}
                  
                  <textarea
                    value={comment.replyText || ''}
                    onChange={(e) => {
                      setComments(prevComments => 
                        updateCommentInTree(prevComments, comment.id, c => ({
                          ...c, 
                          replyText: e.target.value
                        }))
                      );
                    }}
                    rows={3}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                    placeholder="Write your reply..."
                    disabled={comment.isSubmittingReply}
                  />
                  
                  <div className="flex justify-end mt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setComments(prevComments => 
                          updateCommentInTree(prevComments, comment.id, c => ({
                            ...c, 
                            showReplyForm: false, 
                            replyText: '', 
                            replyError: null
                          }))
                        );
                      }}
                      className="mr-2 px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
                    >
                      Cancel
                    </button>
                    
                    <button
                      type="submit"
                      disabled={!comment.replyText?.trim() || comment.isSubmittingReply}
                      className={`px-3 py-1 text-xs text-white rounded-md ${
                        !comment.replyText?.trim() 
                          ? 'bg-gray-400 cursor-not-allowed' 
                          : 'bg-red-600 hover:bg-red-700'
                      }`}
                    >
                      {comment.isSubmittingReply ? 'Posting...' : 'Reply'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Nested replies */}
            {hasReplies && showReplies && (
              <div className="mt-2">
                {comment.replies.map(reply => (
                  <CommentItem
                    key={reply.id}
                    comment={reply}
                    post={post}
                    handleDeleteComment={handleDeleteComment}
                    handleEditComment={handleEditComment}
                    handleCommentVote={handleCommentVote}
                    isAuthenticated={isAuthenticated}
                    user={user}
                    setComments={setComments}
                    createComment={createComment}
                    level={level + 1}
                    isPostLocked={isPostLocked} // Pass lock status down
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </li>
  );
};

// Helper function to update a comment in the nested tree structure
const updateCommentInTree = (comments, commentId, updateFn) => {
  return comments.map(comment => {
    if (comment.id === commentId) {
      return updateFn(comment);
    }
    
    if (comment.replies && comment.replies.length > 0) {
      return {
        ...comment,
        replies: updateCommentInTree(comment.replies, commentId, updateFn)
      };
    }
    
    return comment;
  });
}; 