'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { createPost, getSubreddits, uploadImage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import Spinner from '@/components/Spinner';

export default function SubmitPostPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const communityId = searchParams.get('community_id');
  
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selectedCommunity, setSelectedCommunity] = useState(communityId || '');
  const [communities, setCommunities] = useState([]);
  const [isNsfw, setIsNsfw] = useState(false);
  const [isSpoiler, setIsSpoiler] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  
  // Check if user is authenticated
  useEffect(() => {
    if (!isAuthenticated && !loading) {
      router.push('/login?redirect=/submit');
    }
  }, [isAuthenticated, loading, router]);
  
  // Fetch available communities
  useEffect(() => {
    const fetchCommunities = async () => {
      try {
        const response = await getSubreddits();
        if (response && response.results) {
          setCommunities(response.results);
          
          // If community_id is in URL params but not set yet, set it
          if (communityId && !selectedCommunity) {
            setSelectedCommunity(communityId);
          }
        }
      } catch (err) {
        console.error('Error fetching communities:', err);
        setError('Failed to load communities. Please try again later.');
      }
    };
    
    fetchCommunities();
  }, [communityId, selectedCommunity]);
  
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };
  
  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview('');
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedCommunity) {
      setError('Please select a community.');
      return;
    }
    
    if (!title.trim()) {
      setError('Title is required.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      let postData = {
        title,
        content,
        community_id: selectedCommunity,
        is_nsfw: isNsfw,
        is_spoiler: isSpoiler
      };
      
      // Upload image if selected
      if (imageFile) {
        const uploadResult = await uploadImage(imageFile, 'post');
        if (uploadResult && uploadResult.url) {
          // Depending on your API, you might add the image to the post content
          // or add it to a media array
          postData.media = [{ media_url: uploadResult.url }];
        }
      }
      
      const newPost = await createPost(postData);
      router.push(`/posts/${newPost.id}`);
    } catch (err) {
      console.error('Error creating post:', err);
      
      let errorMessage = 'Failed to create post.';
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
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Create a Post</h1>
      
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}
        
        <div className="mb-4">
          <label htmlFor="community" className="block text-sm font-medium text-gray-700 mb-1">
            Community
          </label>
          <select
            id="community"
            value={selectedCommunity}
            onChange={(e) => setSelectedCommunity(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            required
          >
            <option value="">Select a community</option>
            {communities.map((community) => (
              <option key={community.id} value={community.id}>
                c/{community.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="mb-4">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Title"
            maxLength={300}
            required
          />
          <p className="mt-1 text-xs text-gray-500 text-right">
            {title.length}/300
          </p>
        </div>
        
        <div className="mb-4">
          <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
            Content
          </label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows="6"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Text (optional)"
          />
        </div>
        
        <div className="mb-4">
          <label htmlFor="image" className="block text-sm font-medium text-gray-700 mb-1">
            Image (optional)
          </label>
          {imagePreview ? (
            <div className="relative mb-2">
              <img 
                src={imagePreview} 
                alt="Preview" 
                className="max-h-60 rounded-md"
              />
              <button
                type="button"
                onClick={handleRemoveImage}
                className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 w-6 h-6 flex items-center justify-center"
              >
                ×
              </button>
            </div>
          ) : (
            <input
              type="file"
              id="image"
              accept="image/*"
              onChange={handleImageChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          )}
        </div>
        
        <div className="mb-4 flex space-x-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="nsfw"
              checked={isNsfw}
              onChange={(e) => setIsNsfw(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="nsfw" className="ml-2 block text-sm text-gray-700">
              NSFW
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="spoiler"
              checked={isSpoiler}
              onChange={(e) => setIsSpoiler(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="spoiler" className="ml-2 block text-sm text-gray-700">
              Spoiler
            </label>
          </div>
        </div>
        
        <div className="flex justify-end mt-6">
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
            {loading ? <Spinner /> : 'Post'}
          </button>
        </div>
      </form>
    </div>
  );
} 