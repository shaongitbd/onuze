'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { FaKey, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';
import Spinner from '@/components/Spinner';
import { fetchAPI } from '@/lib/api';

export default function PasswordResetPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');
  const status = searchParams.get('status');
  
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Password validation
  const [passwordStrength, setPasswordStrength] = useState({
    isValid: false,
    message: ''
  });
  
  // Check if the reset token is valid
  const isValidResetRequest = uid && token && status === 'valid';
  
  // Password validation function
  const validatePassword = (pass) => {
    if (pass.length < 10) {
      return { isValid: false, message: 'Password must be at least 10 characters' };
    }
    if (!/[A-Z]/.test(pass)) {
      return { isValid: false, message: 'Password must contain at least one uppercase letter' };
    }
    if (!/[a-z]/.test(pass)) {
      return { isValid: false, message: 'Password must contain at least one lowercase letter' };
    }
    if (!/[0-9]/.test(pass)) {
      return { isValid: false, message: 'Password must contain at least one number' };
    }
    return { isValid: true, message: 'Password strength: Good' };
  };
  
  // Update password strength when password changes
  useEffect(() => {
    if (password) {
      setPasswordStrength(validatePassword(password));
    } else {
      setPasswordStrength({ isValid: false, message: '' });
    }
  }, [password]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset errors
    setError('');
    
    // Validate inputs
    if (!password || !passwordConfirm) {
      setError('Both password fields are required');
      return;
    }
    
    if (password !== passwordConfirm) {
      setError('Passwords do not match');
      return;
    }
    
    if (!passwordStrength.isValid) {
      setError(passwordStrength.message);
      return;
    }
    
    setLoading(true);
    
    try {
      // Submit password reset request to the correct endpoint
      await fetchAPI(`/users/password/reset/confirm/${uid}/${token}/`, {
        method: 'POST',
        body: JSON.stringify({
          new_password: password,
          confirm_password: passwordConfirm
        })
      });
      
      setSuccess(true);
      
      // Clear the form
      setPassword('');
      setPasswordConfirm('');
      
      // Redirect to login after success (with a delay for user to see success message)
      setTimeout(() => {
        router.push('/login');
      }, 3000);
      
    } catch (err) {
      console.error('Password reset error:', err);
      if (err.data?.new_password) {
        setError(err.data.new_password[0]);
      } else if (err.data?.non_field_errors) {
        setError(err.data.non_field_errors[0]);
      } else if (err.data?.token) {
        setError('Invalid or expired password reset token');
      } else {
        setError('Failed to reset password. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  // If token or uid is missing, show error
  if (!isValidResetRequest) {
    return (
      <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md border border-gray-200 my-10">
        <div className="text-center">
          <FaExclamationTriangle className="mx-auto text-red-500 text-5xl mb-4" />
          
          <h1 className="text-2xl font-bold mb-4 text-gray-900">
            Invalid Reset Link
          </h1>
          
          <p className="text-gray-700 mb-6">
            The password reset link is invalid or has expired. Please request a new password reset link.
          </p>
          
          <Link 
            href="/forgot-password" 
            className="bg-red-600 text-white py-2 px-6 rounded-md hover:bg-red-700 transition font-medium inline-block"
          >
            Request New Reset Link
          </Link>
          
          <p className="text-gray-500 text-sm mt-8">
            Remember your password? <Link href="/login" className="text-red-600 hover:text-red-800 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md border border-gray-200 my-10">
      <div className={`text-center ${success ? 'block' : 'hidden'}`}>
        <FaCheckCircle className="mx-auto text-green-500 text-5xl mb-4" />
        
        <h1 className="text-2xl font-bold mb-4 text-gray-900">
          Password Reset Complete
        </h1>
        
        <p className="text-gray-700 mb-6">
          Your password has been successfully reset. You will be redirected to the login page.
        </p>
        
        <Link 
          href="/login" 
          className="bg-green-600 text-white py-2 px-6 rounded-md hover:bg-green-700 transition font-medium inline-block"
        >
          Go to Login
        </Link>
      </div>
      
      <div className={`${success ? 'hidden' : 'block'}`}>
        <div className="text-center mb-6">
          <FaKey className="mx-auto text-red-500 text-4xl mb-4" />
          <h1 className="text-2xl font-bold text-gray-900">Reset Your Password</h1>
          <p className="text-gray-600 mt-2">Create a new password for your account</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              New Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
              placeholder="Enter new password"
            />
            {password && (
              <p className={`text-sm mt-1 ${passwordStrength.isValid ? 'text-green-600' : 'text-orange-500'}`}>
                {passwordStrength.message}
              </p>
            )}
          </div>
          
          <div>
            <label htmlFor="password-confirm" className="block text-sm font-medium text-gray-700 mb-1">
              Confirm New Password
            </label>
            <input
              id="password-confirm"
              type="password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
              placeholder="Confirm new password"
            />
            {passwordConfirm && password !== passwordConfirm && (
              <p className="text-sm mt-1 text-red-600">
                Passwords do not match
              </p>
            )}
          </div>
          
          <button
            type="submit"
            disabled={loading || !passwordStrength.isValid || password !== passwordConfirm}
            className="w-full bg-red-600 text-white py-3 px-4 rounded-md hover:bg-red-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed mt-4"
          >
            {loading ? <Spinner size="sm" /> : 'Reset Password'}
          </button>
        </form>
        
        <p className="text-gray-500 text-sm mt-8 text-center">
          Remember your password? <Link href="/login" className="text-red-600 hover:text-red-800 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  );
} 