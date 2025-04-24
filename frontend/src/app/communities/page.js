'use client';

import React, { useEffect, useState } from 'react';
import { getSubreddits } from '../../lib/api';
import Link from 'next/link';
import Spinner from '../../components/Spinner';
import { useAuth } from '../../lib/auth';

export default function CommunityListPage() {
  const [communities, setCommunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    async function fetchCommunities() {
      try {
        setLoading(true);
        const data = await getSubreddits();
        setCommunities(data);
      } catch (err) {
        console.error('Failed to fetch communities:', err);
        setError('Failed to load communities. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchCommunities();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative my-4" role="alert">
        <span className="block sm:inline">{error}</span>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Communities</h1>
        {user && (
          <Link 
            href="/communities/create" 
            className="bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded"
          >
            Create Community
          </Link>
        )}
      </div>

      {communities.length === 0 ? (
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
          No communities found. Be the first to create one!
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {communities.map(community => (
            <Link 
              key={community.id} 
              href={`/r/${community.name}`}
              className="block"
            >
              <div className="border rounded-lg overflow-hidden hover:shadow-md transition-shadow duration-200">
                <div className="bg-indigo-100 h-20 flex items-center justify-center">
                  <span className="text-2xl font-bold text-indigo-800">r/{community.name}</span>
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-2">r/{community.name}</h3>
                  <p className="text-gray-600 text-sm mb-2">
                    {community.description || 'No description available'}
                  </p>
                  <div className="flex justify-between text-sm text-gray-500">
                    <span>{community.subscribers || 0} members</span>
                    <span>{community.postCount || 0} posts</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
} 