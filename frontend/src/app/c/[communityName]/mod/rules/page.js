'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { fetchAPI } from '../../../../../lib/api';
import Spinner from '../../../../../components/Spinner';

export default function CommunityRulesPage() {
  const { communityName } = useParams();
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAdding, setIsAdding] = useState(false);
  const [isEditing, setIsEditing] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [newRule, setNewRule] = useState({ title: '', description: '' });

  useEffect(() => {
    fetchRules();
  }, [communityName]);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await fetchAPI(`/communities/${communityName}/rules/`);
      setRules(response.results || response);
    } catch (err) {
      console.error('Failed to fetch community rules:', err);
      setError('Failed to load community rules. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRule = async () => {
    if (processing) return;
    if (!newRule.title.trim()) {
      alert('Rule title is required');
      return;
    }

    try {
      setProcessing(true);
      const response = await fetchAPI(`/communities/${communityName}/rules/`, {
        method: 'POST',
        body: JSON.stringify({
          title: newRule.title,
          description: newRule.description,
          order: rules.length // Set order to the end of the list
        })
      });

      // Add the new rule to the list
      setRules(prev => [...prev, response]);
      
      // Reset the form
      setNewRule({ title: '', description: '' });
      setIsAdding(false);
    } catch (err) {
      console.error('Failed to add rule:', err);
      alert(`Failed to add rule: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleUpdateRule = async (ruleId) => {
    if (processing) return;
    if (!isEditing || !isEditing.title.trim()) {
      alert('Rule title is required');
      return;
    }

    try {
      setProcessing(true);
      const response = await fetchAPI(`/communities/${communityName}/rules/${ruleId}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          title: isEditing.title,
          description: isEditing.description
        })
      });

      // Update the rule in the list
      setRules(prev => prev.map(rule => rule.id === ruleId ? response : rule));
      
      // Exit edit mode
      setIsEditing(null);
    } catch (err) {
      console.error('Failed to update rule:', err);
      alert(`Failed to update rule: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (processing) return;
    if (!confirm('Are you sure you want to delete this rule?')) return;

    try {
      setProcessing(true);
      await fetchAPI(`/communities/${communityName}/rules/${ruleId}/`, {
        method: 'DELETE'
      });

      // Remove the rule from the list
      setRules(prev => prev.filter(rule => rule.id !== ruleId));
    } catch (err) {
      console.error('Failed to delete rule:', err);
      alert(`Failed to delete rule: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleStartEdit = (rule) => {
    setIsEditing({
      id: rule.id,
      title: rule.title,
      description: rule.description || ''
    });
    setIsAdding(false);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Community Rules</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Community Rules</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold">Community Rules</h1>
        <p className="text-gray-600 mt-1">
          Create and manage rules for your community.
        </p>
      </div>

      <div className="p-6">
        {rules.length === 0 && !isAdding ? (
          <div className="text-center py-8">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">No rules yet</h3>
            <p className="mt-1 text-gray-500">
              Get started by creating your first community rule.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setIsAdding(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Add First Rule
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Rule list */}
            <div className="space-y-4">
              {rules.map((rule) => (
                <div key={rule.id} className="border border-gray-200 rounded-md p-4">
                  {isEditing && isEditing.id === rule.id ? (
                    <div className="space-y-4">
                      <div>
                        <label htmlFor={`rule-title-${rule.id}`} className="block text-sm font-medium text-gray-700">
                          Rule Title
                        </label>
                        <input
                          type="text"
                          id={`rule-title-${rule.id}`}
                          value={isEditing.title}
                          onChange={(e) => setIsEditing({ ...isEditing, title: e.target.value })}
                          className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                          placeholder="Enter rule title"
                        />
                      </div>
                      <div>
                        <label htmlFor={`rule-desc-${rule.id}`} className="block text-sm font-medium text-gray-700">
                          Description (Optional)
                        </label>
                        <textarea
                          id={`rule-desc-${rule.id}`}
                          rows="3"
                          value={isEditing.description}
                          onChange={(e) => setIsEditing({ ...isEditing, description: e.target.value })}
                          className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                          placeholder="Enter rule description"
                        ></textarea>
                      </div>
                      <div className="flex space-x-3">
                        <button
                          onClick={() => handleUpdateRule(rule.id)}
                          disabled={processing}
                          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                          {processing ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          onClick={() => setIsEditing(null)}
                          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="flex justify-between">
                        <h3 className="text-lg font-medium text-gray-900">{rule.title}</h3>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleStartEdit(rule)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteRule(rule.id)}
                            disabled={processing}
                            className="text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                      {rule.description && (
                        <p className="mt-2 text-sm text-gray-500">{rule.description}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Add new rule form */}
            {isAdding ? (
              <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Rule</h3>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="new-rule-title" className="block text-sm font-medium text-gray-700">
                      Rule Title
                    </label>
                    <input
                      type="text"
                      id="new-rule-title"
                      value={newRule.title}
                      onChange={(e) => setNewRule({ ...newRule, title: e.target.value })}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                      placeholder="Enter rule title"
                    />
                  </div>
                  <div>
                    <label htmlFor="new-rule-desc" className="block text-sm font-medium text-gray-700">
                      Description (Optional)
                    </label>
                    <textarea
                      id="new-rule-desc"
                      rows="3"
                      value={newRule.description}
                      onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                      className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                      placeholder="Enter rule description"
                    ></textarea>
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={handleAddRule}
                      disabled={processing}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {processing ? 'Adding...' : 'Add Rule'}
                    </button>
                    <button
                      onClick={() => {
                        setIsAdding(false);
                        setNewRule({ title: '', description: '' });
                      }}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center pt-4">
                <button
                  onClick={() => {
                    setIsAdding(true);
                    setIsEditing(null);
                  }}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Add Rule
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 