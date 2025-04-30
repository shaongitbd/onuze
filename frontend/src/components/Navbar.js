'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import Spinner from './Spinner'; // Assuming Spinner component exists
import NotificationBadge from './NotificationBadge';

export default function Navbar() {
    const { user, logout, loading, isAuthenticated } = useAuth();
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState('');
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isMobileSearchOpen, setIsMobileSearchOpen] = useState(false);

    const handleSearch = (e) => {
        e.preventDefault();
        
        if (searchQuery.trim()) {
            router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
            setSearchQuery('');
            setIsMobileSearchOpen(false);
        }
    };

    const toggleUserMenu = () => {
        setIsUserMenuOpen(!isUserMenuOpen);
        // Close mobile menu if open
        if (isMobileMenuOpen) setIsMobileMenuOpen(false);
    };

    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen);
        // Close user menu if open
        if (isUserMenuOpen) setIsUserMenuOpen(false);
    };

    const toggleMobileSearch = () => {
        setIsMobileSearchOpen(!isMobileSearchOpen);
    };

    return (
        <nav className="bg-white shadow-md sticky top-0 z-50 border-b border-gray-200">
            <div className="max-w-[1670px] mx-auto px-4 sm:px-6 lg:px-8">
                {/* Mobile search bar - only shown when activated */}
                {isMobileSearchOpen && (
                    <div className="py-2 sm:hidden">
                        <form onSubmit={handleSearch} className="w-full">
                            <div className="relative flex items-center">
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search RedditClone..."
                                    className="w-full pl-10 pr-10 py-2 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 text-sm"
                                    autoFocus
                                />
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <button 
                                    type="button" 
                                    onClick={toggleMobileSearch} 
                                    className="absolute right-2 text-gray-500"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                <div className="flex items-center justify-between h-14">
                    {/* Left section - Logo and Mobile Menu Button */}
                    <div className="flex items-center">
                        <button 
                            className="inline-flex items-center justify-center p-2 rounded-md text-red-600 md:hidden" 
                            onClick={toggleMobileMenu}
                            aria-expanded={isMobileMenuOpen}
                        >
                            <span className="sr-only">Open main menu</span>
                            <svg 
                                className={`${isMobileMenuOpen ? 'hidden' : 'block'} h-6 w-6`} 
                                xmlns="http://www.w3.org/2000/svg" 
                                fill="none" 
                                viewBox="0 0 24 24" 
                                stroke="currentColor" 
                                aria-hidden="true"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                            <svg 
                                className={`${isMobileMenuOpen ? 'block' : 'hidden'} h-6 w-6`} 
                                xmlns="http://www.w3.org/2000/svg" 
                                fill="none" 
                                viewBox="0 0 24 24" 
                                stroke="currentColor" 
                                aria-hidden="true"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        
                        <Link href="/" className="text-xl md:text-2xl font-bold text-red-600 hover:text-red-700 transition-colors ml-2 md:ml-0">
                            RedditClone
                        </Link>
                    </div>
                    
                    {/* Center - Search Bar (hidden on mobile) */}
                    <div className="hidden md:block flex-grow max-w-md mx-4">
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
                    
                    {/* Right section */}
                    <div className="flex items-center">
                        {/* Mobile search icon */}
                        <button 
                            onClick={toggleMobileSearch}
                            className="md:hidden mr-2 p-2 text-red-500 hover:text-red-600 transition-colors"
                            aria-label="Search"
                        >
                            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                            </svg>
                        </button>
                    
                        {loading ? (
                            <Spinner />
                        ) : isAuthenticated ? (
                            <div className="flex items-center">
                                <Link href="/submit" className="hidden md:block mr-2 md:mr-4 bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                                    Create Post
                                </Link>

                                <NotificationBadge />
                                
                                {/* User menu */}
                                <div className="relative ml-2">
                                    <div>
                                        <button
                                            type="button"
                                            onClick={toggleUserMenu}
                                            className="flex items-center text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 rounded-full p-1"
                                            id="user-menu-button"
                                            aria-expanded={isUserMenuOpen}
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
                            <div className="flex items-center">
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

                {/* Mobile menu */}
                {isMobileMenuOpen && (
                    <div className="md:hidden py-3 border-t border-gray-200">
                        <div className="space-y-1 px-2">
                            {isAuthenticated && (
                                <>
                                    <Link
                                        href="/submit"
                                        onClick={() => setIsMobileMenuOpen(false)}
                                        className="block px-3 py-2 rounded-md text-base font-medium text-white bg-red-600 hover:bg-red-700 mb-2"
                                    >
                                        Create Post
                                    </Link>
                                    <Link
                                        href="/c/create"
                                        onClick={() => setIsMobileMenuOpen(false)}
                                        className="block px-3 py-2 rounded-md text-base font-medium text-white bg-blue-600 hover:bg-blue-700 mb-2"
                                    >
                                        Create Community
                                    </Link>
                                </>
                            )}
                            <Link
                                href="/"
                                onClick={() => setIsMobileMenuOpen(false)}
                                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-red-600 hover:bg-gray-50"
                            >
                                Home
                            </Link>
                            <Link
                                href="/popular"
                                onClick={() => setIsMobileMenuOpen(false)}
                                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-red-600 hover:bg-gray-50"
                            >
                                Popular
                            </Link>
                            <Link
                                href="/all"
                                onClick={() => setIsMobileMenuOpen(false)}
                                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-red-600 hover:bg-gray-50"
                            >
                                All
                            </Link>
                        </div>
                    </div>
                )}
            </div>
        </nav>
    );
} 