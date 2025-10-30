import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import Notification from "../../Notification/Notification";
import "./InventoryManagement.css";

export default function InventoryManager() {
  const [inventory, setInventory] = useState([]);
  const [form, setForm] = useState({
    product_name: "",
    brand: "",
    dosage: "",
    form: "",
    category: "",
    batch_no: "",
    expiry_date: "",
    quantity: "",
    price: "",
  });
  const [mode, setMode] = useState("view"); // view, add, update
  const [search, setSearch] = useState({
    product_name: "",
    batch_no: "",
    brand: "",
    generic_name: "",
    dosage: "",
    form: "",
    category: "",
  });
  const [notification, setNotification] = useState({
    show: false,
    type: "error",
    message: "",
  });
  const notificationTimer = useRef();
  const navigate = useNavigate();
  const location = useLocation();

  const getAuthHeaders = () => {
    const token = localStorage.getItem("access_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const showNotification = (type, message) => {
    setNotification({ show: true, type, message });
    clearTimeout(notificationTimer.current);
    notificationTimer.current = setTimeout(() => {
      setNotification((n) => ({ ...n, show: false }));
    }, 8000);
  };

  const handleAuthError = () => {
    showNotification("error", "Unauthorized access. Please log in.");
    setTimeout(() => {
      navigate("/auth", { state: { from: location.pathname } });
    }, 1100);
  };

  // ----------------- Fetch Inventory -----------------
  const fetchInventory = async () => {
    try {
      const res = await axios.get(
        "http://127.0.0.1:8000/medical_store/inventory/all",
        { headers: getAuthHeaders() }
      );
      const data = Array.isArray(res.data) ? res.data : res.data.data || [];
      setInventory(data);
    } catch (error) {
      if (error.response?.status === 401) handleAuthError();
      else
        showNotification(
          "error",
          error.response?.data?.detail || error.message || "Failed to load inventory"
        );
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  // ----------------- Form Handlers -----------------
  const handleFormInput = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const handleSearchInput = (e) => setSearch({ ...search, [e.target.name]: e.target.value });

  // ----------------- Search Inventory -----------------
  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      const params = {};
      Object.entries(search).forEach(([k, v]) => { if (v) params[k] = v; });
      const res = await axios.get(
        "http://127.0.0.1:8000/medical_store/inventory/search",
        { params, headers: getAuthHeaders() }
      );
      const data = Array.isArray(res.data) ? res.data : res.data.data || [];
      setInventory(data);
      if (data.length === 0) showNotification("error", "No items matched search criteria");
    } catch (error) {
      if (error.response?.status === 401) handleAuthError();
      else
        showNotification(
          "error",
          error.response?.data?.detail || error.message || "Error searching inventory"
        );
    }
  };

  const handleSearchReset = () => {
    setSearch({
      product_name: "",
      batch_no: "",
      brand: "",
      generic_name: "",
      dosage: "",
      form: "",
      category: "",
    });
    fetchInventory();
  };

  // ----------------- Add Inventory -----------------
  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      // Send JSON directly
      await axios.post(
        "http://127.0.0.1:8000/medical_store/inventory/by-name",
        {
          product_name: form.product_name,
          batch_no: form.batch_no,
          expiry_date: form.expiry_date,
          quantity: Number(form.quantity),
          price: Number(form.price),
        },
        { headers: { ...getAuthHeaders(), "Content-Type": "application/json" } }
      );
      showNotification("success", "Inventory item added successfully");
      setForm({
        product_name: "",
        brand: "",
        dosage: "",
        form: "",
        category: "",
        batch_no: "",
        expiry_date: "",
        quantity: "",
        price: "",
      });
      setMode("view");
      fetchInventory();
    } catch (error) {
      if (error.response?.status === 401) handleAuthError();
      else
        showNotification(
          "error",
          error.response?.data?.detail || error.message || "Error adding inventory"
        );
    }
  };

  // ----------------- Update Inventory -----------------
  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      Object.entries(form).forEach(([k, v]) => formData.append(k, v));
      await axios.put(
        "http://127.0.0.1:8000/medical_store/inventory/update",
        formData,
        { headers: getAuthHeaders() }
      );
      showNotification("success", "Inventory item updated successfully");
      setMode("view");
      fetchInventory();
    } catch (error) {
      if (error.response?.status === 401) handleAuthError();
      else
        showNotification(
          "error",
          error.response?.data?.detail || error.message || "Error updating inventory"
        );
    }
  };

  // ----------------- Delete Inventory -----------------
  const handleDelete = async (item) => {
    if (!window.confirm(`Are you sure you want to delete ${item.product_name} (${item.product?.brand})?`))
      return;
    try {
      await axios.delete(
        "http://127.0.0.1:8000/medical_store/inventory/delete",
        {
          params: { product_name: item.product_name, brand: item.product?.brand },
          headers: getAuthHeaders(),
        }
      );
      showNotification("success", "Inventory item deleted successfully");
      fetchInventory();
    } catch (error) {
      if (error.response?.status === 401) handleAuthError();
      else
        showNotification(
          "error",
          error.response?.data?.detail || error.message || "Error deleting inventory"
        );
    }
  };

  const handleEdit = (item) => {
    setForm({
      product_name: item.product_name,
      brand: item.product?.brand || "",
      dosage: item.product?.dosage || "",
      form: item.product?.form || "",
      category: item.product?.category || "",
      batch_no: item.batch_no,
      expiry_date: item.expiry_date.split("T")[0],
      quantity: item.quantity,
      price: item.price,
    });
    setMode("update");
  };

  return (
    <div className="inventory__container">
      {notification.show && (
        <Notification
          type={notification.type}
          message={notification.message}
          onClose={() => setNotification({ show: false, type: "", message: "" })}
        />
      )}

      <header className="inventory__header">
        <h2>Inventory Management</h2>
        <button
          className="inventory__addbtn"
          onClick={() => {
            setMode("add");
            setForm({
              product_name: "",
              brand: "",
              dosage: "",
              form: "",
              category: "",
              batch_no: "",
              expiry_date: "",
              quantity: "",
              price: "",
            });
          }}
        >
          + Add
        </button>
      </header>

      {mode === "view" && (
        <form className="inventory__searchform" onSubmit={handleSearch}>
          {["product_name","brand","dosage","batch_no","generic_name","form","category"].map((f) => (
            <input
              key={f}
              name={f}
              placeholder={f.charAt(0).toUpperCase() + f.slice(1)}
              value={search[f]}
              onChange={handleSearchInput}
            />
          ))}
          <button type="submit">Search</button>
          <button type="button" className="inventory__cancel" onClick={handleSearchReset}>Reset</button>
        </form>
      )}

      {mode === "view" && (
        <div className="inventory__tablewrap">
          <table className="inventory__table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Brand</th>
                <th>Dosage</th>
                <th>Form</th>
                <th>Category</th>
                <th>Batch</th>
                <th>Expiry</th>
                <th>Qty</th>
                <th>Price</th>
                <th className="inventory__actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(inventory) && inventory.length > 0 ? (
                inventory.map((item) => (
                  <tr key={item.inventory_id}>
                    <td>{item.product_name}</td>
                    <td>{item.product?.brand}</td>
                    <td>{item.product?.dosage}</td>
                    <td>{item.product?.form}</td>
                    <td>{item.product?.category}</td>
                    <td>{item.batch_no}</td>
                    <td>{item.expiry_date.split("T")[0]}</td>
                    <td>{item.quantity}</td>
                    <td>₹{item.price}</td>
                    <td className="inventory__actions">
                      <button onClick={() => handleEdit(item)} aria-label="Edit">&#9998;</button>
                      <button onClick={() => handleDelete(item)} aria-label="Delete" className="inventory__del">&#128465;</button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="10" className="inventory__empty">No items found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {(mode === "add" || mode === "update") && (
        <form className="inventory__form" onSubmit={mode === "add" ? handleAdd : handleUpdate}>
          {["product_name","brand","dosage","form","category","batch_no","expiry_date","quantity","price"].map((f) => (
            <div key={f}>
              <label>{f.charAt(0).toUpperCase() + f.slice(1)}</label>
              <input
                name={f}
                type={["quantity","price"].includes(f) ? "number" : f === "expiry_date" ? "date" : "text"}
                value={form[f]}
                onChange={handleFormInput}
                required
              />
            </div>
          ))}
          <footer>
            <button type="submit">{mode === "add" ? "Add" : "Update"}</button>
            <button type="button" className="inventory__cancel" onClick={() => setMode("view")}>Cancel</button>
          </footer>
        </form>
      )}
    </div>
  );
}
