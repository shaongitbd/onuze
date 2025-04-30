'use client';

import { useState, useEffect, useMemo, useContext } from 'react';
import Link from 'next/link';
import InfiniteScroll from 'react-infinite-scroll-component';
import PostCard from '../components/PostCard';
import Spinner from '../components/Spinner';
import { useAuth } from '../lib/auth';
import { useInfinitePosts } from '../hooks/useInfiniteScroll';
import { PostFilterContext } from './layout';

export default function HomePage() {
  const [communities, setCommunities] = useState([]);
  const [communityError, setCommunityError] = useState(null);
  const [communityLoading, setCommunityLoading] = useState(true);
  const { user } = useAuth();
  const { filter } = useContext(PostFilterContext);

  // Add sort parameter based on filter
  const getFilterParams = () => {
    switch(filter) {
      case 'popular':
        return { sort: 'hot' };
      case 'new':
        return { sort: 'new' };
      case 'all':
        return { sort: 'top' };
      default:
        return {}; // Default home feed
    }
  };

  const {
    data: postsData,
    fetchNextPage,
    hasNextPage,
    isLoading: isLoadingPosts,
    isError: isErrorPosts,
    error: postsError,
    isFetchingNextPage,
    refetch
  } = useInfinitePosts(getFilterParams(), {
    refetchOnWindowFocus: false,
  });

  // Refetch when filter changes
  useEffect(() => {
    refetch();
  }, [filter, refetch]);

  useEffect(() => {
    async function fetchCommunities() {
      try {
        setCommunityLoading(true);
        setCommunityError(null);
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
        const communitiesResponse = await fetch(`${API_BASE_URL}/communities/popular/`);
        
        if (communitiesResponse.ok) {
          const communitiesData = await communitiesResponse.json();
          setCommunities(communitiesData.slice(0, 5));
        } else {
          throw new Error('Failed to load communities');
        }
      } catch (err) {
        console.error('Error fetching communities:', err);
        setCommunityError('Failed to load communities.');
      } finally {
        setCommunityLoading(false);
      }
    }

    fetchCommunities();
  }, []);

  const allPosts = useMemo(() => 
    postsData?.pages?.flatMap(page => page.results) ?? []
  , [postsData]);

  if (isLoadingPosts) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="large" />
      </div>
    );
  }

  if (isErrorPosts) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative my-4" role="alert">
        <span className="block sm:inline">Error loading posts: {postsError?.message || 'Please try again later.'}</span>
      </div>
    );
  }

  // Get title based on filter
  const getTitle = () => {
    switch(filter) {
      case 'popular':
        return 'Popular Posts';
      case 'new':
        return 'New Posts';
      case 'all':
        return 'All Posts';
      default:
        return 'Home Feed';
    }
  };

  return (
    <div className="px-0 py-0">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Main content - Posts */}
        <div className="flex-1">
          <div className="flex items-center mb-6 px-4 lg:px-0">
            <svg className="w-6 h-6 text-gray-700 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" />
            </svg>
            <h1 className="text-2xl font-bold text-gray-900">{getTitle()}</h1>
          </div>
          
          {allPosts.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm p-8 text-center mx-4 lg:mx-0">
              <div className="w-24 h-24 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-700 mb-2">No posts yet</h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">Be the first one to share something!</p>
              {user && (
                <Link 
                  href="/submit"
                  className="inline-flex items-center px-6 py-3 bg-gray-800 text-white font-medium rounded-full hover:bg-gray-900 transition-colors duration-200 shadow-md hover:shadow-lg"
                >
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                  Create the first post
                </Link>
              )}
            </div>
          ) : (
            <InfiniteScroll
              dataLength={allPosts.length}
              next={fetchNextPage}
              hasMore={hasNextPage}
              loader={
                <div className="flex justify-center items-center py-4">
                  <Spinner />
                </div>
              }
              endMessage={
                <p style={{ textAlign: 'center' }} className="text-gray-500 text-sm py-4">
                  <b>You've seen all posts</b>
                </p>
              }
            >
              <div className="space-y-4 px-4 lg:px-0">
                {allPosts.map(post => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>
            </InfiniteScroll>
          )}
        </div>
        
        {/* Right sidebar */}
        <div className="w-full lg:w-4/12 lg:block">
          {/* About */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden mb-4">
            <div className="px-4 py-3 bg-red-600 text-white">
              <h2 className="text-base font-bold">About</h2>
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-700 mb-4">
                This is a Reddit-style community platform where you can join communities, create posts, and engage in discussions.
              </p>
              {!user && (
                <div className="space-y-2">
                  <Link 
                    href="/login"
                    className="block w-full bg-red-600 hover:bg-red-700 text-white text-center text-sm py-1.5 px-3 rounded-full transition-colors"
                  >
                    Log In
                  </Link>
                  <Link 
                    href="/register"
                    className="block w-full bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-center text-sm py-1.5 px-3 rounded-full transition-colors"
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>
          
          {/* Popular communities */}
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-700 text-white">
              <h2 className="text-base font-bold flex items-center">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                </svg>
                Popular Communities
              </h2>
            </div>
            
            <div className="p-4">
              {communityLoading ? (
                <div className="flex justify-center items-center py-4">
                   <Spinner size="small" />
                </div>
              ) : communityError ? (
                <p className="text-red-600 text-center py-2 text-sm">{communityError}</p>
              ) : communities.length === 0 ? (
                <p className="text-gray-500 text-center py-2 text-sm">No communities yet.</p>
              ) : (
                <ul className="space-y-2">
                  {communities.map(community => (
                    <li key={community.id}>
                      <Link 
                        href={`/c/${community.path || community.name}`}
                        className="flex items-center py-1 px-2 hover:bg-gray-50 rounded-md transition-colors"
                      >
                       {community.icon_image ? (
                        <img src={community.icon_image} alt={community.name} className="w-8 h-8 rounded-full flex items-center justify-center mr-2 flex-shrink-0 border border-gray-200" />
                       ) : (
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-2 flex-shrink-0 border border-gray-200">
                          <span className="text-gray-600 font-medium text-sm">
                            {community.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                       )}
                        <div className="text-sm">
                          <span className="font-medium text-gray-800 block truncate">c/{community.name}</span>
                          <div className="text-xs text-gray-500">
                            {community.subscribers || 0} members
                          </div>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-3 pt-3 border-t border-gray-100 text-center">
                <Link 
                  href="/communities"
                  className="text-red-500 hover:text-red-600 text-xs font-medium flex items-center justify-center"
                >
                  <span>View All Communities</span>
                  <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
