import React from 'react';

export default function SupplierSearch({ search, onChange, onSearch, onClear, onToggleView, showAll }) {
  return (
    <section className="supplier-section supplier-search-section">
      <h2>Search Suppliers</h2>
      <form onSubmit={onSearch} className="supplier-search-form">
        {["supplier_name","contact_name","phone","email","city","pin_code","address"].map(field => (
          <input
            key={field}
            name={field}
            placeholder={field.replace("_", " ").toUpperCase()}
            value={search[field] || ""}
            onChange={onChange}
          />
        ))}
        <button type="submit">Search</button>
        <button type="button" onClick={onClear}>Clear</button>
      </form>
      <div className="toggle-list-view">
        <button onClick={() => onToggleView(true)} disabled={showAll}>Show All</button>
        <button onClick={() => onToggleView(false)} disabled={!showAll}>Paginated</button>
      </div>
    </section>
  );
}
