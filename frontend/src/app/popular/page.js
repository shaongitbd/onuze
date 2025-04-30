'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PostFilterContext } from '../layout';
import { useContext } from 'react';
import Spinner from '@/components/Spinner';

export default function PopularPage() {
  const router = useRouter();
  const { setFilter } = useContext(PostFilterContext);

  useEffect(() => {
    // Set the filter to popular 
    setFilter('popular');
    
    // Redirect to home page
    router.push('/');
  }, [router, setFilter]);

  return (
    <div className="flex justify-center items-center min-h-[50vh]">
      <Spinner size="lg" />
    </div>
  );
} 