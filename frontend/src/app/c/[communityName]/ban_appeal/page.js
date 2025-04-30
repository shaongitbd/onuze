'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { fetchAPI } from '@/lib/api';
import Spinner from '@/components/Spinner';

export default function BanAppealPage() {
  const { communityName } = useParams();
  const router = useRouter();
  const [alertMessage, setAlertMessage] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [communityId, setCommunityId] = useState(null);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    reason: '',
    evidence: ''
  });
  
  useEffect(() => {
    async function fetchCommunityId() {
      try {
        setLoading(true);
        const response = await fetchAPI(`/communities/${communityName}`);
        setCommunityId(response.id);
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch community:', err);
        setError('Community not found or you don\'t have permission to view it.');
        setLoading(false);
      }
    }
    
    fetchCommunityId();
  }, [communityName]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.reason.trim()) {
      setAlertMessage({
        type: 'error',
        text: 'Please provide a reason for your appeal.'
      });
      return;
    }
    
    try {
      setSubmitting(true);
      
      const appealData = {
        appeal_type: 'community_ban',
        reason: formData.reason,
        evidence: formData.evidence || null,
        community_id: communityId
      };
      
      await fetchAPI('/moderation/ban-appeals/', {
        method: 'POST',
        body: JSON.stringify(appealData)
      });
      
      setAlertMessage({
        type: 'success',
        text: 'Your ban appeal has been submitted successfully. Moderators will review it soon.'
      });
      
      // Redirect to the community page after successful submission
      setTimeout(() => {
        router.push(`/c/${communityName}`);
      }, 1500);
      
    } catch (err) {
      console.error('Failed to submit ban appeal:', err);
      setAlertMessage({
        type: 'error',
        text: err.message || 'Something went wrong. Please try again later.'
      });
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[70vh]">
        <Spinner size="lg" />
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="max-w-3xl mx-auto mt-8 p-6 bg-white rounded-lg shadow">
        <h1 className="text-xl font-bold text-red-600 mb-4">Error</h1>
        <p className="text-gray-700">{error}</p>
      </div>
    );
  }
  
  return (
    <div className="max-w-3xl mx-auto mt-8 p-6 bg-white rounded-lg shadow">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Appeal Your Ban</h1>
      <p className="text-gray-600 mb-6">
        Use this form to appeal your ban from r/{communityName}. Provide a clear explanation of why you believe the ban should be reconsidered.
      </p>
      
      {alertMessage && (
        <div className={`p-4 rounded-md mb-6 ${
          alertMessage.type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
        }`}>
          {alertMessage.text}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-1">
            Why should your ban be lifted? *
          </label>
          <textarea
            id="reason"
            name="reason"
            rows={6}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Explain why you believe your ban should be reconsidered. Be respectful and provide specific details."
            value={formData.reason}
            onChange={handleChange}
          />
          <p className="mt-1 text-sm text-gray-500">
            Be respectful, specific, and honest in your appeal.
          </p>
        </div>
        
        <div>
          <label htmlFor="evidence" className="block text-sm font-medium text-gray-700 mb-1">
            Additional Evidence (Optional)
          </label>
          <textarea
            id="evidence"
            name="evidence"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Add any evidence or additional context that supports your appeal."
            value={formData.evidence}
            onChange={handleChange}
          />
          <p className="mt-1 text-sm text-gray-500">
            You can provide links or additional context that supports your appeal.
          </p>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-md">
          <p className="text-sm text-gray-600">
            <strong>Note:</strong> The moderators will review your appeal and make a decision. Please be patient as this process may take some time.
          </p>
        </div>
        
        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => router.back()}
            className="mr-4 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            disabled={submitting}
          >
            {submitting ? 'Submitting...' : 'Submit Appeal'}
          </button>
        </div>
      </form>
    </div>
  );
} 