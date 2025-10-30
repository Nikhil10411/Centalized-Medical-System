import React from 'react';

export default function SupplierForm({ form, onChange, onSubmit, onCancel, editing }) {
  return (
    <section className="supplier-section supplier-form-section">
      <h2>{editing ? "Edit Supplier" : "Add Supplier"}</h2>
      <form onSubmit={onSubmit} className="supplier-form">
        <input required name="supplier_name" placeholder="Supplier Name" value={form.supplier_name} onChange={onChange} />
        <input name="contact_name" placeholder="Contact Name" value={form.contact_name} onChange={onChange} />
        <input required name="phone" placeholder="Phone" value={form.phone} onChange={onChange} />
        <input name="email" placeholder="Email" type="email" value={form.email} onChange={onChange} />
        <input name="address" placeholder="Address" value={form.address} onChange={onChange} />
        <input name="city" placeholder="City" value={form.city} onChange={onChange} />
        <input name="pin_code" placeholder="Pin Code" value={form.pin_code} onChange={onChange} />
        <input name="age" type="number" min="0" placeholder="Age" value={form.age} onChange={onChange} />
        <select name="gender" value={form.gender} onChange={onChange}>
          <option value="">Gender</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
        <button type="submit">{editing ? "Update" : "Add"}</button>
        {editing && (
          <button type="button" className="cancel-btn" onClick={onCancel}>Cancel</button>
        )}
      </form>
    </section>
  );
}
