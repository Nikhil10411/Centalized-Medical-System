import React from 'react';

export default function Pagination({ page, totalPages, onPageChange }) {
  return (
    <div className="pagination-controls">
      <button onClick={() => onPageChange(page -1)} disabled={page <= 1}>Previous</button>
      <span>Page {page} / {totalPages}</span>
      <button onClick={() => onPageChange(page +1)} disabled={page >= totalPages}>Next</button>
    </div>
  );
}
