'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  getPostByPath, getComments, createComment, deletePost, deleteComment, 
  upvotePost, downvotePost, upvoteComment, downvoteComment, updateComment 
} from '../../../../../lib/api';
import { useAuth } from '../../../../../lib/auth';
import Spinner from '../../../../../components/Spinner';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

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

  // Fetch post and comments
  React.useEffect(() => {
    async function fetchPostAndComments() {
      try {
        setLoading(true);
        const postData = await getPostByPath(postPath);
        setPost(postData);
        
        if (postData && postData.id) {
          const commentsData = await getComments(postData.id);
          if (commentsData && Array.isArray(commentsData.results)) {
            setComments(commentsData.results);
          } else {
            console.warn("Comments data received in unexpected format:", commentsData);
            setComments([]);
          }
        } else {
          console.warn("Post data did not contain an ID, cannot fetch comments.");
          setComments([]);
        }
      } catch (err) {
        console.error('Error fetching post details:', err);
        setError('Post not found or you do not have access.');
      } finally {
        setLoading(false);
      }
    }

    if (postPath) {
      fetchPostAndComments();
    }
  }, [postPath]);

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

    if (!post || !post.id) {
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
      await action(post.id);
      
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

  // Handle deleting the post
  const handleDeletePost = async () => {
    if (!isAuthenticated || !user || !post || post?.user?.id !== user.id) {
      alert('You are not authorized to delete this post.');
      return;
    }

    if (window.confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
      try {
        setLoading(true); // Show loading indicator
        await deletePost(post.path);
        alert('Post deleted successfully.');
        // Redirect to the community page after deletion
        router.push(`/c/${communityName}`); 
      } catch (err) {
        console.error('Error deleting post:', err);
        setError(err.message || 'Failed to delete post.');
        setLoading(false); // Hide loading on error
      }
      // No finally setLoading(false) here, because we navigate away on success
    }
  };
  
  // Handle deleting a comment
  const handleDeleteComment = async (commentId) => {
      // Find the comment to check ownership
    const commentToDelete = comments.find(c => c.id === commentId);
    if (!isAuthenticated || !user || commentToDelete?.user?.id !== user.id) {
      alert('You are not authorized to delete this comment.');
      return;
    }

    if (window.confirm('Are you sure you want to delete this comment?')) {
      try {
        await deleteComment(commentId);
        // Remove the comment from the local state
        setComments(prevComments => prevComments.filter(comment => comment.id !== commentId));
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
      
      // Optimistic UI update for comments
      setComments(prevComments => 
        prevComments.map(comment => {
          if (comment.id === commentId) {
            const voteValue = voteDirection === 'UP' ? 1 : -1;
            const currentVote = comment.user_vote; // Assuming comments also have user_vote
            let scoreChange = 0;

            if (voteValue === 1) { // Upvoting
                scoreChange = currentVote === 'upvote' ? -1 : (currentVote === 'downvote' ? 2 : 1);
            } else { // Downvoting (-1)
                scoreChange = currentVote === 'downvote' ? 1 : (currentVote === 'upvote' ? -2 : -1);
            }
            
            return {
              ...comment,
              score: (comment.score ?? 0) + scoreChange,
              user_vote: voteValue === 1 ? (currentVote === 'upvote' ? null : 'upvote') : (currentVote === 'downvote' ? null : 'downvote')
            };
          }
          return comment;
        })
      );
    } catch (err) {
      console.error(`Error ${voteDirection === 'UP' ? 'upvoting' : 'downvoting'} comment ${commentId}:`, err);
    }
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

  if (loading || isLoading) {
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

  const canEdit = isAuthenticated && user && post?.user?.id === user.id;
  const editUrl = `/c/${communityName}/post/${postPath}/edit`;

  return (
    <div className="p-4 max-w-3xl mx-auto">
      {/* Post */}
      <div className="bg-white rounded-md shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center mb-4">
          <Link href={`/c/${communityName}`} className="font-medium text-gray-800 hover:underline">
            c/{communityName}
          </Link>
          <span className="mx-2 text-gray-500">•</span>
          <span className="text-sm text-gray-500">
            Posted by u/{post?.user?.username} {formatDistanceToNow(new Date(post?.created_at || Date.now()), { addSuffix: true })}
          </span>
        </div>
        
        <h1 className="text-2xl font-bold mb-4">{post.title}</h1>
        
        {post.content && (
          <div className="mb-6 text-gray-800 whitespace-pre-wrap">{post.content}</div>
        )}
        
        <div className="flex items-center text-gray-600 mt-4">
          <button 
            onClick={() => handleVote('UP')}
            className={`flex items-center mr-4 hover:text-red-600 disabled:opacity-50 ${
              post.user_vote === 'upvote' ? 'text-red-500' : ''
            }`}
            disabled={!isAuthenticated}
            title={!isAuthenticated ? "Log in to vote" : "Upvote"}
          >
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"></path>
            </svg>
            Upvote
          </button>
          
          <span className="mx-2 font-medium">{post?.score ?? 0}</span>
          
          <button 
            onClick={() => handleVote('DOWN')}
            className={`flex items-center ml-4 hover:text-blue-600 disabled:opacity-50 ${
              post.user_vote === 'downvote' ? 'text-blue-500' : ''
            }`}
            disabled={!isAuthenticated}
            title={!isAuthenticated ? "Log in to vote" : "Downvote"}
          >
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
            </svg>
            Downvote
          </button>
          
          <div className="flex-grow"></div>

          {canEdit && (
            <div className="flex items-center space-x-2 ml-4">
              <Link href={editUrl} className="text-gray-500 hover:text-red-600 text-sm">
                Edit
              </Link>
              <button 
                onClick={handleDeletePost}
                className="text-red-500 hover:text-red-700 text-sm"
                disabled={loading}
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Comment form */}
      <div className="bg-white rounded-md shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Add a comment</h2>
        
        {!user && (
          <p className="mb-4 text-gray-600">
            <Link href={`/login?redirect=${encodeURIComponent(`/c/${communityName}/post/${postPath}`)}`} className="text-red-600 hover:underline">
              Sign in
            </Link> to leave a comment
          </p>
        )}
        
        <form onSubmit={handleCommentSubmit}>
          {commentError && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
              {commentError}
            </div>
          )}
          
          <div className="mb-4">
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              placeholder="What are your thoughts?"
              disabled={!user || submittingComment}
            />
          </div>
          
          <button
            type="submit"
            disabled={!user || submittingComment}
            className={`px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition ${(!user || submittingComment) ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {submittingComment ? 'Posting...' : 'Comment'}
          </button>
        </form>
      </div>
      
      {/* Comments */}
      <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-4">
            Comments ({comments.length})
          </h2>
          
          {comments.length === 0 ? (
            <p className="text-gray-500">No comments yet. Be the first to comment!</p>
          ) : (
            <ul className="space-y-6">
              {comments.map(comment => (
                <li key={comment.id} className="border-b border-gray-100 pb-6 last:border-0 last:pb-0">
                  <div className="flex items-center mb-2">
                    <span className="font-medium">{comment?.user?.username ?? '[deleted]'}</span>
                    <span className="mx-2 text-gray-400">•</span>
                    <span className="text-sm text-gray-500">
                      {formatDistanceToNow(new Date(comment?.created_at || Date.now()), { addSuffix: true })}
                    </span>
                    <div className="flex-grow"></div>
                    
                    {/* Comment Actions */}
                    <div className="flex items-center mt-2 text-sm">
                      {/* Comment Voting Buttons */} 
                      <div className="flex items-center space-x-1 mr-4">
                        <button 
                          onClick={() => handleCommentVote(comment.id, 'UP')} 
                          className={`p-1 rounded hover:bg-gray-100 disabled:opacity-50 ${comment.user_vote === 'upvote' ? 'text-red-500' : 'text-gray-500'}`} 
                          disabled={!isAuthenticated}
                          title={!isAuthenticated ? "Log in to vote" : "Upvote"}
                          aria-label="Upvote comment"
                        >
                          ▲
                        </button>
                        <span className="font-medium text-xs">{comment.score ?? 0}</span>
                        <button 
                          onClick={() => handleCommentVote(comment.id, 'DOWN')} 
                          className={`p-1 rounded hover:bg-gray-100 disabled:opacity-50 ${comment.user_vote === 'downvote' ? 'text-blue-500' : 'text-gray-500'}`} 
                          disabled={!isAuthenticated}
                          title={!isAuthenticated ? "Log in to vote" : "Downvote"}
                          aria-label="Downvote comment"
                        >
                          ▼
                        </button>
                      </div>
                      
                      {/* Edit/Delete Buttons */}
                      {isAuthenticated && user && comment?.user?.id === user.id && (
                        <div className="flex items-center space-x-2 ml-auto">
                          <button 
                            onClick={() => {
                              // Toggle edit mode for this comment
                              setComments(prevComments => 
                                prevComments.map(c => 
                                  c.id === comment.id 
                                    ? {...c, isEditing: true, editText: c.content} 
                                    : c
                                )
                              );
                            }} 
                            className="text-gray-500 hover:text-red-600 text-xs"
                          >
                            Edit
                          </button>
                          <button 
                            onClick={() => handleDeleteComment(comment.id)} 
                            className="text-gray-500 hover:text-red-600 text-xs"
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="mt-1 text-gray-700 whitespace-pre-wrap">
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
                              prevComments.map(c => 
                                c.id === comment.id 
                                  ? {...c, editText: e.target.value} 
                                  : c
                              )
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
                                prevComments.map(c => 
                                  c.id === comment.id 
                                    ? {...c, isEditing: false, editText: null, editError: null} 
                                    : c
                                )
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
                  
                  {/* Reply Button and Form */}
                  <div className="mt-2">
                    {isAuthenticated && (
                      <button 
                        onClick={() => {
                          // Toggle reply form for this comment
                          setComments(prevComments => 
                            prevComments.map(c => 
                              c.id === comment.id 
                                ? {...c, showReplyForm: !c.showReplyForm} 
                                : c
                            )
                          );
                        }}
                        className="text-xs text-gray-500 hover:text-red-500"
                      >
                        Reply
                      </button>
                    )}
                    
                    {comment.showReplyForm && (
                      <div className="mt-3 ml-6 p-3 bg-gray-50 rounded-md">
                        <form 
                          onSubmit={(e) => {
                            e.preventDefault();
                            if (!comment.replyText?.trim()) return;
                            
                            const handleReply = async () => {
                              try {
                                setComments(prevComments => 
                                  prevComments.map(c => 
                                    c.id === comment.id 
                                      ? {...c, isSubmittingReply: true} 
                                      : c
                                  )
                                );
                                
                                const reply = await createComment({
                                  content: comment.replyText,
                                  post: post.id,
                                  parent: comment.id
                                });
                                
                                // Update UI with new reply
                                setComments(prevComments => {
                                  const updatedComments = prevComments.map(c => {
                                    if (c.id === comment.id) {
                                      // Add the reply to this comment's replies
                                      return {
                                        ...c, 
                                        showReplyForm: false,
                                        replyText: '',
                                        isSubmittingReply: false
                                      };
                                    }
                                    return c;
                                  });
                                  
                                  // Add the new reply to the main comments list
                                  return [reply, ...updatedComments];
                                });
                                
                              } catch (err) {
                                console.error('Error posting reply:', err);
                                setComments(prevComments => 
                                  prevComments.map(c => 
                                    c.id === comment.id 
                                      ? {...c, replyError: err.message, isSubmittingReply: false} 
                                      : c
                                  )
                                );
                              }
                            };
                            
                            handleReply();
                          }}
                        >
                          {comment.replyError && (
                            <div className="mb-2 text-xs text-red-600">
                              {comment.replyError}
                            </div>
                          )}
                          
                          <textarea
                            value={comment.replyText || ''}
                            onChange={(e) => {
                              setComments(prevComments => 
                                prevComments.map(c => 
                                  c.id === comment.id 
                                    ? {...c, replyText: e.target.value} 
                                    : c
                                )
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
                                  prevComments.map(c => 
                                    c.id === comment.id 
                                      ? {...c, showReplyForm: false, replyText: '', replyError: null} 
                                      : c
                                  )
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
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
} 