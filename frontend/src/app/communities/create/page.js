'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createCommunity, uploadImage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import Spinner from '@/components/Spinner';

export default function CreateCommunityPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [isNsfw, setIsNsfw] = useState(false);
  const [iconImage, setIconImage] = useState(null);
  const [iconPreview, setIconPreview] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Redirect if not logged in
  React.useEffect(() => {
    if (!isAuthenticated && !loading) {
      router.push('/login?redirect=/communities/create');
    }
  }, [isAuthenticated, loading, router]);

  const handleIconChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setIconImage(file);
      // Create preview URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setIconPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let iconUrl = null;
      
      // Upload icon image if selected
      if (iconImage) {
        const uploadResult = await uploadImage(iconImage, 'community');
        if (uploadResult && uploadResult.url) {
          iconUrl = uploadResult.url;
        }
      }

      // Create the community
      const communityData = {
        name,
        description,
        is_private: isPrivate,
        is_nsfw: isNsfw,
      };

      if (iconUrl) {
        communityData.icon_image = iconUrl;
      }

      const newCommunity = await createCommunity(communityData);
      router.push(`/communities/${newCommunity.id}`);
    } catch (err) {
      console.error('Error creating community:', err);
      
      let errorMessage = 'Failed to create community.';
      if (err.data) {
        errorMessage = Object.entries(err.data)
          .map(([field, errors]) => {
            if (Array.isArray(errors)) {
              return `${field}: ${errors.join(' ')}`;
            }
            return `${field}: ${errors}`;
          })
          .join('; ');
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return <div className="text-center py-8"><Spinner /></div>;
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Create a Community</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}

        <div className="mb-4">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Name
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="community_name"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Cannot be changed later. No spaces allowed. Use lowercase letters, numbers, and underscores only.
          </p>
        </div>

        <div className="mb-4">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows="3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="What's this community about?"
          />
        </div>

        <div className="mb-4">
          <label htmlFor="icon" className="block text-sm font-medium text-gray-700 mb-1">
            Community Icon (Optional)
          </label>
          <div className="flex items-center">
            {iconPreview && (
              <div className="mr-4">
                <img src={iconPreview} alt="Icon preview" className="w-16 h-16 rounded-full object-cover" />
              </div>
            )}
            <input
              type="file"
              id="icon"
              accept="image/*"
              onChange={handleIconChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="private"
              checked={isPrivate}
              onChange={(e) => setIsPrivate(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="private" className="ml-2 block text-sm text-gray-700">
              Private Community
            </label>
          </div>
          <p className="mt-1 text-xs text-gray-500 ml-6">
            Only approved users can view and participate.
          </p>
        </div>

        <div className="mb-6">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="nsfw"
              checked={isNsfw}
              onChange={(e) => setIsNsfw(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="nsfw" className="ml-2 block text-sm text-gray-700">
              NSFW (18+) Community
            </label>
          </div>
          <p className="mt-1 text-xs text-gray-500 ml-6">
            Content in this community may not be safe for work.
          </p>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => router.back()}
            className="mr-4 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {loading ? <Spinner /> : 'Create Community'}
          </button>
        </div>
      </form>
    </div>
  );
} 