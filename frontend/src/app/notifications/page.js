'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import NotificationsList from '@/components/NotificationsList';
import Spinner from '@/components/Spinner';

export default function NotificationsPage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  
  // Redirect to login if user is not authenticated
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login?next=/notifications');
    }
  }, [isAuthenticated, loading, router]);

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-64px)]">
        <Spinner />
      </div>
    );
  }

  // Don't render anything if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }
  
  return (
    <div className="max-w-3xl mx-auto py-8 px-4 sm:px-6">
      <h1 className="text-2xl font-bold mb-6">Your Notifications</h1>
      <NotificationsList />
    </div>
  );
} 