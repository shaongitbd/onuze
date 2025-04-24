'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { updateUserProfile, uploadImage } from '@/lib/api';
import Spinner from '@/components/Spinner';

export default function SettingsPage() {
  const { user, loading: authLoading, isAuthenticated, checkUserLoggedIn } = useAuth();
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    bio: '',
    email: '',
    displayName: '',
    notifications: true
  });
  
  const [profileImage, setProfileImage] = useState(null);
  const [profileImagePreview, setProfileImagePreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Redirect unauthenticated users
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?redirect=/settings');
    }
  }, [authLoading, isAuthenticated, router]);

  // Initialize form with user data once loaded
  useEffect(() => {
    if (user) {
      setFormData({
        bio: user.bio || '',
        email: user.email || '',
        displayName: user.display_name || user.username || '',
        notifications: user.preferences?.notifications !== false
      });
      
      if (user.profile_image) {
        setProfileImagePreview(user.profile_image);
      }
    }
  }, [user]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setProfileImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfileImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);
      
      let profileImageUrl = user?.profile_image;
      
      // Upload profile image if changed
      if (profileImage) {
        const uploadResult = await uploadImage(profileImage, 'profile');
        if (uploadResult && uploadResult.url) {
          profileImageUrl = uploadResult.url;
        }
      }
      
      // Prepare update data
      const updateData = {
        bio: formData.bio,
        display_name: formData.displayName,
        profile_image: profileImageUrl,
        preferences: {
          notifications: formData.notifications
        }
      };
      
      // Only include email if it was changed
      if (formData.email !== user.email) {
        updateData.email = formData.email;
      }
      
      // Update profile
      await updateUserProfile(updateData);
      
      // Refresh user data
      await checkUserLoggedIn();
      
      setSuccess(true);
    } catch (err) {
      console.error('Error updating profile:', err);
      
      // Format error message
      let errorMessage = 'Failed to update profile.';
      if (err.data) {
        if (typeof err.data === 'object') {
          errorMessage = Object.entries(err.data)
            .map(([field, errors]) => {
              if (Array.isArray(errors)) {
                return `${field}: ${errors.join(' ')}`;
              }
              return `${field}: ${errors}`;
            }).join('; ');
        } else if (err.data.detail) {
          errorMessage = err.data.detail;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex justify-center items-center min-h-[300px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">Account Settings</h1>
      
      {success && (
        <div className="mb-6 p-4 bg-green-50 text-green-700 rounded-md">
          Your profile has been updated successfully!
        </div>
      )}
      
      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        <div className="mb-6">
          <div className="flex items-center">
            <div className="mr-6">
              {profileImagePreview ? (
                <img 
                  src={profileImagePreview} 
                  alt="Profile preview" 
                  className="w-24 h-24 rounded-full object-cover border-2 border-gray-200"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center text-gray-500">
                  <span className="text-3xl">{user.username?.charAt(0).toUpperCase()}</span>
                </div>
              )}
            </div>
            
            <div className="flex-1">
              <label htmlFor="profile-image" className="block text-sm font-medium text-gray-700 mb-1">
                Profile Image
              </label>
              <input
                type="file"
                id="profile-image"
                accept="image/*"
                onChange={handleImageChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">
                Recommended size: 300x300 pixels. Max size: 5MB.
              </p>
            </div>
          </div>
        </div>
        
        <div className="mb-4">
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
            Username
          </label>
          <input
            type="text"
            id="username"
            value={user.username}
            disabled
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 cursor-not-allowed"
          />
          <p className="mt-1 text-xs text-gray-500">
            Usernames cannot be changed.
          </p>
        </div>
        
        <div className="mb-4">
          <label htmlFor="displayName" className="block text-sm font-medium text-gray-700 mb-1">
            Display Name
          </label>
          <input
            type="text"
            id="displayName"
            name="displayName"
            value={formData.displayName}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Your display name"
          />
        </div>
        
        <div className="mb-4">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="your-email@example.com"
          />
        </div>
        
        <div className="mb-6">
          <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-1">
            Bio
          </label>
          <textarea
            id="bio"
            name="bio"
            value={formData.bio}
            onChange={handleChange}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Tell us about yourself..."
          />
        </div>
        
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-3">Preferences</h3>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="notifications"
              name="notifications"
              checked={formData.notifications}
              onChange={handleChange}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="notifications" className="ml-2 block text-sm text-gray-700">
              Enable email notifications
            </label>
          </div>
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
            {loading ? <Spinner /> : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
} 