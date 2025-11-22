import React, { useState, useEffect } from "react";
import axios from "axios";
import Notification from "../../Notification/Notification";
import { useNavigate, useLocation } from "react-router-dom";
import styles from "./CustomerManagement.module.css";

const API_BASE = "http://localhost:8000/api/medical_store";

const emptyCustomer = {
  name: "",
  phone: "",
  email: "",
  address: "",
  age: "",
  gender: "",
};

export default function CustomerManagement() {
  const [customers, setCustomers] = useState([]);
  const [formData, setFormData] = useState(emptyCustomer);
  const [searchData, setSearchData] = useState(emptyCustomer);
  const [editing, setEditing] = useState(null);
  const [editForm, setEditForm] = useState(emptyCustomer);
  const [notification, setNotification] = useState({ message: "", type: "" });
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchCustomers();
  }, []);

  // Sanitize and normalize customer data before sending to backend
  function sanitizeCustomerData(data) {
    const genderMap = {
      MALE: "Male",
      FEMALE: "Female",
      OTHER: "Other",
      male: "male",
      female: "female",
      other: "other",
    };
    return {
      ...data,
      age: data.age === "" ? null : Number(data.age),
      gender: data.gender === "" ? null : genderMap[data.gender] || data.gender,
    };
  }

  async function fetchCustomers(params = {}) {
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const query = Object.fromEntries(Object.entries(params).filter(([_, v]) => v));
      const res = await axios.get(`${API_BASE}/customers/find/`, {
        params: query,
        headers: { Authorization: `Bearer ${token}` },
      });
      setCustomers(Array.isArray(res.data.items) ? res.data.items : []);
      setNotification({ message: "Customers loaded!", type: "success" });
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login", { state: { from: location } });
      } else {
        setCustomers([]);
        setNotification({ message: err?.response?.data?.detail || "Load failed", type: "error" });
      }
    }
    setLoading(false);
  }

  async function handleCreate(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const dataToSend = sanitizeCustomerData(formData);
      await axios.post(`${API_BASE}/customers`, dataToSend, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotification({ message: "Customer added!", type: "success" });
      setFormData(emptyCustomer);
      fetchCustomers();
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login", { state: { from: location } });
      } else if (err.response && err.response.status === 422) {
        const errors = err.response.data.detail || [];
        const message = errors.map((e) => `${e.loc.join(" -> ")}: ${e.msg}`).join(", ");
        setNotification({ message: `Validation failed: ${message}`, type: "error" });
      } else {
        setNotification({ message: err.response?.data?.detail || "Create failed", type: "error" });
      }
    }
    setLoading(false);
  }

  function handleSearch(e) {
    e.preventDefault();
    fetchCustomers(searchData);
  }

  function startEdit(customer) {
    setEditing(customer.customer_id);
    setEditForm({ ...customer });
  }

  async function handleEdit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const encodedName = encodeURIComponent(editForm.name);
      const dataToSend = sanitizeCustomerData(editForm);
      await axios.put(`${API_BASE}/customers/update/${encodedName}`, dataToSend, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotification({ message: "Customer updated!", type: "success" });
      setEditing(null);
      fetchCustomers();
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login", { state: { from: location } });
      } else if (err.response && err.response.status === 422) {
        const errors = err.response.data.detail || [];
        const message = errors.map((e) => `${e.loc.join(" -> ")}: ${e.msg}`).join(", ");
        setNotification({ message: `Validation failed: ${message}`, type: "error" });
      } else {
        setNotification({ message: err.response?.data?.detail || "Update failed", type: "error" });
      }
    }
    setLoading(false);
  }

  async function handleDelete(customer) {
    if (!window.confirm(`Delete ${customer.name}?`)) return;
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      await axios.delete(`${API_BASE}/customers/delete/`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          name: customer.name,
          phone: customer.phone,
          email: customer.email,
          address: customer.address,
        },
      });
      setNotification({ message: "Customer deleted!", type: "success" });
      fetchCustomers();
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login", { state: { from: location } });
      } else {
        setNotification({ message: "Delete failed", type: "error" });
      }
    }
    setLoading(false);
  }

  return (
    <div className={styles.container}>
      <Notification message={notification.message} type={notification.type} onClose={() => setNotification({ message: "", type: "" })} />
      <h1 className={styles.head}>Customer Management</h1>

      <section className={styles.section}>
        <h2>Create Customer</h2>
        <form onSubmit={handleCreate} className={styles.grid}>
          <input name="name" placeholder="Name" required value={formData.name} onChange={(e) => setFormData((f) => ({ ...f, name: e.target.value }))} />
          <input name="phone" placeholder="Phone" required value={formData.phone} onChange={(e) => setFormData((f) => ({ ...f, phone: e.target.value }))} />
          <input name="email" placeholder="Email" value={formData.email} onChange={(e) => setFormData((f) => ({ ...f, email: e.target.value }))} />
          <input name="address" placeholder="Address" value={formData.address} onChange={(e) => setFormData((f) => ({ ...f, address: e.target.value }))} />
          <input name="age" type="number" placeholder="Age" min="0" value={formData.age} onChange={(e) => setFormData((f) => ({ ...f, age: e.target.value }))} />
          <select name="gender" value={formData.gender} onChange={(e) => setFormData((f) => ({ ...f, gender: e.target.value }))}>
            <option value="">Gender</option>
            <option value="MALE">Male</option>
            <option value="FEMALE">Female</option>
            <option value="OTHER">Other</option>
          </select>
          <button type="submit" disabled={loading}>Add</button>
        </form>
      </section>

      <section className={styles.section}>
        <h2>Search Customers</h2>
        <form onSubmit={handleSearch} className={styles.grid}>
          <input name="name" placeholder="Name" value={searchData.name} onChange={(e) => setSearchData((f) => ({ ...f, name: e.target.value }))} />
          <input name="phone" placeholder="Phone" value={searchData.phone} onChange={(e) => setSearchData((f) => ({ ...f, phone: e.target.value }))} />
          <input name="email" placeholder="Email" value={searchData.email} onChange={(e) => setSearchData((f) => ({ ...f, email: e.target.value }))} />
          <input name="address" placeholder="Address" value={searchData.address} onChange={(e) => setSearchData((f) => ({ ...f, address: e.target.value }))} />
          <button type="submit" disabled={loading}>Search</button>
        </form>
      </section>

      <section className={styles.section}>
        <h2>Customer List</h2>
        {loading ? <p>Loading...</p> : customers.length === 0 ? <p>No customers found.</p> : (
          <table className={styles.table}>
            <thead>
              <tr><th>Name</th><th>Phone</th><th>Email</th><th>Address</th><th>Age</th><th>Gender</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {customers.map(c => (
                <tr key={c.customer_id}>
                  <td>{c.name}</td>
                  <td>{c.phone}</td>
                  <td>{c.email || "-"}</td>
                  <td>{c.address || "-"}</td>
                  <td>{c.age || "-"}</td>
                  <td>{c.gender || "-"}</td>
                  <td>
                    <button className={styles.action} onClick={() => startEdit(c)}>Edit</button>
                    <button className={styles.delete} onClick={() => handleDelete(c)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {editing && (
        <div className={styles.modal}>
          <div className={styles.modalcontent}>
            <h2>Edit Customer</h2>
            <form onSubmit={handleEdit} className={styles.grid}>
              <input name="name" placeholder="Name" value={editForm.name} required onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} />
              <input name="phone" placeholder="Phone" value={editForm.phone} required onChange={e => setEditForm(f => ({ ...f, phone: e.target.value }))} />
              <input name="email" placeholder="Email" value={editForm.email} onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))} />
              <input name="address" placeholder="Address" value={editForm.address} onChange={e => setEditForm(f => ({ ...f, address: e.target.value }))} />
              <input name="age" type="number" placeholder="Age" min="0" value={editForm.age} onChange={e => setEditForm(f => ({ ...f, age: e.target.value }))} />
              <select name="gender" value={editForm.gender} onChange={e => setEditForm(f => ({ ...f, gender: e.target.value }))}>
                <option value="">Gender</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
              <button type="submit" disabled={loading}>Update</button>
              <button className={styles.cancel} onClick={() => setEditing(null)} type="button">Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
