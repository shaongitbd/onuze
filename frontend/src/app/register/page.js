'use client'; // Needed for handling form state and interactions

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth';
import Link from 'next/link';
import Spinner from '@/components/Spinner';
import EmailVerification from '@/components/EmailVerification';

export default function RegisterPage() {
    const { register } = useAuth();
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [rePassword, setRePassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [registered, setRegistered] = useState(false);
    const [userUid, setUserUid] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (password !== rePassword) {
            setError('Passwords do not match.');
            return;
        }
        setError(null);
        setLoading(true);

        try {
            // Using the register function from auth context
            // Adding { noRedirect: true } to prevent automatic redirection
            const response = await register({
                username,
                email,
                password,
                re_password: rePassword  // API expects re_password (not rePassword)
            }, { noRedirect: true });
            
            // Save the uid from the response for email verification
            if (response && response.id) {
                setUserUid(response.id);
            } else if (response && response.user && response.user.id) {
                // Alternative: if uid is in a user object
                setUserUid(response.user.id.toString());
            } else {
                console.log('Registration response:', response);
            }
            
            // Set registered to true to show the verification component
            setRegistered(true);
        } catch (err) {
            console.error("Registration error:", err);
            
            // Handle various error formats from the API
            let errorMessage = '';
            if (err.data?.detail) {
                errorMessage = err.data.detail;
            } else if (err.data?.non_field_errors) {
                errorMessage = err.data.non_field_errors.join(' ');
            } else if (typeof err.data === 'object') {
                // Format field-specific errors
                errorMessage = Object.entries(err.data)
                    .map(([field, errors]) => {
                        if (Array.isArray(errors)) {
                            return `${field}: ${errors.join(' ')}`;
                        }
                        return `${field}: ${errors}`;
                    })
                    .join('; ');
            } else {
                errorMessage = err.message || 'Registration failed. Please try again.';
            }
            
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    // If registered, show the email verification component
    if (registered) {
        return (
            <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 py-8 bg-gray-50">
                <div className="w-full max-w-lg">
                    <EmailVerification 
                        email={email}
                        uid={userUid}
                        onResendSuccess={() => console.log('Verification email resent')}
                        onVerifySuccess={() => console.log('Email verified successfully')}
                    />
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 py-8 bg-gray-50">
            <div className="w-full max-w-md overflow-hidden bg-white rounded-lg shadow-md">
                <div className="px-6 py-4">
                    <h1 className="text-2xl font-bold text-center text-gray-800">Create Account</h1>
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
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm"
                            />
                        </div>
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                Email address
                            </label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
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
                                autoComplete="new-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-gray-500 focus:border-gray-500 sm:text-sm"
                            />
                        </div>
                        <div>
                            <label htmlFor="re_password" className="block text-sm font-medium text-gray-700">
                                Confirm Password
                            </label>
                            <input
                                id="re_password"
                                name="re_password"
                                type="password"
                                autoComplete="new-password"
                                required
                                value={rePassword}
                                onChange={(e) => setRePassword(e.target.value)}
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
                                {loading ? <Spinner /> : 'Sign Up'}
                            </button>
                        </div>
                    </form>
                    <p className="mt-4 text-sm text-center text-gray-600">
                        Already have an account?{' '}
                        <Link href="/login" className="font-medium text-red-500 hover:text-red-600 transition-colors">
                            Log In
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
} 