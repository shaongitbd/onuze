'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { updateUserProfile, uploadImage, changePassword } from '@/lib/api';
import Spinner from '@/components/Spinner';

export default function SettingsPage() {
  const { user, loading: authLoading, isAuthenticated, checkUserLoggedIn } = useAuth();
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    bio: '',
    email: '',
    displayName: '',
    username: '',
    notifications: true
  });
  
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    re_new_password: ''
  });
  
  const [profileImage, setProfileImage] = useState(null);
  const [profileImagePreview, setProfileImagePreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [passwordError, setPasswordError] = useState(null);

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
        username: user.username || '',
        notifications: user.preferences?.notifications !== false
      });
      
      // Check for avatar first (backend field name), then fall back to profile_image (frontend field name)
      if (user.avatar) {
        setProfileImagePreview(user.avatar);
        console.log("Using user.avatar for profile preview:", user.avatar);
      } else if (user.profile_image) {
        setProfileImagePreview(user.profile_image);
        console.log("Using user.profile_image for profile preview:", user.profile_image);
      } else {
        console.log("No avatar/profile image found for user:", user);
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

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value
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
      
      // Store current avatar - check both possible field names
      let currentAvatar = user?.avatar || user?.profile_image;
      
      // Upload profile image if changed
      if (profileImage) {
        console.log("Uploading profile image...");
        const uploadResult = await uploadImage(profileImage, 'profile');
        if (uploadResult && uploadResult.url) {
          currentAvatar = uploadResult.url;
          console.log("Image uploaded successfully:", currentAvatar);
        }
      }
      
      // Prepare update data with field names matching the backend serializer
      const updateData = {
        bio: formData.bio,
        // Include username for editing
        username: formData.username,
        // Map profile_image to avatar
        avatar: currentAvatar,
        // Include two_factor_enabled if needed
        two_factor_enabled: user.two_factor_enabled || false
      };
      
      // Only include email if it was changed
      if (formData.email !== user.email) {
        updateData.email = formData.email;
      }
      
      console.log("Sending profile update with data:", JSON.stringify(updateData));
      
      // Update profile
      const response = await updateUserProfile(updateData);
      console.log("Profile update response:", response);
      
      // Update preview image with the new avatar
      setProfileImagePreview(currentAvatar);
      
      // Refresh user data
      const refreshedUser = await checkUserLoggedIn();
      console.log("Refreshed user data:", refreshedUser);
      
      // Debug available fields
      if (refreshedUser) {
        console.log("Available user fields:", Object.keys(refreshedUser));
        console.log("User avatar field:", refreshedUser.avatar);
        console.log("User profile_image field:", refreshedUser.profile_image);
      }
      
      setSuccess(true);
    } catch (err) {
      console.error('Error updating profile:', err);
      console.log('Error details:', err.data ? JSON.stringify(err.data) : 'No error data');
      console.log('Error status:', err.status || 'No status code');
      
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

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    
    // Validate passwords
    if (passwordData.new_password !== passwordData.re_new_password) {
      setPasswordError('New passwords do not match');
      return;
    }
    
    if (passwordData.new_password.length < 8) {
      setPasswordError('New password must be at least 8 characters long');
      return;
    }
    
    try {
      setPasswordLoading(true);
      setPasswordError(null);
      setPasswordSuccess(false);
      
      console.log('Changing password...');
      
      // Call the API to change password
      await changePassword(passwordData);
      
      // Reset form
      setPasswordData({
        current_password: '',
        new_password: '',
        re_new_password: ''
      });
      
      setPasswordSuccess(true);
    } catch (err) {
      console.error('Error changing password:', err);
      console.log('Error details:', err.data ? JSON.stringify(err.data) : 'No error data');
      
      // Format error message
      let errorMessage = 'Failed to change password.';
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
      
      setPasswordError(errorMessage);
    } finally {
      setPasswordLoading(false);
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
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Account Settings</h1>
      
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 text-blue-700 rounded-md dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-300">
        <p>
          <strong>Note:</strong> You can update your username, profile image, bio, and email address. 
          Notification preferences are not currently supported.
        </p>
      </div>
      
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-md dark:bg-green-900/30 dark:border-green-800 dark:text-green-300">
          Your profile has been updated successfully!
        </div>
      )}
      
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md dark:bg-red-900/30 dark:border-red-800 dark:text-red-300">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6 mb-8 border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white border-b pb-2 border-gray-200 dark:border-gray-700">Profile Information</h2>
        
        <div className="mb-6">
          <div className="flex items-center flex-wrap md:flex-nowrap">
            <div className="mr-6 mb-4 md:mb-0">
              {profileImagePreview ? (
                <img 
                  src={profileImagePreview} 
                  alt="Profile preview" 
                  className="w-24 h-24 rounded-full object-cover border-2 border-gray-200 dark:border-gray-600"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-500 dark:text-gray-400">
                  <span className="text-3xl">{user.username?.charAt(0).toUpperCase()}</span>
                </div>
              )}
            </div>
            
            <div className="flex-1">
              <label htmlFor="profile-image" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Profile Image
              </label>
              <input
                type="file"
                id="profile-image"
                accept="image/*"
                onChange={handleImageChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Recommended size: 300x300 pixels. Max size: 5MB.
              </p>
            </div>
          </div>
        </div>
        
        <div className="mb-4">
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Username
          </label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:focus:ring-red-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Choose a unique username. This will be visible to other users.
          </p>
        </div>
        
        <div className="mb-4">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:focus:ring-red-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            placeholder="your-email@example.com"
          />
        </div>
        
        <div className="mb-6">
          <label htmlFor="bio" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Bio
          </label>
          <textarea
            id="bio"
            name="bio"
            value={formData.bio}
            onChange={handleChange}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:focus:ring-red-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            placeholder="Tell us about yourself..."
          />
        </div>
        
        <div className="mb-6 opacity-50">
          <h3 className="text-lg font-medium mb-3 text-gray-900 dark:text-white">Preferences</h3>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="notifications"
              name="notifications"
              checked={formData.notifications}
              onChange={handleChange}
              disabled
              className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded cursor-not-allowed"
            />
            <label htmlFor="notifications" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Enable email notifications (not currently supported)
            </label>
          </div>
        </div>
        
        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => router.back()}
            className="mr-4 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
          >
            {loading ? <Spinner /> : 'Save Changes'}
          </button>
        </div>
      </form>
      
      {/* Password Change Section */}
      <form onSubmit={handlePasswordSubmit} className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white border-b pb-2 border-gray-200 dark:border-gray-700">Change Password</h2>
        
        {passwordSuccess && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-md dark:bg-green-900/30 dark:border-green-800 dark:text-green-300">
            Your password has been changed successfully!
          </div>
        )}
        
        {passwordError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-md dark:bg-red-900/30 dark:border-red-800 dark:text-red-300">
            {passwordError}
          </div>
        )}
        
        <div className="mb-4">
          <label htmlFor="current_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Current Password
          </label>
          <input
            type="password"
            id="current_password"
            name="current_password"
            value={passwordData.current_password}
            onChange={handlePasswordChange}
            required
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:focus:ring-red-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>
        
        <div className="mb-4">
          <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            New Password
          </label>
          <input
            type="password"
            id="new_password"
            name="new_password"
            value={passwordData.new_password}
            onChange={handlePasswordChange}
            required
            minLength={10}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:focus:ring-red-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Password must be at least 10 characters long.
          </p>
        </div>
        
        <div className="mb-6">
          <label htmlFor="re_new_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Confirm New Password
          </label>
          <input
            type="password"
            id="re_new_password"
            name="re_new_password"
            value={passwordData.re_new_password}
            onChange={handlePasswordChange}
            required
            minLength={10}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 dark:focus:ring-red-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>
        
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={passwordLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
          >
            {passwordLoading ? <Spinner /> : 'Change Password'}
          </button>
        </div>
      </form>
    </div>
  );
} 