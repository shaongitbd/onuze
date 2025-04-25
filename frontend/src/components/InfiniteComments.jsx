import React, { useRef, useCallback } from 'react';
import { useInfiniteComments } from '@/hooks/useInfiniteScroll';
import CommentItem from './CommentItem';
import Spinner from './Spinner';

/**
 * Component for displaying infinite scrolling comments
 * @param {Object} props - Component props
 * @param {string} props.postPath - The path identifier for the post
 * @param {Object} props.initialParams - Initial parameters for the comments query
 * @param {string} props.emptyMessage - Message to display when no comments are available
 */
export default function InfiniteComments({ 
  postPath, 
  initialParams = {}, 
  emptyMessage = "No comments yet. Be the first to comment!"
}) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
    error
  } = useInfiniteComments(postPath, initialParams);

  const observer = useRef();
  
  // Set up the intersection observer on the last comment
  const lastCommentRef = useCallback(node => {
    if (isFetchingNextPage) return;
    
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasNextPage) {
        fetchNextPage();
      }
    });
    
    if (node) observer.current.observe(node);
  }, [isFetchingNextPage, fetchNextPage, hasNextPage]);

  // Render based on query status
  if (status === 'pending') {
    return <div className="flex justify-center p-4"><Spinner size="lg" /></div>;
  }

  if (status === 'error') {
    return <div className="text-center text-red-500 p-4">Error loading comments: {error.message}</div>;
  }

  // Get all comments from all pages
  const allComments = data?.pages.flatMap(page => page.results) || [];

  if (allComments.length === 0) {
    return <div className="text-center text-gray-500 p-4">{emptyMessage}</div>;
  }

  return (
    <div className="space-y-4">
      {allComments.map((comment, index) => {
        // Only add the ref to the last item
        const isLastComment = index === allComments.length - 1;
        
        return (
          <div 
            key={`${comment.id}-${index}`}
            ref={isLastComment ? lastCommentRef : null}
          >
            <CommentItem comment={comment} />
          </div>
        );
      })}
      
      {isFetchingNextPage && (
        <div className="flex justify-center p-2">
          <Spinner />
        </div>
      )}
    </div>
  );
} 