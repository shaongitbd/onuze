import React from 'react';
import { getSubreddits } from '../../lib/api';
import Link from 'next/link';
import Spinner from '../../components/Spinner';
import { useAuth } from '../../lib/auth';

export default function CommunitiesPage() {
  const [communities, setCommunities] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const { user } = useAuth();

  React.useEffect(() => {
    async function fetchCommunities() {
      try {
        setLoading(true);
        const data = await getSubreddits();
        setCommunities(data);
      } catch (err) {
        console.error('Error fetching communities:', err);
        setError('Failed to load communities. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchCommunities();
  }, []);

  if (loading) {
    return (
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-6">Communities</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-6">Communities</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Communities</h1>
        {user && (
          <Link 
            href="/c/create" 
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
          >
            Create Community
          </Link>
        )}
      </div>

      {communities.length === 0 ? (
        <div className="bg-gray-50 p-8 rounded-md text-center">
          <p className="text-gray-600">No communities found.</p>
          {user && (
            <p className="mt-2">
              <Link href="/c/create" className="text-indigo-600 hover:underline">
                Create the first community
              </Link>
            </p>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {communities.map(community => (
            <Link 
              key={community.id} 
              href={`/c/${community.name}`}
              className="block p-4 border border-gray-200 rounded-md hover:border-indigo-300 hover:bg-indigo-50 transition"
            >
              <h2 className="text-xl font-medium">c/{community.name}</h2>
              <p className="text-gray-600 mt-1">
                {community.description || 'No description available'}
              </p>
              <div className="mt-2 text-sm text-gray-500">
                {community.memberCount || 0} members • Created {new Date(community.createdAt).toLocaleDateString()}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
} 