'use client';

import React, { useState, useEffect } from 'react';
import { useParams, usePathname } from 'next/navigation';
import Link from 'next/link';
import { getCommunityDetails } from '../../../../lib/api';
import { useAuth } from '../../../../lib/auth';
import Spinner from '../../../../components/Spinner';

export default function ModeratorLayout({ children }) {
  const { communityName } = useParams();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, checkUserLoggedIn } = useAuth();
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModerator, setIsModerator] = useState(false);
  const [initialCheckDone, setInitialCheckDone] = useState(false);

  // First check: try to refresh the auth state on direct navigation
  useEffect(() => {
    if (isLoading === false && !initialCheckDone) {
      // Ensure we run checkUserLoggedIn at least once
      checkUserLoggedIn();
      setInitialCheckDone(true);
    }
  }, [isLoading, initialCheckDone, checkUserLoggedIn]);

  useEffect(() => {
    async function checkModeratorStatus() {
      console.log("Checking mod status:", { isAuthenticated, isLoading, user });
      
      // Wait for auth to complete regardless of outcome
      if (isLoading) {
        console.log("Still loading auth status, waiting...");
        return;
      }

      // Proceed with mod check only if we have a user
      if (!user) {
        console.log("No user found after auth check completed");
        setError('You must be logged in to access moderator tools.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const communityData = await getCommunityDetails(communityName);
        console.log("Community data:", communityData);
        setCommunity(communityData);

        if (communityData.moderators) {
          const userIsModerator = communityData.moderators.some(
            mod => mod.user_id === user.id
          );
          console.log("Checking if user is moderator:", { 
            userId: user.id, 
            moderators: communityData.moderators,
            userIsModerator 
          });
          
          setIsModerator(userIsModerator);

          if (!userIsModerator) {
            setError('You do not have permission to access moderator tools for this community.');
          }
        } else {
          console.log("Missing moderators data:", { 
            hasUser: !!user, 
            hasModerators: !!communityData.moderators 
          });
          setIsModerator(false);
          setError('You do not have permission to access moderator tools for this community.');
        }
      } catch (err) {
        console.error('Failed to fetch community data:', err);
        setError('Failed to load community data. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    // Only run the check when auth state is settled and we have a user
    if (!isLoading && user) {
      checkModeratorStatus();
    }
  }, [communityName, user, isAuthenticated, isLoading]);

  // Always show loading while authentication is in progress or we haven't checked moderator status
  if (isLoading || loading) {
    console.log("Showing loading spinner:", { isLoading, loading });
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  // Only show error if we have an error message and are not still loading
  if (error && !loading) {
    console.log("Showing error message:", error);
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 p-4 rounded-md text-red-700 mb-4">
          <p className="font-medium">{error}</p>
        </div>
        <Link href={`/c/${communityName}`} className="text-red-600 hover:text-red-700 hover:underline transition-colors">
          Return to community
        </Link>
      </div>
    );
  }

  // Only show the "not a moderator" message if explicitly checked and determined not a mod
  if (isModerator === false && !loading && user) {
    console.log("Showing not a moderator message");
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 p-4 rounded-md text-red-700 mb-4">
          <p className="font-medium">You do not have permission to access moderator tools for this community.</p>
        </div>
        <Link href={`/c/${communityName}`} className="text-red-600 hover:text-red-700 hover:underline transition-colors">
          Return to community
        </Link>
      </div>
    );
  }

  // Only proceed to render content if user is confirmed as a moderator
  if (isModerator === true) {
    console.log("Rendering moderator interface");
    const isActive = (path) => pathname.includes(path);

    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar */}
          <div className="md:w-1/4">
            <div className="bg-white rounded-lg shadow-sm overflow-hidden mb-4 sticky top-16">
              <div className="px-4 py-3 bg-red-600 text-white">
                <h3 className="text-lg font-semibold">Moderator Tools</h3>
                <p className="text-sm opacity-80">c/{communityName}</p>
              </div>
              <div className="p-2">
                <nav className="space-y-1">
                  <Link 
                    href={`/c/${communityName}/mod/edit`}
                    className={`block px-3 py-2 rounded-md ${isActive('/mod/edit') 
                      ? 'bg-red-50 text-red-700 font-medium' 
                      : 'text-gray-700 hover:bg-gray-100'}`}
                  >
                    Edit Community
                  </Link>
                  <Link 
                    href={`/c/${communityName}/mod/reports`}
                    className={`block px-3 py-2 rounded-md ${isActive('/mod/reports') 
                      ? 'bg-red-50 text-red-700 font-medium' 
                      : 'text-gray-700 hover:bg-gray-100'}`}
                  >
                    Reports
                  </Link>
                  <Link 
                    href={`/c/${communityName}/mod/banned`}
                    className={`block px-3 py-2 rounded-md ${isActive('/mod/banned') 
                      ? 'bg-red-50 text-red-700 font-medium' 
                      : 'text-gray-700 hover:bg-gray-100'}`}
                  >
                    Banned Users
                  </Link>
                  <Link 
                    href={`/c/${communityName}/mod/members`}
                    className={`block px-3 py-2 rounded-md ${isActive('/mod/members') 
                      ? 'bg-red-50 text-red-700 font-medium' 
                      : 'text-gray-700 hover:bg-gray-100'}`}
                  >
                    Members
                  </Link>
                  <Link 
                    href={`/c/${communityName}/mod/moderators`}
                    className={`block px-3 py-2 rounded-md ${isActive('/mod/moderators') 
                      ? 'bg-red-50 text-red-700 font-medium' 
                      : 'text-gray-700 hover:bg-gray-100'}`}
                  >
                    Moderators
                  </Link>
                  <Link 
                    href={`/c/${communityName}/mod/rules`}
                    className={`block px-3 py-2 rounded-md ${isActive('/mod/rules') 
                      ? 'bg-red-50 text-red-700 font-medium' 
                      : 'text-gray-700 hover:bg-gray-100'}`}
                  >
                    Community Rules
                  </Link>
                </nav>
              </div>
            </div>
            <div className="hidden md:block">
              <Link 
                href={`/c/${communityName}`}
                className="text-gray-600 hover:text-red-600 text-sm flex items-center transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Community
              </Link>
            </div>
          </div>

          {/* Main Content */}
          <div className="md:w-3/4">
            {children}
          </div>
        </div>
      </div>
    );
  }
  
  // Fallback loading state if none of the other conditions match
  console.log("Fallback loading spinner");
  return (
    <div className="flex items-center justify-center min-h-screen">
      <Spinner size="lg" />
    </div>
  );
} 