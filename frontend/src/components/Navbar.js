'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import Spinner from './Spinner'; // Assuming Spinner component exists

export default function Navbar() {
    const { user, logout, loading, isAuthenticated } = useAuth();
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState('');
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

    const handleSearch = (e) => {
        e.preventDefault();
        
        if (searchQuery.trim()) {
            router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
            setSearchQuery('');
        }
    };

    const toggleUserMenu = () => {
        setIsUserMenuOpen(!isUserMenuOpen);
    };

    return (
        <nav className="bg-white shadow-md sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <div className="flex-shrink-0 mr-4">
                            <Link href="/" className="text-2xl font-bold text-red-600 hover:text-red-700 transition-colors">
                                RedditClone
                            </Link>
                        </div>
                        <div className="hidden md:block ml-4">
                            <Link href="/r" className="text-gray-500 hover:text-red-600 px-3 py-2 rounded-md text-sm font-medium">
                                Communities
                            </Link>
                        </div>
                    </div>
                    
                    {/* Search Bar */}
                    <div className="flex-1 max-w-md mx-4 hidden sm:flex">
                        <form onSubmit={handleSearch} className="w-full">
                            <div className="relative">
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search RedditClone..."
                                    className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 text-sm transition-all hover:bg-white hover:border-gray-300"
                                />
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                                    </svg>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    {/* Small screen search icon */}
                    <Link href="/search" className="sm:hidden mr-4 text-red-500 hover:text-red-600 transition-colors">
                        <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                        </svg>
                    </Link>
                    
                    <div className="flex items-center">
                        {loading ? (
                            <Spinner />
                        ) : isAuthenticated ? (
                            <div className="flex items-center">
                                <Link href="/submit" className="mr-4 bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                                    Create Post
                                </Link>
                                
                                {/* User menu */}
                                <div className="relative ml-3">
                                    <div>
                                        <button
                                            type="button"
                                            onClick={toggleUserMenu}
                                            className="flex items-center text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 rounded-full"
                                            id="user-menu-button"
                                        >
                                            <span className="sr-only">Open user menu</span>
                                            {user?.profile_image ? (
                                                <img
                                                    className="h-8 w-8 rounded-full"
                                                    src={user.profile_image}
                                                    alt={`${user.username}'s profile`}
                                                />
                                            ) : (
                                                <div className="h-8 w-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-medium">
                                                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                                                </div>
                                            )}
                                        </button>
                                    </div>
                                    
                                    {/* Dropdown menu */}
                                    {isUserMenuOpen && (
                                        <div
                                            className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                                            role="menu"
                                            aria-orientation="vertical"
                                            aria-labelledby="user-menu-button"
                                        >
                                            <Link
                                                href={`/user/${user.username}`}
                                                onClick={() => setIsUserMenuOpen(false)}
                                                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                                role="menuitem"
                                            >
                                                Your Profile
                                            </Link>
                                            <Link
                                                href="/settings"
                                                onClick={() => setIsUserMenuOpen(false)}
                                                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                                role="menuitem"
                                            >
                                                Settings
                                            </Link>
                                            <Link
                                                href="/c/create"
                                                onClick={() => setIsUserMenuOpen(false)}
                                                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                                role="menuitem"
                                            >
                                                Create Community
                                            </Link>
                                            <button
                                                onClick={() => {
                                                    setIsUserMenuOpen(false);
                                                    logout();
                                                }}
                                                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                                role="menuitem"
                                            >
                                                Sign out
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="flex space-x-4">
                                <Link href="/login" className="text-gray-700 hover:text-red-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                                    Log In
                                </Link>
                                <Link href="/register" className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                                    Sign Up
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
} 