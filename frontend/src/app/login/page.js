'use client'; // Needed for handling form state and interactions

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth';
import Link from 'next/link';
import Spinner from '@/components/Spinner';
import EmailVerification from '@/components/EmailVerification';

export default function LoginPage() {
    const { login } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [needsVerification, setNeedsVerification] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            await login({
                username,
                password
            });
            // If successful, the login function in auth.js will redirect
        } catch (err) {
            console.error("Login error:", err);
            
            // Check for unverified email error message
            const errorMessage = err.data?.detail || err.message || 'Login failed';
            
            // If the error indicates unverified email
            if (errorMessage.toLowerCase().includes('email is not verified') || 
                errorMessage.toLowerCase().includes('account not activated') ||
                errorMessage.toLowerCase().includes('verify your email')) {
                
                // Set email for verification component (assuming it's the same as username for email logins)
                setEmail(username.includes('@') ? username : '');
                setNeedsVerification(true);
            } else {
                // For other errors, display the message normally
                setError(errorMessage);
            }
        } finally {
            setLoading(false);
        }
    };

    // If the user needs to verify their email
    if (needsVerification) {
        return (
            <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 py-8 bg-gray-50">
                <div className="w-full max-w-lg">
                    <div className="bg-white p-6 rounded-lg shadow-md">
                        <h2 className="text-xl font-semibold text-center mb-4">Email Verification Required</h2>
                        
                        <div className="bg-amber-50 border border-amber-200 rounded-md p-4 mb-6">
                            <p className="text-amber-700">
                                Your account has not been verified yet. Please check your email for a verification code
                                or request a new one.
                            </p>
                        </div>
                        
                        {!email && (
                            <div className="mb-6">
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="Enter your email address"
                                    required
                                />
                                <p className="text-sm text-gray-500 mt-1">
                                    Please enter the email address you used during registration.
                                </p>
                            </div>
                        )}
                        
                        {email && (
                            <div className="mt-4">
                                <EmailVerification 
                                    email={email}
                                    onResendSuccess={() => console.log('Verification email resent')}
                                    onVerifySuccess={() => console.log('Email verified successfully')}
                                />
                            </div>
                        )}
                        
                        <div className="mt-6 text-center">
                            <button
                                onClick={() => setNeedsVerification(false)}
                                className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                            >
                                Return to Login
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 py-8 bg-gray-50">
            <div className="w-full max-w-md overflow-hidden bg-white rounded-lg shadow-md">
                <div className="px-6 py-4">
                    <h1 className="text-2xl font-bold text-center text-gray-800">Welcome Back</h1>
                </div>
                <div className="p-6 space-y-6">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                                Username or Email
                            </label>
                            <input
                                id="username"
                                name="username"
                                type="text"
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
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm"
                            />
                        </div>

                        {error && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                                <p className="text-sm text-red-600 text-center">{error}</p>
                            </div>
                        )}

                        <div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
                            >
                                {loading ? <Spinner /> : 'Sign In'}
                            </button>
                        </div>
                    </form>
                    
                    <div className="mt-4 text-sm text-center">
                        <Link href="/forgot-password" className="font-medium text-red-500 hover:text-red-600 transition-colors">
                            Forgot password?
                        </Link>
                    </div>
                    
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