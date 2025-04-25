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
  
  const [activeTab, setActiveTab] = useState('post'); // 'post' or 'media'
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selectedCommunity, setSelectedCommunity] = useState(communityId || '');
  const [communities, setCommunities] = useState([]);
  const [isNsfw, setIsNsfw] = useState(false);
  const [isSpoiler, setIsSpoiler] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null); // Can be image or video
  const [filePreview, setFilePreview] = useState('');
  const [fileType, setFileType] = useState(''); // 'image' or 'video'
  
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
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const type = selectedFile.type.startsWith('image/') ? 'image' : (selectedFile.type.startsWith('video/') ? 'video' : 'unknown');
      
      if (type === 'unknown') {
        setError('Unsupported file type. Please upload an image or video.');
        return;
      }
      
      setFile(selectedFile);
      setFileType(type);
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setFilePreview(reader.result);
      };
      reader.readAsDataURL(selectedFile);
    }
  };
  
  const handleRemoveFile = () => {
    setFile(null);
    setFilePreview('');
    setFileType('');
    // Clear file input
    const fileInput = document.getElementById('media-upload');
    if (fileInput) fileInput.value = '';
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
    
    if (activeTab === 'media' && !file) {
      setError('Please upload an image or video for media posts.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    let newPost = null;
    let communityPath = 'unknown';
    
    try {
      let postData = {
        title,
        community_id: selectedCommunity,
        is_nsfw: isNsfw,
        is_spoiler: isSpoiler
      };
      
      if (activeTab === 'post') {
        // Text post: include content
        postData.content = content;
      } else {
        // Media post: upload first, then include media details in createPost
        
        // 1. Upload media file
        const uploadResult = await uploadImage(file, 'post');
        if (!uploadResult || !uploadResult.url || !uploadResult.media_type) {
          throw new Error('Media upload failed or did not return expected data.');
        }
        
        // 2. Prepare media data for the post payload
        postData.media = [{
          media_url: uploadResult.url,
          media_type: uploadResult.media_type // Use media_type from upload result
        }];
        
        // Send an empty string instead of null for content
        postData.content = '';
      }
      
      // 3. Create the post (with or without media data included)
      newPost = await createPost(postData);
      
      // Redirect after successful post creation
      if (newPost && newPost.path) {
          const community = communities.find(c => c.id === selectedCommunity);
          communityPath = community?.path || community?.name || 'unknown';
          router.push(`/c/${communityPath}/post/${newPost.path}`);
      } else {
          // Fallback redirect or error handling if post path isn't available
          console.error("Post created but path missing in response:", newPost);
          setError('Post created, but failed to redirect. Please check the community page.');
      }
      
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
  
  const TabButton = ({ tabName, label }) => (
    <button
      type="button"
      onClick={() => setActiveTab(tabName)}
      className={`flex-1 py-2 px-4 text-center font-medium border-b-2 transition-colors duration-150 
        ${
          activeTab === tabName
            ? 'border-red-500 text-red-600'
            : 'border-gray-300 text-gray-500 hover:text-gray-700 hover:border-gray-400'
        }`}
    >
      {label}
    </button>
  );
  
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Create a Post</h1>
      
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg">
        {/* Community Selector */}
        <div className="p-4 border-b">
          <label htmlFor="community" className="block text-sm font-medium text-gray-700 mb-1">
            Choose a community
          </label>
          <select
            id="community"
            value={selectedCommunity}
            onChange={(e) => setSelectedCommunity(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500"
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
        
        {/* Tab Navigation */}
        <div className="flex border-b">
          <TabButton tabName="post" label="Post" />
          <TabButton tabName="media" label="Image & Video" />
        </div>

        <div className="p-6">
          {/* Title Input - common to both tabs */}
        <div className="mb-4">
            <label htmlFor="title" className="sr-only">Title</label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500"
            placeholder="Title"
            maxLength={300}
            required
          />
          <p className="mt-1 text-xs text-gray-500 text-right">
            {title.length}/300
          </p>
        </div>
        
          {/* Tab Content */}
          {activeTab === 'post' && (
        <div className="mb-4">
              <label htmlFor="content" className="sr-only">Content</label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
                rows="8"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500"
            placeholder="Text (optional)"
          />
        </div>
          )}
        
          {activeTab === 'media' && (
        <div className="mb-4">
              <label htmlFor="media-upload" className="block text-sm font-medium text-gray-700 mb-2">
                Upload Image or Video
          </label>
              {filePreview ? (
                <div className="relative mb-2 border p-2 rounded-md">
                  {fileType === 'image' ? (
                    <img src={filePreview} alt="Preview" className="max-h-80 rounded-md mx-auto" />
                  ) : (
                    <video controls src={filePreview} className="max-h-80 rounded-md mx-auto" />
                  )}
              <button
                type="button"
                    onClick={handleRemoveFile}
                    className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 w-6 h-6 flex items-center justify-center text-xs"
                    aria-label="Remove file"
              >
                ×
              </button>
            </div>
          ) : (
                <div className="flex items-center justify-center w-full">
                  <label htmlFor="media-upload" className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <svg className="w-8 h-8 mb-4 text-gray-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                        <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                      </svg>
                      <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                      <p className="text-xs text-gray-500">Image or Video (MP4, WEBM, etc.)</p>
                    </div>
                    <input id="media-upload" type="file" className="hidden" onChange={handleFileChange} accept="image/*,video/*" />
                  </label>
                </div> 
          )}
        </div>
          )}

          {/* NSFW/Spoiler Tags - common to both tabs */}
          <div className="mb-4 flex space-x-6">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="nsfw"
              checked={isNsfw}
              onChange={(e) => setIsNsfw(e.target.checked)}
                className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
            />
              <label htmlFor="nsfw" className="ml-2 block text-sm text-gray-700 font-medium">NSFW</label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="spoiler"
              checked={isSpoiler}
              onChange={(e) => setIsSpoiler(e.target.checked)}
                className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
            />
              <label htmlFor="spoiler" className="ml-2 block text-sm text-gray-700 font-medium">Spoiler</label>
            </div>
          </div>
          
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">
              {error}
        </div>
          )}
          
          {/* Submit Button */}
          <div className="flex justify-end pt-4 border-t mt-6">
          <button
            type="submit"
            disabled={loading}
              className={`px-6 py-2 font-medium rounded-full text-white ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-red-600 hover:bg-red-700'
              }`}
          >
              {loading ? <Spinner size="sm" /> : 'Post'}
          </button>
          </div>
        </div>
      </form>
    </div>
  );
} 