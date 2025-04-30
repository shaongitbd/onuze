import React, { useState } from 'react';
import Link from 'next/link';
import Spinner from '@/components/Spinner';
import { fetchAPI } from '@/lib/api';

const EmailVerification = ({ email, uid, onResendSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  const handleResendCode = async () => {
    setResendLoading(true);
    setError(null);
    
    try {
      // Call the API to resend verification email using the correct Djoser endpoint
      await fetchAPI('/auth/users/resend_activation/', {
        method: 'POST',
        body: JSON.stringify({ email })
      });
      
      setResendSuccess(true);
      
      // Notify parent component if needed
      if (onResendSuccess) {
        onResendSuccess();
      }
    } catch (err) {
      console.error('Resend verification error:', err);
      setError(err.data?.detail || 'Failed to resend verification email. Please try again later.');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md border border-gray-200">
      <h2 className="text-2xl font-bold text-center mb-6 text-gray-900">Verify Your Email</h2>
      
      <div className="text-gray-700 mb-8 text-center space-y-3">
        <p>
          We've sent a verification link to <span className="font-semibold">{email}</span>.
        </p>
        <p>
          Please check your inbox (and spam folder) and click on the link to activate your account.
        </p>
      </div>
      
      <div className="space-y-5">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        
        {resendSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <p className="text-green-700">Verification email has been resent!</p>
          </div>
        )}
        
        <div className="flex justify-center mt-6">
          <button
            type="button"
            onClick={handleResendCode}
            disabled={resendLoading || resendSuccess}
            className="bg-red-600 text-white py-2 px-6 rounded-md hover:bg-red-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {resendLoading ? (
              <span className="flex items-center justify-center gap-2">
                <Spinner size="sm" /> Sending...
              </span>
            ) : (
              'Resend Verification Email'
            )}
          </button>
        </div>
      </div>
      
      <p className="text-gray-500 text-sm mt-8 text-center">
        Need help? <Link href="/contact" className="text-red-600 hover:text-red-800 font-medium">Contact Support </Link>
      </p>
    </div>
  );
};

export default EmailVerification; 