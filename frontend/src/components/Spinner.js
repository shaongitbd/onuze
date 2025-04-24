import React from 'react';

// A simple loading spinner using Tailwind CSS
export default function Spinner({ size = 'md' }) {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12'
    };
    
    return (
        <div className="flex justify-center items-center">
            <div 
                className={`${sizeClasses[size]} border-4 border-gray-200 border-t-red-600 rounded-full animate-spin`} 
                role="status" 
                aria-label="Loading"
            />
        </div>
    );
} 