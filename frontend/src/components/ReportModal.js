import React, { useState } from 'react';
import fetchAPI from '@/lib/api';

const REPORT_REASONS = [
  { id: "spam", name: "Spam" },
  { id: "harassment", name: "Harassment" },
  { id: "violence", name: "Violence" },
  { id: "misinformation", name: "Misinformation" },
  { id: "hate", name: "Hate Speech" },
  { id: "self_harm", name: "Self Harm" },
  { id: "nsfw", name: "NSFW Content Not Marked" },
  { id: "other", name: "Other" }
];

export default function ReportModal({ isOpen, onClose, contentType, contentId }) {
  const [selectedReason, setSelectedReason] = useState('');
  const [details, setDetails] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (!selectedReason) {
      setError('Please select a reason for your report');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const reportData = {
        content_type: contentType, // 'post' or 'comment'
        content_id: contentId,
        reason: selectedReason,
        details: details.trim() || null
      };

      await fetchAPI('/moderation/reports/', {
        method: 'POST',
        body: JSON.stringify(reportData)
      });

      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setSelectedReason('');
        setDetails('');
      }, 1500);
    } catch (err) {
      console.error('Error submitting report:', err);
      setError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Report {contentType === 'post' ? 'Post' : 'Comment'}</h3>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={isSubmitting}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {success ? (
          <div className="bg-green-50 p-4 rounded-md text-green-700 mb-4">
            Report submitted successfully. Thank you for helping keep the community safe.
          </div>
        ) : (
          <>
            <p className="text-gray-700 mb-4">Why are you reporting this {contentType}?</p>
            
            {error && (
              <div className="bg-red-50 p-3 rounded-md text-red-700 text-sm mb-4">
                {error}
              </div>
            )}
            
            <div className="space-y-2 mb-4">
              {REPORT_REASONS.map((reason) => (
                <button 
                  key={reason.id}
                  onClick={() => setSelectedReason(reason.id)}
                  className={`w-full text-left px-4 py-2 rounded transition ${
                    selectedReason === reason.id 
                      ? 'bg-red-50 border border-red-200 text-red-700' 
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                  disabled={isSubmitting}
                >
                  {reason.name}
                </button>
              ))}
            </div>
            
            <div className="mb-4">
              <label htmlFor="report-details" className="block text-sm font-medium text-gray-700 mb-1">
                Additional details (optional)
              </label>
              <textarea
                id="report-details"
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500"
                rows={3}
                placeholder="Please provide any additional context about this report"
                disabled={isSubmitting}
              />
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button 
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-700 rounded hover:bg-gray-50 border border-gray-300"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button 
                onClick={handleSubmit}
                className={`px-4 py-2 text-sm text-white rounded ${
                  isSubmitting ? 'bg-gray-400 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'
                }`}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
} 