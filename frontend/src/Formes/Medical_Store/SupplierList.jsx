import React from "react";
import { FiEdit, FiTrash2 } from "react-icons/fi";

export default function SupplierList({
  suppliers,
  loading,
  onEdit,
  onDelete,
  onLink,
  onShowProducts,
}) {
  if (loading) return <p>Loading...</p>;

  if (!suppliers.length)
    return <p style={{ textAlign: "center" }}>No suppliers found.</p>;

  return (
    <section className="supplier-section supplier-list-section">
      <h2>Suppliers</h2>
      <table className="supplier-table">
        <thead>
          <tr>
            {[
              "Name",
              "Contact",
              "Phone",
              "Email",
              "City",
              "Pin",
              "Gender",
              "Age",
              "Actions",
            ].map((s) => (
              <th key={s}>{s}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {suppliers.map((s) => (
            <tr key={s.supplier_id}>
              <td>{s.supplier_name}</td>
              <td>{s.contact_name || "-"}</td>
              <td>{s.phone}</td>
              <td>{s.email || "-"}</td>
              <td>{s.city || "-"}</td>
              <td>{s.pin_code || "-"}</td>
              <td>{s.gender}</td>
              <td>{s.age || "-"}</td>
              <td>
                <button
                  className="icon-btn edit-btn"
                  onClick={() => onEdit(s)}
                  title="Edit Supplier"
                  aria-label="Edit Supplier"
                >
                  <FiEdit size={18} />
                </button>
                <button
                  className="icon-btn delete-btn"
                  onClick={() => onDelete(s.supplier_id)}
                  title="Delete Supplier"
                  aria-label="Delete Supplier"
                >
                  <FiTrash2 size={18} />
                </button>
                <button
                  className="link-btn interactive-btn"
                  onClick={() => onLink(s.supplier_id)}
                  title="Link to Store"
                  aria-label="Link Supplier to Store"
                >
                  Link to Store
                </button>
                <button
                  className="show-products-btn interactive-btn"
                  onClick={() => onShowProducts && onShowProducts(s)}
                  title="Show Products"
                  aria-label="Show Supplier Products"
                >
                  Show Products
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

