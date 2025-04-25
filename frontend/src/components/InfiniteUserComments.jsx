import React, { useRef, useCallback } from 'react';
import { useInfiniteUserComments } from '@/hooks/useInfiniteScroll';
import Spinner from './Spinner';

/**
 * Component for displaying a user's comments with infinite scrolling
 * @param {Object} props - Component props
 * @param {string} props.username - Username of the user whose comments to display
 * @param {Object} props.initialParams - Initial parameters for filtering and sorting
 * @param {React.Component} props.commentComponent - Component to render each comment
 * @param {string} props.emptyMessage - Message to display when no comments are found
 */
export default function InfiniteUserComments({ 
  username, 
  initialParams = {},
  commentComponent: CommentComponent,
  emptyMessage = "No comments found." 
}) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
    error
  } = useInfiniteUserComments(username, initialParams);

  const observer = useRef();
  
  // Set up the intersection observer on the last comment
  const lastCommentRef = useCallback(node => {
    if (isFetchingNextPage) return;
    
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      // Log the state before deciding to fetch
      console.log(`[IntersectionObserver] Entry intersecting: ${entries[0].isIntersecting}, hasNextPage: ${hasNextPage}`);
      
      if (entries[0].isIntersecting && hasNextPage) {
        console.log("[IntersectionObserver] Conditions met. Calling fetchNextPage().");
        fetchNextPage();
      } else if (entries[0].isIntersecting && !hasNextPage) {
        console.log("[IntersectionObserver] Intersecting but hasNextPage is false. Not fetching.");
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
            <CommentComponent comment={comment} />
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