'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getFlairs, createFlair, updateFlair, deleteFlair } from '../../../../../lib/modapi';
import Spinner from '../../../../../components/Spinner';

export default function FlairsPage() {
  const { communityName } = useParams();
  const [flairs, setFlairs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreatingFlair, setIsCreatingFlair] = useState(false);
  const [editingFlairId, setEditingFlairId] = useState(null);
  const [newFlair, setNewFlair] = useState({ name: '', color: '#6366F1' }); // Default color: indigo
  const [processingAction, setProcessingAction] = useState(false);

  useEffect(() => {
    async function fetchFlairs() {
      try {
        setLoading(true);
        const response = await getFlairs(communityName);
        setFlairs(response || []);
      } catch (err) {
        console.error('Failed to fetch flairs:', err);
        setError('Failed to load flairs. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchFlairs();
  }, [communityName]);

  const handleCreateFlair = async (e) => {
    e.preventDefault();
    
    if (!newFlair.name) {
      alert('Please enter a flair name');
      return;
    }
    
    try {
      setProcessingAction(true);
      const response = await createFlair(communityName, newFlair);
      setFlairs(prev => [...prev, response]);
      setNewFlair({ name: '', color: '#6366F1' });
      setIsCreatingFlair(false);
    } catch (err) {
      console.error('Failed to create flair:', err);
      alert(`Failed to create flair: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleUpdateFlair = async (e, flair) => {
    e.preventDefault();
    
    if (!flair.name) {
      alert('Please enter a flair name');
      return;
    }
    
    try {
      setProcessingAction(true);
      const response = await updateFlair(communityName, flair.id, {
        name: flair.name,
        color: flair.color
      });
      
      setFlairs(prev => prev.map(f => f.id === flair.id ? response : f));
      setEditingFlairId(null);
    } catch (err) {
      console.error('Failed to update flair:', err);
      alert(`Failed to update flair: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingAction(false);
    }
  };

  const handleDeleteFlair = async (flairId) => {
    if (!confirm('Are you sure you want to delete this flair? This action cannot be undone.')) {
      return;
    }
    
    try {
      setProcessingAction(true);
      await deleteFlair(communityName, flairId);
      setFlairs(prev => prev.filter(f => f.id !== flairId));
    } catch (err) {
      console.error('Failed to delete flair:', err);
      alert(`Failed to delete flair: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingAction(false);
    }
  };

  const startEditing = (flair) => {
    setEditingFlairId(flair.id);
    setNewFlair({ name: flair.name, color: flair.color });
  };

  const cancelEditing = () => {
    setEditingFlairId(null);
    setNewFlair({ name: '', color: '#6366F1' });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Flairs</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Flairs</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold">Flairs</h1>
        <p className="text-gray-600 mt-1">
          Manage post flairs for your community.
        </p>
      </div>

      <div className="p-6">
        {!isCreatingFlair ? (
          <button 
            onClick={() => setIsCreatingFlair(true)}
            className="mb-6 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            disabled={processingAction}
          >
            Create New Flair
          </button>
        ) : (
          <div className="mb-8 bg-gray-50 p-4 rounded-md">
            <h3 className="text-lg font-medium mb-3">Create New Flair</h3>
            <form onSubmit={handleCreateFlair}>
              <div className="mb-4">
                <label htmlFor="flairName" className="block text-sm font-medium text-gray-700">
                  Flair Name
                </label>
                <input
                  type="text"
                  id="flairName"
                  value={newFlair.name}
                  onChange={(e) => setNewFlair(prev => ({ ...prev, name: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  required
                />
              </div>
              <div className="mb-4">
                <label htmlFor="flairColor" className="block text-sm font-medium text-gray-700">
                  Flair Color
                </label>
                <div className="flex items-center mt-1">
                  <input
                    type="color"
                    id="flairColor"
                    value={newFlair.color}
                    onChange={(e) => setNewFlair(prev => ({ ...prev, color: e.target.value }))}
                    className="h-8 w-8 rounded-md border border-gray-300"
                  />
                  <input
                    type="text"
                    value={newFlair.color}
                    onChange={(e) => setNewFlair(prev => ({ ...prev, color: e.target.value }))}
                    className="ml-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  disabled={processingAction}
                >
                  {processingAction ? 'Creating...' : 'Create Flair'}
                </button>
                <button
                  type="button"
                  onClick={() => setIsCreatingFlair(false)}
                  className="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  disabled={processingAction}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {flairs.length === 0 ? (
          <div className="text-center p-8">
            <p className="text-gray-500">No flairs have been created yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Flair
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Color
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {flairs.map((flair) => (
                  <tr key={flair.id} className="hover:bg-gray-50">
                    {editingFlairId === flair.id ? (
                      <td colSpan="3" className="px-6 py-4">
                        <form onSubmit={(e) => handleUpdateFlair(e, { id: flair.id, name: newFlair.name, color: newFlair.color })}>
                          <div className="flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-4">
                            <div className="flex-1">
                              <label htmlFor={`edit-name-${flair.id}`} className="sr-only">Flair Name</label>
                              <input
                                type="text"
                                id={`edit-name-${flair.id}`}
                                value={newFlair.name}
                                onChange={(e) => setNewFlair(prev => ({ ...prev, name: e.target.value }))}
                                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                required
                              />
                            </div>
                            <div className="sm:w-32">
                              <label htmlFor={`edit-color-${flair.id}`} className="sr-only">Flair Color</label>
                              <div className="flex items-center">
                                <input
                                  type="color"
                                  id={`edit-color-${flair.id}`}
                                  value={newFlair.color}
                                  onChange={(e) => setNewFlair(prev => ({ ...prev, color: e.target.value }))}
                                  className="h-8 w-8 rounded-md border border-gray-300"
                                />
                                <input
                                  type="text"
                                  value={newFlair.color}
                                  onChange={(e) => setNewFlair(prev => ({ ...prev, color: e.target.value }))}
                                  className="ml-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                />
                              </div>
                            </div>
                            <div className="flex space-x-2">
                              <button
                                type="submit"
                                className="inline-flex justify-center py-2 px-3 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                disabled={processingAction}
                              >
                                {processingAction ? 'Saving...' : 'Save'}
                              </button>
                              <button
                                type="button"
                                onClick={cancelEditing}
                                className="inline-flex justify-center py-2 px-3 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                disabled={processingAction}
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        </form>
                      </td>
                    ) : (
                      <>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span
                              className="px-2 py-1 text-xs font-medium rounded-full"
                              style={{
                                backgroundColor: flair.color,
                                color: isLightColor(flair.color) ? '#000' : '#fff'
                              }}
                            >
                              {flair.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div 
                              className="h-5 w-5 rounded-md mr-2"
                              style={{ backgroundColor: flair.color }}
                            ></div>
                            <span className="text-sm text-gray-500">{flair.color}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => startEditing(flair)}
                            className="text-indigo-600 hover:text-indigo-900 mr-3"
                            disabled={processingAction}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteFlair(flair.id)}
                            className="text-red-600 hover:text-red-900"
                            disabled={processingAction}
                          >
                            Delete
                          </button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper function to determine if a color is light or dark
function isLightColor(color) {
  const hex = color.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return brightness > 128;
} 