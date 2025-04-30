'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { FaEnvelope, FaCheckCircle } from 'react-icons/fa';
import Spinner from '@/components/Spinner';
import { fetchAPI } from '@/lib/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset error
    setError('');
    
    // Validate email
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setLoading(true);
    
    try {
      // Call the API to request password reset
      await fetchAPI('/auth/users/reset_password/', {
        method: 'POST',
        body: JSON.stringify({ email:email })
      });
      
      // Show success message
      setSuccess(true);
      
      // Clear the form
      setEmail('');
      
    } catch (err) {
      console.error('Password reset request error:', err);
      if (err.data?.email) {
        setError(err.data.email[0]);
      } else if (err.data?.non_field_errors) {
        setError(err.data.non_field_errors[0]);
      } else {
        setError('Something went wrong. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md border border-gray-200 my-10">
      {success ? (
        <div className="text-center">
          <FaCheckCircle className="mx-auto text-green-500 text-5xl mb-4" />
          
          <h1 className="text-2xl font-bold mb-4 text-gray-900">
            Reset Link Sent
          </h1>
          
          <p className="text-gray-700 mb-6">
            If an account exists with the email you provided, we've sent instructions for resetting your password.
            Please check your inbox and spam folder.
          </p>
          
          <Link 
            href="/login" 
            className="bg-red-600 text-white py-2 px-6 rounded-md hover:bg-red-700 transition font-medium inline-block"
          >
            Back to Login
          </Link>
        </div>
      ) : (
        <>
          <div className="text-center mb-6">
            <FaEnvelope className="mx-auto text-red-500 text-4xl mb-4" />
            <h1 className="text-2xl font-bold text-gray-900">Forgot Your Password?</h1>
            <p className="text-gray-600 mt-2">
              Enter your email and we'll send you a link to reset your password
            </p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
            
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="Enter your email address"
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-red-600 text-white py-3 px-4 rounded-md hover:bg-red-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed mt-4"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <Spinner size="sm" />
                  <span className="ml-2">Sending...</span>
                </span>
              ) : (
                'Send Reset Link'
              )}
            </button>
          </form>
          
          <p className="text-gray-500 text-sm mt-8 text-center">
            Remember your password? <Link href="/login" className="text-red-600 hover:text-red-800 font-medium">Sign in</Link>
          </p>
        </>
      )}
    </div>
  );
} 