'use client';

import React, { useEffect, useState, useContext } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { getSubreddits } from '@/lib/api';
import Spinner from './Spinner';
import { 
  HomeIcon, 
  FireIcon, 
  SparklesIcon, 
  GlobeAltIcon 
} from '@heroicons/react/24/outline';
import { PostFilterContext } from '@/app/layout';

export default function LeftSidebar({ onFilterChange }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const { filter } = useContext(PostFilterContext);
  const [communities, setCommunities] = useState([]);
  const [loadingCommunities, setLoadingCommunities] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated && user) {
      setLoadingCommunities(true);
      getSubreddits()
        .then(data => {
          if (data && Array.isArray(data.results)) {
            const joinedCommunities = data.results.filter(community => community.is_member === true);
            setCommunities(joinedCommunities);
          } else {
            setCommunities([]);
          }
          setError('');
        })
        .catch(err => {
          console.error("Error fetching user communities:", err);
          setError("Failed to load communities.");
          setCommunities([]);
        })
        .finally(() => {
          setLoadingCommunities(false);
        });
    } else {
      setCommunities([]);
    }
  }, [isAuthenticated, user]);

  const navItems = [
    { name: 'Home', filter: 'home', icon: HomeIcon },
    { name: 'Popular', filter: 'popular', icon: FireIcon },
    { name: 'New', filter: 'new', icon: SparklesIcon },
    { name: 'All', filter: 'all', icon: GlobeAltIcon },
  ];

  const handleNavClick = (filterValue) => {
    // Always update the filter state through the prop callback
    onFilterChange(filterValue);
    
    // Only navigate if we're not already on the home page
    if (pathname !== '/') {
      router.push('/');
    }
  };

  return (
    <div className="space-y-4 sticky top-[68px]">
      <div className="space-y-2">
        <h3 className="px-3 text-sm font-semibold text-gray-600 uppercase tracking-wider mb-1">
          Feeds
        </h3>
        <nav>
          <ul className="space-y-1">
            {navItems.map(item => {
              // Check if current item matches the active filter
              const isActive = item.filter === filter;
              
              return (
                <li key={item.name}>
                  <button
                    onClick={() => handleNavClick(item.filter)}
                    className={`flex items-center w-full text-left px-3 py-2 text-base font-medium rounded-md transition-colors ${ 
                      isActive 
                        ? 'bg-gray-200 text-gray-900' 
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <item.icon 
                      className={`mr-3 h-6 w-6 flex-shrink-0 ${ 
                        isActive ? 'text-gray-700' : 'text-gray-500 group-hover:text-gray-600' 
                      }`}
                      aria-hidden="true" 
                    />
                    {item.name}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>

      <hr className="border-gray-200" />

      {isAuthenticated && (
        <div className="space-y-2">
          <h3 className="px-3 text-sm font-semibold text-gray-600 uppercase tracking-wider mb-1">
            My Communities
          </h3>
          {isLoading || loadingCommunities ? (
            <div className="flex justify-center p-2">
              <Spinner size="sm" />
            </div>
          ) : error ? (
            <p className="px-3 text-sm text-red-600">{error}</p>
          ) : communities.length > 0 ? (
            <ul className="space-y-1">
              {communities.map(community => {
                const communityPath = `/c/${community.name}`;
                const isActive = pathname === communityPath;
                return (
                  <li key={community.id}>
                    <Link 
                      href={communityPath}
                      className={`flex items-center px-3 py-1.5 text-base rounded-md transition-colors ${ 
                        isActive 
                          ? 'bg-gray-200 text-gray-900 font-semibold'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                      }`}
                    >
                      <span className="w-5 h-5 mr-2 rounded-full bg-gray-300 text-xs font-bold flex items-center justify-center flex-shrink-0">
                        {community.name?.charAt(0).toUpperCase()}
                      </span>
                      <span className="truncate">
                        c/{community.name}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="px-3 text-sm text-gray-500">You haven't joined any communities yet.</p>
          )}
        </div>
      )}
    </div>
  );
} 