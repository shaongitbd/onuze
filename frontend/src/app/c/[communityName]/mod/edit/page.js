'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { fetchAPI, uploadImage } from '../../../../../lib/api';
import Spinner from '../../../../../components/Spinner';

export default function EditCommunityPage() {
  const { communityName } = useParams();
  const router = useRouter();
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [formData, setFormData] = useState({
    description: '',
    is_private: false,
    is_restricted: false,
    icon_image: null,
    banner_image: null
  });

  useEffect(() => {
    async function fetchCommunity() {
      try {
        setLoading(true);
        const response = await fetchAPI(`/communities/${communityName}/`);
        setCommunity(response);
        setFormData({
          description: response.description || '',
          is_private: response.is_private || false,
          is_restricted: response.is_restricted || false,
          icon_image: null,
          banner_image: null,
          current_icon: response.icon_image || null,
          current_banner: response.banner_image || null
        });
      } catch (err) {
        console.error('Failed to fetch community details:', err);
        setError('Failed to load community details. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchCommunity();
  }, [communityName]);

  const handleChange = (e) => {
    const { name, type, checked, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleFileChange = (e) => {
    const { name, files } = e.target;
    if (files && files[0]) {
      // Create a preview URL for the selected file
      const previewUrl = URL.createObjectURL(files[0]);
      
      setFormData(prev => ({
        ...prev,
        [name]: files[0],
        // Update the current_icon or current_banner with the preview URL
        [name === 'icon_image' ? 'current_icon' : 'current_banner']: previewUrl
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (processing) return;

    try {
      setProcessing(true);

      const formPayload = {
        description: formData.description,
        is_private: formData.is_private,
        is_restricted: formData.is_restricted
      };

      // Update community details
      await fetchAPI(`/communities/${community.path}/`, {
        method: 'PATCH',
        body: JSON.stringify(formPayload)
      });

      // Handle image uploads if needed
      if (formData.icon_image) {
        const uploadResult = await uploadImage(formData.icon_image, 'community');
        if (uploadResult && uploadResult.url) {
          // Update the community with the new icon
          await fetchAPI(`/communities/${community.path}/`, {
            method: 'PATCH',
            body: JSON.stringify({ icon_image: uploadResult.url })
          });
        }
      }

      if (formData.banner_image) {
        const uploadResult = await uploadImage(formData.banner_image, 'community');
        if (uploadResult && uploadResult.url) {
          // Update the community with the new banner
          await fetchAPI(`/communities/${community.path}/`, {
            method: 'PATCH',
            body: JSON.stringify({ banner_image: uploadResult.url })
          });
        }
      }

      // Navigate back to community page after successful update
      router.push(`/c/${communityName}`);

    } catch (err) {
      console.error('Failed to update community:', err);
      setError(`Failed to update community: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Edit Community</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Edit Community</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold">Edit Community</h1>
        <p className="text-gray-600 mt-1">
          Modify settings and information for c/{communityName}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            Community Description
          </label>
          <div className="mt-1">
            <textarea
              id="description"
              name="description"
              rows="4"
              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md"
              placeholder="Describe your community..."
              value={formData.description}
              onChange={handleChange}
            ></textarea>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Tell members what this community is all about.
          </p>
        </div>

        <div className="space-y-4">
          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="is_private"
                name="is_private"
                type="checkbox"
                className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                checked={formData.is_private}
                onChange={handleChange}
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="is_private" className="font-medium text-gray-700">
                Private Community
              </label>
              <p className="text-gray-500">
                Only approved users can view and submit to this community.
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="is_restricted"
                name="is_restricted"
                type="checkbox"
                className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                checked={formData.is_restricted}
                onChange={handleChange}
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="is_restricted" className="font-medium text-gray-700">
                Restricted Community
              </label>
              <p className="text-gray-500">
                Anyone can view, but only approved users can submit to this community.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Community Icon
            </label>
            <div className="mt-1 flex items-center space-x-4">
              <div className="w-20 h-20 rounded-full overflow-hidden bg-gray-100 flex-shrink-0">
                {formData.current_icon ? (
                  <img 
                    src={formData.current_icon} 
                    alt="Community icon" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <svg className="h-12 w-12" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                    </svg>
                  </div>
                )}
              </div>
              <div>
                <input
                  type="file"
                  id="icon_image"
                  name="icon_image"
                  accept="image/*"
                  className="sr-only"
                  onChange={handleFileChange}
                />
                <label
                  htmlFor="icon_image"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 cursor-pointer"
                >
                  Change Icon
                </label>
                {formData.icon_image && (
                  <p className="mt-2 text-sm text-gray-500">
                    Selected: {formData.icon_image.name}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Banner Image
            </label>
            <div className="mt-1 flex flex-col space-y-2">
              {formData.current_banner && (
                <div className="h-24 rounded-md overflow-hidden bg-gray-100">
                  <img 
                    src={formData.current_banner} 
                    alt="Community banner" 
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              <div>
                <input
                  type="file"
                  id="banner_image"
                  name="banner_image"
                  accept="image/*"
                  className="sr-only"
                  onChange={handleFileChange}
                />
                <label
                  htmlFor="banner_image"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 cursor-pointer"
                >
                  Change Banner
                </label>
                {formData.banner_image && (
                  <p className="mt-2 text-sm text-gray-500">
                    Selected: {formData.banner_image.name}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="pt-5 border-t border-gray-200">
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => router.push(`/c/${communityName}`)}
              className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={processing}
              className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {processing ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
} 