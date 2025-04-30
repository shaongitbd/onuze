'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';

export default function ActivationPage() {
  const searchParams = useSearchParams();
  const status = searchParams.get('status');
  const error = searchParams.get('error');
  const [message, setMessage] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    if (status === 'success' && !error) {
      setIsSuccess(true);
      setMessage('Your account has been successfully activated! You can now log in.');
    } else if (error) {
      setIsSuccess(false);
      switch (error) {
        case 'invalid_token':
          setMessage('The activation link is invalid or has expired. Please request a new verification email.');
          break;
        case 'already_activated':
          setMessage('This account has already been activated. You can log in.');
          break;
        case 'user_not_found':
          setMessage('We couldn\'t find an account associated with this activation link.');
          break;
        default:
          setMessage('There was a problem activating your account. Please try again or contact support.');
      }
    } else {
      setIsSuccess(false);
      setMessage('Invalid activation request. Please use the link sent to your email.');
    }
  }, [status, error]);

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md border border-gray-200 my-10">
      <div className="text-center">
        {isSuccess ? (
          <FaCheckCircle className="mx-auto text-green-500 text-5xl mb-4" />
        ) : (
          <FaExclamationTriangle className="mx-auto text-red-500 text-5xl mb-4" />
        )}
        
        <h1 className="text-2xl font-bold mb-4 text-gray-900">
          {isSuccess ? 'Activation Successful' : 'Activation Failed'}
        </h1>
        
        <p className="text-gray-700 mb-6">
          {message}
        </p>
        
        <div className="flex flex-col space-y-3">
          {isSuccess ? (
            <Link 
              href="/login" 
              className="bg-green-600 text-white py-2 px-6 rounded-md hover:bg-green-700 transition font-medium"
            >
              Proceed to Login
            </Link>
          ) : (
            <>
              <Link 
                href="/login" 
                className="bg-gray-600 text-white py-2 px-6 rounded-md hover:bg-gray-700 transition font-medium"
              >
                Back to Login
              </Link>
              
              <Link 
                href="/register" 
                className="bg-red-600 text-white py-2 px-6 rounded-md hover:bg-red-700 transition font-medium"
              >
                Request New Activation Link
              </Link>
            </>
          )}
        </div>
        
        <p className="text-gray-500 text-sm mt-8">
          Need help? <Link href="/contact" className="text-red-600 hover:text-red-800 font-medium">Contact Support</Link>
        </p>
      </div>
    </div>
  );
} 