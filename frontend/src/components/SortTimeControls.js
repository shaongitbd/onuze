'use client';

import React from 'react';

const SortTimeControls = ({ sort, setSort, time, setTime, showPinned, setShowPinned }) => {
  const sortOptions = [
    { value: 'new', label: 'New' },
    { value: 'hot', label: 'Hot' },
    { value: 'top', label: 'Top' },
    { value: 'controversial', label: 'Controversial' },
    // Add 'top' if your API supports it
  ];

  const timeOptions = [
    { value: 'day', label: 'Past 24 Hours' },
    { value: 'week', label: 'Past Week' },
    { value: 'month', label: 'Past Month' },
    { value: 'year', label: 'Past Year' },
    { value: 'all', label: 'All Time' }, // Assuming 'all' or empty string for all time
  ];

  const handleSortChange = (e) => {
    const newSort = e.target.value;
    setSort(newSort);
    // Reset time filter when changing to 'new' or 'hot' as it's usually not applicable
    if (newSort === 'new' || newSort === 'hot') {
      setTime('');
    }
  };

  const handleTimeChange = (e) => {
    setTime(e.target.value === 'all' ? '' : e.target.value);
  };

  const handleShowPinnedChange = (e) => {
    setShowPinned(e.target.checked);
  };

  const showTimeFilter = sort === 'controversial' || sort === 'top'; // Show time filter only for relevant sorts

  return (
    <div className="flex flex-wrap items-center gap-4 bg-gray-100 p-3 rounded-md mb-4">
      {/* Sort Dropdown */}
      <div>
        <label htmlFor="sort-select" className="sr-only">Sort by:</label>
        <select 
          id="sort-select"
          value={sort}
          onChange={handleSortChange}
          className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
        >
          {sortOptions.map(option => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      {/* Time Dropdown (conditionally rendered) */}
      {showTimeFilter && (
        <div>
          <label htmlFor="time-select" className="sr-only">Timeframe:</label>
          <select 
            id="time-select"
            value={time || 'all'} // Use 'all' if time is empty
            onChange={handleTimeChange}
            className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          >
            {timeOptions.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
      )}

      {/* Pinned Posts Checkbox */}
      {setShowPinned && (
        <div className="flex items-center">
          <input
            id="pinned-checkbox"
            type="checkbox"
            checked={showPinned}
            onChange={handleShowPinnedChange}
            className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
          />
          <label htmlFor="pinned-checkbox" className="ml-2 text-sm text-gray-700">
            Pinned Posts
          </label>
        </div>
      )}
    </div>
  );
};

export default SortTimeControls; 