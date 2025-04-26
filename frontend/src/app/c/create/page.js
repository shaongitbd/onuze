'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import fetchAPI, { uploadImage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { getCookie } from '@/lib/utils';

function CreateCommunityPage() {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [iconFile, setIconFile] = useState(null);
    const [bannerFile, setBannerFile] = useState(null);
    const [sidebarFile, setSidebarFile] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    // Redirect if not logged in
    if (!authLoading && !user) {
        router.push('/login?message=Please login to create a community');
        return null; // Render nothing while redirecting
    }

    const handleFileChange = (setter) => (event) => {
        if (event.target.files && event.target.files[0]) {
            setter(event.target.files[0]);
        }
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
            let sidebarImageUrl = null;

            // Upload images if selected
            if (iconFile) {
                const result = await uploadImage(iconFile, 'community');
                iconUrl = result.url;
            }
            if (bannerFile) {
                const result = await uploadImage(bannerFile, 'community');
                bannerUrl = result.url;
            }
            if (sidebarFile) {
                const result = await uploadImage(sidebarFile, 'community');
                sidebarImageUrl = result.url;
            }

            // Prepare community data
            const communityData = {
                name: name.trim(),
                description: description.trim(),
                icon_url: iconUrl,
                banner_url: bannerUrl,
                sidebar_image_url: sidebarImageUrl,
            };

            // Get JWT token (first try cookie, then localStorage)
          
        
            // Create the community
            const response = await fetchAPI(`/communities/`, {
                method: 'POST',
           
                body: JSON.stringify(communityData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error( `Failed to create community: ${response.status}`);
            }

            const newCommunity = await response.json();
            console.log('Community created successfully:', newCommunity);

            // Redirect to the new community page
            router.push(`/c/${newCommunity.name}`);
        } catch (err) {
            console.error('Failed to create community:', err);
            setError(err.message || 'Failed to create community. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) {
        return <div>Loading...</div>; // Show loading state while checking auth
    }

    return (
        <div className="max-w-2xl mx-auto mt-8 p-4 bg-white rounded shadow">
            <h1 className="text-2xl font-bold mb-6 text-center">Create a Community</h1>
            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                        Community Name (c/)
                    </label>
                    <div className="mt-1">
                        <input
                            type="text"
                            name="name"
                            id="name"
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            maxLength={21} // Typical Reddit limit
                            pattern="^[A-Za-z0-9_]+$" // Allow letters, numbers, underscore
                            title="Name can only contain letters, numbers, and underscores."
                        />
                        <p className="mt-1 text-xs text-gray-500">Cannot contain spaces or special characters other than underscores. Max 21 characters.</p>
                    </div>
                </div>

                <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                        Description (Optional)
                    </label>
                    <div className="mt-1">
                        <textarea
                            id="description"
                            name="description"
                            rows={4}
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            maxLength={500}
                        />
                         <p className="mt-1 text-xs text-gray-500">Max 500 characters.</p>
                    </div>
                </div>

                {/* Image Uploads */}
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Icon Image (Optional)</label>
                        <input type="file" accept="image/*" onChange={handleFileChange(setIconFile)} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"/>
                        {iconFile && <span className="text-xs text-gray-600 ml-2">{iconFile.name}</span>}
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Banner Image (Optional)</label>
                        <input type="file" accept="image/*" onChange={handleFileChange(setBannerFile)} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"/>
                        {bannerFile && <span className="text-xs text-gray-600 ml-2">{bannerFile.name}</span>}
                    </div>
                     <div>
                        <label className="block text-sm font-medium text-gray-700">Sidebar Image (Optional)</label>
                        <input type="file" accept="image/*" onChange={handleFileChange(setSidebarFile)} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"/>
                        {sidebarFile && <span className="text-xs text-gray-600 ml-2">{sidebarFile.name}</span>}
                    </div>
                </div>

                {error && (
                    <p className="text-sm text-red-600">{error}</p>
                )}

                <div>
                    <button
                        type="submit"
                        disabled={isLoading || authLoading}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? 'Creating...' : 'Create Community'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default CreateCommunityPage; 