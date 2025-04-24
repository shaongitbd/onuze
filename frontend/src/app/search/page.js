'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { searchContent } from '@/lib/api';
import Spinner from '@/components/Spinner';
import Pagination from '@/components/Pagination';
import { formatDistanceToNow } from 'date-fns';

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryParam = searchParams.get('q') || '';
  const typeParam = searchParams.get('type') || 'all';

  const [searchQuery, setSearchQuery] = useState(queryParam);
  const [searchType, setSearchType] = useState(typeParam);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);

  useEffect(() => {
    // Update form state when URL params change
    setSearchQuery(queryParam);
    setSearchType(typeParam);
    
    // Search when URL params change
    if (queryParam) {
      handleSearch(queryParam, typeParam, 1);
    }
  }, [queryParam, typeParam]);

  const handleSearch = async (query, type, pageNumber) => {
    if (!query) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const data = await searchContent(
        query, 
        type === 'all' ? null : type, 
        { page: pageNumber, limit: 10 }
      );
      
      if (data.results) {
        setResults(data.results);
        setTotalResults(data.count || 0);
        setTotalPages(Math.ceil((data.count || 0) / 10));
      } else {
        // Handle potential non-paginated response
        setResults(data || []);
        setTotalResults(data.length || 0);
        setTotalPages(1);
      }
      
      setPage(pageNumber);
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to perform search. Please try again.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Update URL with search params
    const params = new URLSearchParams();
    params.set('q', searchQuery);
    if (searchType !== 'all') params.set('type', searchType);
    
    router.push(`/search?${params.toString()}`);
  };

  const handlePageChange = (newPage) => {
    handleSearch(searchQuery, searchType, newPage);
    // Optional: Update URL with page number
    const params = new URLSearchParams(searchParams);
    params.set('page', newPage);
    router.push(`/search?${params.toString()}`, { scroll: false });
  };

  // Render a search result based on its type
  const renderSearchResult = (result) => {
    switch (result.type) {
      case 'post':
        return renderPostResult(result);
      case 'comment':
        return renderCommentResult(result);
      case 'community':
        return renderCommunityResult(result);
      case 'user':
        return renderUserResult(result);
      default:
        return null;
    }
  };

  const renderPostResult = (post) => (
    <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <div className="text-xs text-gray-500 mb-1">
        <Link href={`/r/${post.community?.name}`} className="hover:underline font-medium">
          r/{post.community?.name}
        </Link>
        <span className="mx-1">•</span>
        Posted by{' '}
        <Link href={`/user/${post.author?.username}`} className="hover:underline">
          u/{post.author?.username}
        </Link>
        {post.created_at && (
          <>
            <span className="mx-1">•</span>
            {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
          </>
        )}
      </div>
      
      <Link href={`/posts/${post.id}`} className="block group">
        <h2 className="text-lg font-semibold group-hover:text-indigo-600 mb-1">
          {post.title}
        </h2>
      </Link>
      
      <p className="text-gray-700 text-sm line-clamp-2 mb-2">
        {post.content}
      </p>
      
      <div className="flex text-xs text-gray-500">
        <span className="mr-3">{post.vote_score || 0} votes</span>
        <span>{post.comment_count || 0} comments</span>
      </div>
    </div>
  );

  const renderCommentResult = (comment) => (
    <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <div className="text-xs text-gray-500 mb-1">
        <span>Comment on post: </span>
        <Link href={`/posts/${comment.post?.id}`} className="hover:underline font-medium">
          {comment.post?.title || 'Unknown post'}
        </Link>
        <span className="mx-1">•</span>
        <span>by </span>
        <Link href={`/user/${comment.author?.username}`} className="hover:underline">
          u/{comment.author?.username}
        </Link>
        {comment.created_at && (
          <>
            <span className="mx-1">•</span>
            {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
          </>
        )}
      </div>
      
      <p className="text-gray-700 text-sm mb-2 pl-2 border-l-2 border-gray-300">
        {comment.content}
      </p>
      
      <Link 
        href={`/posts/${comment.post?.id}#comment-${comment.id}`}
        className="text-xs text-indigo-600 hover:underline"
      >
        Go to comment
      </Link>
    </div>
  );

  const renderCommunityResult = (community) => (
    <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <Link href={`/r/${community.name}`} className="block group">
        <h2 className="text-lg font-semibold group-hover:text-indigo-600 mb-1">
          r/{community.name}
        </h2>
      </Link>
      
      <p className="text-gray-700 text-sm mb-2">
        {community.description || 'No description available'}
      </p>
      
      <div className="flex text-xs text-gray-500">
        <span className="mr-3">{community.subscribers || 0} members</span>
        <span>{community.post_count || 0} posts</span>
      </div>
    </div>
  );

  const renderUserResult = (user) => (
    <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <Link href={`/user/${user.username}`} className="block group">
        <h2 className="text-lg font-semibold group-hover:text-indigo-600 mb-1">
          u/{user.username}
        </h2>
      </Link>
      
      {user.bio && (
        <p className="text-gray-700 text-sm mb-2">
          {user.bio}
        </p>
      )}
      
      <div className="flex text-xs text-gray-500">
        <span className="mr-3">{user.post_count || 0} posts</span>
        <span>{user.karma || 0} karma</span>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Search</h1>
      
      {/* Search Form */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search posts, communities, comments, users..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>
          
          <div className="sm:w-40">
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All</option>
              <option value="post">Posts</option>
              <option value="comment">Comments</option>
              <option value="community">Communities</option>
              <option value="user">Users</option>
            </select>
          </div>
          
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            disabled={loading || !searchQuery.trim()}
          >
            {loading ? <Spinner /> : 'Search'}
          </button>
        </div>
      </form>
      
      {/* Search Results */}
      {queryParam && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">
              {loading ? 'Searching...' : `Results for "${queryParam}"`}
            </h2>
            
            {!loading && totalResults > 0 && (
              <p className="text-sm text-gray-500">
                Found {totalResults} {totalResults === 1 ? 'result' : 'results'}
              </p>
            )}
          </div>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-md mb-4">
              {error}
            </div>
          )}
          
          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : results.length === 0 ? (
            <div className="bg-gray-50 p-6 rounded-md text-center">
              <p className="text-gray-500">No results found for "{queryParam}"</p>
              <p className="text-sm text-gray-400 mt-2">
                Try different keywords or search for another term
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((result) => (
                <div key={`${result.type}-${result.id}`}>
                  {renderSearchResult(result)}
                </div>
              ))}
              
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={handlePageChange}
                loading={loading}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
} 