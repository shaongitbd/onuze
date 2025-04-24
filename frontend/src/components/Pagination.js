import React from 'react';

/**
 * Reusable pagination component
 * @param {Object} props
 * @param {number} props.currentPage - Current active page (1-based)
 * @param {number} props.totalPages - Total number of pages
 * @param {function} props.onPageChange - Function to call when page changes
 * @param {boolean} props.loading - Whether data is currently loading
 * @param {string} props.className - Additional CSS classes
 */
const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange, 
  loading = false,
  className = '' 
}) => {
  // Don't render pagination if there's only one page
  if (totalPages <= 1) return null;

  // Calculate range of page numbers to show
  const getPageNumbers = () => {
    const pageNumbers = [];
    const maxPagesToShow = 5; // Show at most 5 page numbers
    
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = startPage + maxPagesToShow - 1;
    
    if (endPage > totalPages) {
      endPage = totalPages;
      startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }
    
    return pageNumbers;
  };

  const handlePrevious = () => {
    if (currentPage > 1 && !loading) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages && !loading) {
      onPageChange(currentPage + 1);
    }
  };

  return (
    <div className={`flex items-center justify-center my-6 ${className}`}>
      <nav className="inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
        {/* Previous Page Button */}
        <button
          onClick={handlePrevious}
          disabled={currentPage === 1 || loading}
          className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${
            currentPage === 1 || loading
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-500 hover:bg-gray-50'
          }`}
        >
          <span className="sr-only">Previous</span>
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </button>

        {/* First Page */}
        {getPageNumbers()[0] > 1 && (
          <>
            <button
              onClick={() => onPageChange(1)}
              disabled={loading}
              className={`relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium ${
                loading ? 'text-gray-300 cursor-not-allowed' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              1
            </button>
            {getPageNumbers()[0] > 2 && (
              <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                ...
              </span>
            )}
          </>
        )}

        {/* Page Numbers */}
        {getPageNumbers().map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            disabled={loading}
            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
              page === currentPage
                ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                : loading
                ? 'border-gray-300 bg-white text-gray-300 cursor-not-allowed'
                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {page}
          </button>
        ))}

        {/* Last Page */}
        {getPageNumbers()[getPageNumbers().length - 1] < totalPages && (
          <>
            {getPageNumbers()[getPageNumbers().length - 1] < totalPages - 1 && (
              <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                ...
              </span>
            )}
            <button
              onClick={() => onPageChange(totalPages)}
              disabled={loading}
              className={`relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium ${
                loading ? 'text-gray-300 cursor-not-allowed' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              {totalPages}
            </button>
          </>
        )}

        {/* Next Page Button */}
        <button
          onClick={handleNext}
          disabled={currentPage === totalPages || loading}
          className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${
            currentPage === totalPages || loading
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-500 hover:bg-gray-50'
          }`}
        >
          <span className="sr-only">Next</span>
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        </button>
      </nav>
    </div>
  );
};

export default Pagination; 