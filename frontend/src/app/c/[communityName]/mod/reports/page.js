'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { getReports, resolveReport, rejectReport } from '../../../../../lib/modapi';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import Spinner from '../../../../../components/Spinner';

export default function ReportsPage() {
  const { communityName } = useParams();
  const searchParams = useSearchParams();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(searchParams.get('status') || 'pending');
  const [processingReports, setProcessingReports] = useState({});

  useEffect(() => {
    async function fetchReports() {
      try {
        setLoading(true);
        console.log('Fetching reports for community:', communityName);
        const response = await getReports(communityName);
        console.log('Reports response:', response);
        setReports(response.results || []);
      } catch (err) {
        console.error('Failed to fetch reports:', err);
        setError('Failed to load reports. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchReports();
  }, [communityName]);

  const handleResolveReport = async (reportId) => {
    if (processingReports[reportId]) return;
    
    try {
      setProcessingReports(prev => ({ ...prev, [reportId]: true }));
      console.log('Resolving report:', reportId);
      await resolveReport(reportId);
      
      // Remove the report from the list
      setReports(prev => prev.filter(report => report.id !== reportId));
    } catch (err) {
      console.error('Failed to resolve report:', err);
      alert(`Failed to resolve report: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingReports(prev => ({ ...prev, [reportId]: false }));
    }
  };

  const handleRejectReport = async (reportId) => {
    if (processingReports[reportId]) return;
    
    try {
      setProcessingReports(prev => ({ ...prev, [reportId]: true }));
      await rejectReport(reportId);
      
      // Remove the report from the list
      setReports(prev => prev.filter(report => report.id !== reportId));
    } catch (err) {
      console.error('Failed to reject report:', err);
      alert(`Failed to reject report: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessingReports(prev => ({ ...prev, [reportId]: false }));
    }
  };

  const filteredReports = reports.filter(report => {
    if (activeTab === 'pending') return report.status === 'pending';
    if (activeTab === 'resolved') return report.status === 'resolved';
    if (activeTab === 'rejected') return report.status === 'rejected';
    return true; // Should not happen, but fallback
  });

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Reports</h1>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Reports</h1>
        <div className="bg-red-50 p-4 rounded-md text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="text-gray-600 mt-1">
          Review and manage reported content in your community.
        </p>
      </div>

      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('pending')}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'pending'
                ? 'bg-indigo-100 text-indigo-800 font-medium'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Pending
          </button>
          <button
            onClick={() => setActiveTab('resolved')}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'resolved'
                ? 'bg-indigo-100 text-indigo-800 font-medium'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Resolved
          </button>
          <button
            onClick={() => setActiveTab('rejected')}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'rejected'
                ? 'bg-indigo-100 text-indigo-800 font-medium'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Rejected
          </button>
        </div>
      </div>

      {filteredReports.length === 0 ? (
        <div className="p-6 text-center">
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
          <h3 className="mt-2 text-lg font-medium text-gray-900">No {activeTab.toLowerCase()} reports</h3>
          <p className="mt-1 text-gray-500">
            There are currently no {activeTab.toLowerCase()} reports in this community.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reported Content
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reason
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reported By
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredReports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <div className="text-sm font-medium text-gray-900">
                        {report.content_type === 'post' ? 'Post: ' : 'Comment: '}
                        {report.content_preview ? (
                          <span className="text-gray-700">
                            {report.content_preview.length > 100 
                              ? report.content_preview.substring(0, 100) + '...' 
                              : report.content_preview}
                          </span>
                        ) : (
                          <span className="text-gray-500 italic">No preview available</span>
                        )}
                      </div>
                      <div className="text-xs text-indigo-600 mt-1">
                        {report.content_type === 'post' ? (
                          <Link href={`/c/${report.community.path}/post/${report.post_path}`}>
                            View Post
                          </Link>
                        ) : (
                          <Link href={`/c/${communityName}/post/${report.post_path}/comment/${report.comment_path}`}>
                            View Comment
                          </Link>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {report.reason || 'No reason provided'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-medium text-gray-900">
                        {report.reporter?.username || 'Unknown User'}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {activeTab === 'pending' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleResolveReport(report.id)}
                          disabled={processingReports[report.id]}
                          className="text-green-600 hover:text-green-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                        >
                          {processingReports[report.id] ? 'Processing...' : 'Resolve'}
                        </button>
                        <button
                          onClick={() => handleRejectReport(report.id)}
                          disabled={processingReports[report.id]}
                          className="text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed ml-3"
                        >
                          {processingReports[report.id] ? 'Processing...' : 'Reject'}
                        </button>
                      </div>
                    )}
                    {activeTab === 'resolved' && (
                      <span className="text-green-600">Resolved</span>
                    )}
                    {activeTab === 'rejected' && (
                      <span className="text-red-600">Rejected</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 