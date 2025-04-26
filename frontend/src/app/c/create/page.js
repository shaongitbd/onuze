'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import fetchAPI, { uploadImage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { getCookie } from '@/lib/utils';
import Spinner from '@/components/Spinner';

function CreateCommunityPage() {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [iconFile, setIconFile] = useState(null);
    const [iconPreview, setIconPreview] = useState('');
    const [bannerFile, setBannerFile] = useState(null);
    const [bannerPreview, setBannerPreview] = useState('');
    const [sidebarContent, setSidebarContent] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    // Redirect if not logged in
    if (!authLoading && !user) {
        router.push('/login?message=Please login to create a community');
        return null; // Render nothing while redirecting
    }

    const handleFileChange = (setter, previewSetter) => (event) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            setter(file);
            
            // Create preview URL
            const reader = new FileReader();
            reader.onloadend = () => {
                previewSetter(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };
    
    const handleRemoveFile = (fileSetter, previewSetter) => () => {
        fileSetter(null);
        previewSetter('');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setIsLoading(true);
        setError(null);

        if (!name.trim()) {
            setError('Community name cannot be empty.');
            setIsLoading(false);
            return;
        }

        try {
            let iconUrl = null;
            let bannerUrl = null;

            // Upload images if selected
            if (iconFile) {
                const result = await uploadImage(iconFile, 'community');
                iconUrl = result.url;
            }
            if (bannerFile) {
                const result = await uploadImage(bannerFile, 'community');
                bannerUrl = result.url;
            }

            // Prepare community data
            const communityData = {
                name: name.trim(),
                description: description.trim(),
                icon_image: iconUrl,
                banner_image: bannerUrl,
                sidebar_content: sidebarContent.trim(),
            };

            // Get JWT token (first try cookie, then localStorage)
          
        
            // Create the community
            try {
                const response = await fetchAPI(`/communities/`, {
                    method: 'POST',
                    body: JSON.stringify(communityData)
                });
                
                console.log('Community created successfully:', response);
                
                // Redirect to the new community page
                router.push(`/c/${response.name}`);
            } catch (err) {
                console.error('Failed to create community:', err);
                // Extract error message from fetchAPI error
                setError(err.message || 'Failed to create community. Please try again.');
                setIsLoading(false);
            }
        } catch (err) {
            console.error('Failed to create community:', err);
            setError(err.message || 'Failed to create community. Please try again.');
            setIsLoading(false);
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) {
        return <div className="text-center py-8"><Spinner /></div>;
    }

    return (
        <div className="max-w-3xl mx-auto px-4 py-8">
            <h1 className="text-2xl font-bold mb-6">Create a Community</h1>
            
            <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg">
                <div className="p-6">
                    {/* Community Name */}
                    <div className="mb-4">
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                            Community Name (c/)
                        </label>
                        <input
                            type="text"
                            name="name"
                            id="name"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            maxLength={21} // Typical Reddit limit
                            pattern="^[A-Za-z0-9_]+$" // Allow letters, numbers, underscore
                            title="Name can only contain letters, numbers, and underscores."
                        />
                        <p className="mt-1 text-xs text-gray-500">Cannot contain spaces or special characters other than underscores. Max 21 characters.</p>
                    </div>

                    {/* Description */}
                    <div className="mb-4">
                        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                            Description (Optional)
                        </label>
                        <textarea
                            id="description"
                            name="description"
                            rows={4}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            maxLength={500}
                            placeholder="Community description"
                        />
                        <p className="mt-1 text-xs text-gray-500 text-right">
                            {description.length}/500
                        </p>
                    </div>

                    {/* Image Uploads */}
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Icon Image (Optional)</label>
                        {iconPreview ? (
                            <div className="relative mb-2 border p-2 rounded-md">
                                <img src={iconPreview} alt="Icon Preview" className="max-h-40 rounded-md mx-auto" />
                                <button
                                    type="button"
                                    onClick={handleRemoveFile(setIconFile, setIconPreview)}
                                    className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 w-6 h-6 flex items-center justify-center text-xs"
                                    aria-label="Remove file"
                                >
                                    ×
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center w-full">
                                <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                                    <div className="flex flex-col items-center justify-center pt-3 pb-3">
                                        <svg className="w-8 h-8 mb-3 text-gray-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                                            <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                                        </svg>
                                        <p className="text-xs text-gray-500">Click to upload community icon</p>
                                    </div>
                                    <input 
                                        type="file" 
                                        accept="image/*" 
                                        onChange={handleFileChange(setIconFile, setIconPreview)} 
                                        className="hidden" 
                                        id="icon-upload"
                                    />
                                </label>
                            </div>
                        )}
                    </div>

                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Banner Image (Optional)</label>
                        {bannerPreview ? (
                            <div className="relative mb-2 border p-2 rounded-md">
                                <img src={bannerPreview} alt="Banner Preview" className="w-full h-32 object-cover rounded-md" />
                                <button
                                    type="button"
                                    onClick={handleRemoveFile(setBannerFile, setBannerPreview)}
                                    className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 w-6 h-6 flex items-center justify-center text-xs"
                                    aria-label="Remove file"
                                >
                                    ×
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center w-full">
                                <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                                    <div className="flex flex-col items-center justify-center pt-3 pb-3">
                                        <svg className="w-8 h-8 mb-3 text-gray-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                                            <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                                        </svg>
                                        <p className="text-xs text-gray-500">Click to upload banner image (recommended: 1920×384)</p>
                                    </div>
                                    <input 
                                        type="file" 
                                        accept="image/*" 
                                        onChange={handleFileChange(setBannerFile, setBannerPreview)} 
                                        className="hidden" 
                                        id="banner-upload"
                                    />
                                </label>
                            </div>
                        )}
                    </div>

                    {/* Sidebar Content */}
                    <div className="mb-4">
                        <label htmlFor="sidebarContent" className="block text-sm font-medium text-gray-700 mb-1">
                            Sidebar Content (Optional)
                        </label>
                        <textarea
                            id="sidebarContent"
                            name="sidebarContent"
                            rows={6}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500"
                            value={sidebarContent}
                            onChange={(e) => setSidebarContent(e.target.value)}
                            placeholder="Add text, links, and formatting for your community's sidebar"
                        />
                        <p className="mt-1 text-xs text-gray-500">You can use basic HTML formatting. This will be displayed in your community's sidebar.</p>
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
                            disabled={isLoading || authLoading}
                            className={`px-6 py-2 font-medium rounded-full text-white ${
                                isLoading || authLoading
                                    ? 'bg-gray-400 cursor-not-allowed'
                                    : 'bg-red-600 hover:bg-red-700'
                            }`}
                        >
                            {isLoading ? <Spinner size="sm" /> : 'Create Community'}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}

export default CreateCommunityPage; 