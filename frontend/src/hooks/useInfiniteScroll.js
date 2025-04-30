import { useInfiniteQuery } from '@tanstack/react-query';
import { fetchPosts, fetchComments, fetchUserComments, fetchNotifications } from '@/lib/api';

/**
 * Custom hook for fetching infinite posts with pagination using API-provided next URLs
 * @param {Object} initialParams - Initial parameters for the first posts query (e.g., sorting, filters)
 * @param {Object} options - Additional options for the infinite query
 * @returns {Object} The infinite query result object
 */
export function useInfinitePosts(initialParams = {}, options = {}) {
  return useInfiniteQuery({
    // Query key includes initial params to refetch if they change
    queryKey: ['posts', initialParams],
    // pageParam will be the URL for the next page, or undefined for the initial fetch
    queryFn: async ({ pageParam }) => {
      const fetchArg = pageParam || initialParams;
      console.log(`[useInfinitePosts] Fetching page. Argument:`, fetchArg);
      // Pass the URL string directly if pageParam exists, otherwise pass initialParams object
      const response = await fetchPosts(fetchArg);
      return response; 
    },
    // getNextPageParam simply returns the 'next' URL from the last page data
    getNextPageParam: (lastPage) => {
      console.log(`[useInfinitePosts - getNextPageParam] Last page next URL: ${lastPage?.next}`);
      return lastPage?.next || undefined; // Return undefined if no next URL
    },
    // Use undefined to signify the initial fetch uses initialParams
    initialPageParam: undefined,
    ...options,
  });
}

/**
 * Custom hook for fetching infinite comments with pagination using API-provided next URLs
 * @param {string} postPath - Path of the post to fetch comments for
 * @param {Object} initialParams - Initial parameters for the first comments query
 * @param {Object} options - Additional options for the infinite query
 * @returns {Object} The infinite query result object
 */
export function useInfiniteComments(postPath, initialParams = {}, options = {}) {
  return useInfiniteQuery({
    queryKey: ['comments', postPath, initialParams],
    queryFn: async ({ pageParam }) => {
      const fetchArg = pageParam || initialParams;
      console.log(`[useInfiniteComments] Fetching page. Argument:`, fetchArg);
      // Pass the URL string directly if pageParam exists, otherwise pass initialParams object
      // The fetchComments function needs postPath only for the initial fetch (handled inside api.js)
      const response = await fetchComments(postPath, fetchArg);
      return response;
    },
    getNextPageParam: (lastPage) => {
      console.log(`[useInfiniteComments - getNextPageParam] Last page next URL: ${lastPage?.next}`);
      return lastPage?.next || undefined;
    },
    initialPageParam: undefined,
    ...options,
  });
}

/**
 * Custom hook for fetching infinite user comments with pagination using API-provided next URLs
 * @param {string} username - Username to fetch comments for
 * @param {Object} initialParams - Initial parameters for the first comments query
 * @param {Object} options - Additional options for the infinite query
 * @returns {Object} The infinite query result object
 */
export function useInfiniteUserComments(username, initialParams = {}, options = {}) {
  return useInfiniteQuery({
    queryKey: ['user-comments', username, initialParams],
    queryFn: async ({ pageParam }) => {
      // For the initial fetch, ensure username is in the params object
      const fetchArg = pageParam || { ...initialParams, username };
      console.log(`[useInfiniteUserComments] Fetching page. Argument:`, fetchArg);
      // Pass the URL string directly if pageParam exists, otherwise pass the params object
      const response = await fetchUserComments(fetchArg);
      return response;
    },
    getNextPageParam: (lastPage) => {
      console.log(`[useInfiniteUserComments - getNextPageParam] Last page next URL: ${lastPage?.next}`);
      return lastPage?.next || undefined;
    },
    initialPageParam: undefined,
    ...options,
  });
}

/**
 * Custom hook for fetching infinite notifications with pagination using API-provided next URLs
 * @param {Object} initialParams - Initial parameters for the first notifications query (e.g., is_read filter)
 * @param {Object} options - Additional options for the infinite query
 * @returns {Object} The infinite query result object
 */
export function useInfiniteNotifications(initialParams = {}, options = {}) {
  return useInfiniteQuery({
    queryKey: ['notifications', initialParams],
    queryFn: async ({ pageParam }) => {
      const fetchArg = pageParam || initialParams;
      console.log(`[useInfiniteNotifications] Fetching page. Argument:`, fetchArg);
      // Pass the URL string directly if pageParam exists, otherwise pass params object
      const response = await fetchNotifications(fetchArg);
      return response;
    },
    getNextPageParam: (lastPage) => {
      console.log(`[useInfiniteNotifications - getNextPageParam] Last page next URL: ${lastPage?.next}`);
      return lastPage?.next || undefined;
    },
    initialPageParam: undefined,
    ...options,
  });
} 