import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { UpvoteIcon, DownvoteIcon, ReplyIcon, EditIcon, DeleteIcon, BanIcon, UnbanIcon } from './Icons';
import { useAuth } from '../lib/auth';
import { voteComment, deleteComment, banUser, unbanUser, checkBanStatus } from '../lib/api';
import CommentForm from './CommentForm';
import BanUserModal from './BanUserModal'; // Import the BanUserModal

function CommentItem({ comment, onCommentDeleted, communityPath, isModerator, onReplySuccess, onVote }) {
  const { user, isAuthenticated } = useAuth();
  const [voteStatus, setVoteStatus] = useState(comment.user_vote || 0);
  const [score, setScore] = useState(comment.score || 0);
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editText, setEditText] = useState(comment.content);
  const [isUserBanned, setIsUserBanned] = useState(false);
  const [banStatusLoading, setBanStatusLoading] = useState(false);
  const [showOptions, setShowOptions] = useState(false); 
  const optionsRef = useRef(null);
  // Ban modal state
  const [showBanModal, setShowBanModal] = useState(false);
  const [banTargetUser, setBanTargetUser] = useState(null);
  const [banLoading, setBanLoading] = useState(false);

  // Close options menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (optionsRef.current && !optionsRef.current.contains(event.target)) {
        setShowOptions(false);
      }
    }

    // Add event listener
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      // Remove event listener on cleanup
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Check ban status when component mounts
  useEffect(() => {
    if (isModerator && comment?.user?.username && communityPath) {
      checkBanStatusForUser();
    }
  }, [isModerator, comment?.user?.username, communityPath]);
  
  const checkBanStatusForUser = async () => {
    if (!isModerator || !comment?.user?.username || !communityPath) return;
    
    try {
      setBanStatusLoading(true);
      const banStatus = await checkBanStatus(communityPath, comment.user.username);
      setIsUserBanned(banStatus.is_banned);
    } catch (err) {
      console.error('Error checking comment author ban status:', err);
    } finally {
      setBanStatusLoading(false);
    }
  };

  const handleVote = async (direction) => {
    if (!isAuthenticated) {
      alert('You need to login to vote.');
      return;
    }

    // Optimistic UI update
    const previousVote = voteStatus;
    let scoreChange = 0;

    if (direction === previousVote) {
      // Canceling vote
      setVoteStatus(0);
      scoreChange = -direction;
    } else {
      // New vote or changing vote
      setVoteStatus(direction);
      scoreChange = direction - previousVote;
    }

    setScore(prevScore => prevScore + scoreChange);

    try {
      await voteComment(comment.id, direction);
      if (onVote) onVote(comment.id, direction);
    } catch (error) {
      // Revert on error
      setVoteStatus(previousVote);
      setScore(prevScore => prevScore - scoreChange);
      console.error('Error voting:', error);
      alert(`Failed to vote: ${error.message}`);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this comment?')) {
      try {
        await deleteComment(comment.id);
        onCommentDeleted(comment.id);
      } catch (error) {
        console.error('Error deleting comment:', error);
        alert(`Failed to delete comment: ${error.message}`);
      }
    }
  };

  const handleSubmitEdit = async (e) => {
    e.preventDefault();
    try {
      await onCommentDeleted(comment.id, editText);
      setShowEditForm(false);
    } catch (error) {
      console.error('Error updating comment:', error);
      alert(`Failed to update comment: ${error.message}`);
    }
  };

  const handleReply = async (text) => {
    try {
      await onReplySuccess(comment.id, text);
      setShowReplyForm(false);
    } catch (error) {
      console.error('Error replying to comment:', error);
      alert(`Failed to reply: ${error.message}`);
    }
  };

  // Handle banning a user - opens the modal
  const handleBanUser = async () => {
    if (!isModerator || !comment?.user?.username || banStatusLoading) {
      return;
    }
    setBanTargetUser(comment.user.username);
    setShowBanModal(true);
    setShowOptions(false); // Close the options menu
  };

  // Function to be called by the modal on confirmation
  const confirmBanUser = async (reason, durationDays) => {
    try {
      if (!banTargetUser || !communityPath) {
        console.error('Missing username or community path');
        return;
      }
      setBanLoading(true);
      await banUser(communityPath, banTargetUser, { reason, duration_days: durationDays });
      setIsUserBanned(true);
      alert(`User u/${banTargetUser} has been banned from c/${communityPath}.`);
      setShowBanModal(false);
      setBanTargetUser(null);
    } catch (error) {
      console.error('Error banning user:', error);
      alert(`Failed to ban user: ${error.message || 'Unknown error'}`);
    } finally {
      setBanLoading(false);
    }
  };

  const handleUnbanUser = async () => {
    try {
      if (!isModerator || !comment?.user?.username || !communityPath) {
        console.error('Missing username or community path');
        return;
      }
      
      setBanStatusLoading(true);
      await unbanUser(communityPath, comment.user.username);
      setIsUserBanned(false);
      setShowOptions(false);
      alert(`User ${comment.user.username} has been unbanned from ${communityPath}`);
    } catch (error) {
      console.error('Error unbanning user:', error);
      alert(`Failed to unban user: ${error.message}`);
    } finally {
      setBanStatusLoading(false);
    }
  };

  return (
    <div className="border-b border-gray-200 py-4 flex">
      {/* Vote buttons */}
      <div className="flex flex-col items-center mr-4">
        <button
          onClick={() => handleVote(1)}
          disabled={!isAuthenticated}
          className={`p-1 ${voteStatus === 1 ? 'text-orange-500' : 'text-gray-400 hover:text-gray-600'}`}
        >
          <UpvoteIcon size={5} />
        </button>
        <span className={`text-xs font-semibold py-1 ${
          voteStatus === 1 ? 'text-orange-500' : voteStatus === -1 ? 'text-blue-500' : 'text-gray-600'
        }`}>
          {score}
        </span>
        <button
          onClick={() => handleVote(-1)}
          disabled={!isAuthenticated}
          className={`p-1 ${voteStatus === -1 ? 'text-blue-500' : 'text-gray-400 hover:text-gray-600'}`}
        >
          <DownvoteIcon size={5} />
        </button>
      </div>

      {/* Comment content */}
      <div className="flex-1">
        {/* Comment header */}
        <div className="flex items-center mb-1">
          <Link 
            href={`/user/${comment.user?.username || 'deleted-user'}`} 
            className="text-xs font-medium text-gray-900 hover:underline"
            passHref
          >
            u/{comment.user?.username || '[deleted]'}
          </Link>
          {isUserBanned && (
            <span className="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded-md">
              Banned
            </span>
          )}
          <span className="text-xs text-gray-500 ml-2">
            {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
          </span>
        </div>

        {/* Comment body */}
        {showEditForm ? (
          <form onSubmit={handleSubmitEdit} className="mt-2">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
              rows="3"
            />
            <div className="flex justify-end mt-2">
              <button
                type="button"
                onClick={() => setShowEditForm(false)}
                className="mr-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Save
              </button>
            </div>
          </form>
        ) : (
          <div className="text-sm text-gray-800">{comment.content}</div>
        )}

        {/* Comment actions */}
        <div className="mt-2 flex items-center space-x-4">
          <button
            onClick={() => setShowReplyForm(!showReplyForm)}
            className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
            disabled={!isAuthenticated}
          >
            <ReplyIcon size={4} className="mr-1" />
            Reply
          </button>

          {isAuthenticated && user?.id === comment.user?.id && (
            <>
              <button
                onClick={() => {
                  setShowEditForm(!showEditForm);
                  setEditText(comment.content);
                }}
                className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
              >
                <EditIcon size={4} className="mr-1" />
                Edit
              </button>
              <button
                onClick={handleDelete}
                className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
              >
                <DeleteIcon size={4} className="mr-1" />
                Delete
              </button>
            </>
          )}

          {/* Moderator actions */}
          {isModerator && isAuthenticated && user?.id !== comment.user?.id && (
            <div className="relative" ref={optionsRef}>
              <button
                onClick={() => setShowOptions(!showOptions)}
                className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                </svg>
                Mod
              </button>
              
              {showOptions && (
                <div className="absolute left-0 mt-2 w-40 bg-white rounded-md shadow-lg overflow-hidden z-20 border border-gray-200">
                  {isUserBanned ? (
                    <button 
                      onClick={handleUnbanUser}
                      disabled={banStatusLoading}
                      className="flex items-center w-full px-4 py-2 text-sm text-green-600 hover:bg-gray-100"
                    >
                      <UnbanIcon size={4} className="mr-2" />
                      Unban User
                    </button>
                  ) : (
                    <button 
                      onClick={handleBanUser}
                      disabled={banStatusLoading}
                      className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                    >
                      <BanIcon size={4} className="mr-2" />
                      Ban User
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Reply form */}
        {showReplyForm && (
          <div className="mt-3">
            <CommentForm
              onSubmit={handleReply}
              initialValue=""
              buttonText="Reply"
              placeholder="Write a reply..."
            />
          </div>
        )}
      </div>

      {/* Ban User Modal */}
      <BanUserModal
        isOpen={showBanModal}
        onClose={() => {
          setShowBanModal(false);
          setBanTargetUser(null);
        }}
        onConfirmBan={confirmBanUser}
        username={banTargetUser}
        isLoading={banLoading}
      />
    </div>
  );
}

export default CommentItem;
