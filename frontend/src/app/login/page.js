'use client'; // Needed for handling form state and interactions

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth';
import Link from 'next/link';
import Spinner from '@/components/Spinner';

export default function LoginPage() {
    const { login } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            // Using username as the identifier based on API documentation
            await login({ username, password });
            // Redirect handled by useAuth hook
        } catch (err) {
            // Assuming err.data contains backend error details
            console.error("Login error:", err);
            
            let errorMessage = '';
            
            // Handle various error formats from the API
            if (err.data?.detail) {
                errorMessage = err.data.detail;
            } else if (err.data?.non_field_errors) {
                errorMessage = err.data.non_field_errors.join(' ');
            } else if (typeof err.data === 'object') {
                errorMessage = Object.entries(err.data)
                    .map(([field, errors]) => {
                        if (Array.isArray(errors)) {
                            return `${field}: ${errors.join(' ')}`;
                        }
                        return `${field}: ${errors}`;
                    })
                    .join('; ');
            } else {
                errorMessage = err.message || 'Login failed. Please check your credentials.';
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 py-8 bg-gray-50"> 
            <div className="w-full max-w-md overflow-hidden bg-white rounded-lg shadow-md">
                <div className="px-6 py-4">
                    <h1 className="text-2xl font-bold text-center text-gray-800">Log In to RedditClone</h1>
                </div>
                <div className="p-6 space-y-6">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                                Username
                            </label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                autoComplete="username"
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm"
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm"
                            />
                        </div>

                        {error && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                                <p className="text-sm text-red-600 text-center whitespace-pre-wrap">{error}</p>
                            </div>
                        )}

                        <div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
                            >
                                {loading ? <Spinner /> : 'Log In'}
                            </button>
                        </div>
                    </form>
                    <p className="mt-4 text-sm text-center text-gray-600">
                        Don't have an account?{' '}
                        <Link href="/register" className="font-medium text-red-500 hover:text-red-600 transition-colors">
                            Sign Up
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
} 