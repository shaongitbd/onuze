import React, { useRef, useCallback } from 'react';
import { useInfinitePosts } from '@/hooks/useInfiniteScroll';
import PostCard from './PostCard';
import Spinner from './Spinner';

/**
 * Component for displaying infinite scrolling posts
 * @param {Object} props - Component props
 * @param {Object} props.initialParams - Initial parameters for the posts query
 * @param {string} props.emptyMessage - Message to display when no posts are available
 */
export default function InfinitePosts({ 
  initialParams = {}, 
  emptyMessage = "No posts found." 
}) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
    error
  } = useInfinitePosts(initialParams);

  const observer = useRef();
  
  // Set up the intersection observer on the last post
  const lastPostRef = useCallback(node => {
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
    return <div className="flex justify-center p-6"><Spinner size="lg" /></div>;
  }

  if (status === 'error') {
    return <div className="text-center text-red-500 p-4">Error loading posts: {error.message}</div>;
  }

  const posts = data?.pages.flatMap(page => page.results) || [];

  if (posts.length === 0) {
    return <div className="text-center text-gray-500 p-6">{emptyMessage}</div>;
  }

  return (
    <div className="space-y-4">
      {posts.map((post, index) => (
        <div 
          key={post.id} 
          ref={index === posts.length - 1 ? lastPostRef : null}
        >
          <PostCard post={post} />
        </div>
      ))}
      
      {isFetchingNextPage && (
        <div className="flex justify-center p-3">
          <Spinner />
        </div>
      )}
    </div>
  );
} 