import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import Notification from "../../Notification/Notification";
import SupplierForm from "./SupplierForm";
import SupplierSearch from "./SupplierSearch";
import SupplierList from "./SupplierList";
import Pagination from "./Pagination";
import "./SupplierManagement.css";

const API_BASE = "http://localhost:8000/api/medical_store";

const emptySupplier = {
  contact_name: "",
  phone: "",
  email: "",
  address: "",
  city: "",
  pin_code: "",
  age: "",
  gender: "",
};

export default function SupplierManagement() {
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm] = useState(emptySupplier);
  const [editId, setEditId] = useState(null);
  const [search, setSearch] = useState({});
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);   // Notification state
  const [showAll, setShowAll] = useState(false);

  // States for supplier product listing
  const [supplierProducts, setSupplierProducts] = useState([]);
  const [showProducts, setShowProducts] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);

  const token = localStorage.getItem("access_token");
  const navigate = useNavigate();
  const location = useLocation();

  // Close notification handler (used for notification component)
  const closeNotification = useCallback(() => setNotification(null), []);

  // Axios interceptor to catch 401 globally and redirect to login
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem("access_token");
          setNotification({
            type: "error",
            message: "Session expired, redirecting to login"
          });
          setTimeout(() => {
            navigate("/auth", { state: { from: location.pathname } });
          }, 1000);
        }
        return Promise.reject(error);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, [navigate, location.pathname]);

  async function fetchSuppliers(p = 1) {
    setLoading(true);
    try {
      const params = { ...search, page: p };
      const res = await axios.get(
        `${API_BASE}/stores/suppliers/search`,
        {
          params,
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setSuppliers(res.data.items || []);
      setTotalPages(res.data.pageCount || 1);
      setPage(p);
    } catch {
      setNotification({ type: "error", message: "Failed to fetch suppliers" });
      setSuppliers([]);
    }
    setLoading(false);
  }

  async function fetchAllSuppliers() {
    setShowAll(true);
    setLoading(true);
    try {
      const res = await axios.get(
        `${API_BASE}/supplier/get_all_suppliers`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuppliers(res.data || []);
      setTotalPages(1);
      setPage(1);
      setNotification({ type: "success", message: "Fetched all suppliers" });
    } catch {
      setShowAll(false);
      setNotification({ type: "error", message: "Failed to fetch all suppliers" });
      setSuppliers([]);
    }
    setLoading(false);
  }

  useEffect(() => {
    if (!showAll) fetchSuppliers();
    // eslint-disable-next-line
  }, [showAll]);

  async function fetchSupplierProducts(supplier) {
    setLoading(true);
    setShowProducts(true);
    setSelectedSupplier(supplier);
    try {
      const res = await axios.get(
        `${API_BASE}/get_all_supplier/${supplier.supplier_id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSupplierProducts(res.data || []);
    } catch {
      setNotification({ type: "error", message: "Failed to fetch supplier products" });
      setSupplierProducts([]);
    }
    setLoading(false);
  }

  function closeProductList() {
    setShowProducts(false);
    setSupplierProducts([]);
    setSelectedSupplier(null);
  }

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(
          `${API_BASE }/supplier/update/${editId}`,
          form,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setNotification({ type: "success", message: "Supplier updated!" });
      } else {
        await axios.post(
          `${API_BASE}/supplier`,
          form,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setNotification({ type: "success", message: "Supplier added!" });
      }
      setForm(emptySupplier);
      setEditId(null);
      showAll ? fetchAllSuppliers() : fetchSuppliers(page);
    } catch {
      setNotification({ type: "error", message: "Failed to save supplier" });
    }
  }

  function startEdit(supplier) {
    setEditId(supplier.supplier_id);
    setForm({ ...supplier, age: supplier.age || "", gender: supplier.gender || "" });
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this supplier?")) return;
    try {
      await axios.delete(`${API_BASE}/supplier/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotification({ type: "success", message: "Supplier deleted!" });
      showAll ? fetchAllSuppliers() : fetchSuppliers(page);
    } catch {
      setNotification({ type: "error", message: "Delete failed" });
    }
  }

  async function handleLinkSupplier(id) {
    if (!window.confirm("Link this supplier to your store?")) return;
    try {
      await axios.post(
        `${API_BASE}/supplier/link/${id}`,
        null,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNotification({ type: "success", message: "Supplier linked to your store!" });
      showAll ? fetchAllSuppliers() : fetchSuppliers(page);
    } catch {
      setNotification({ type: "error", message: "Linking failed" });
    }
  }

  function handleSearchChange(e) {
    const { name, value } = e.target;
    setSearch((s) => ({ ...s, [name]: value }));
  }

  function handleSearch(e) {
    e.preventDefault();
    setShowAll(false);
    fetchSuppliers(1);
  }

  function handlePageChange(newPage) {
    if (newPage < 1 || newPage > totalPages) return;
    fetchSuppliers(newPage);
  }

  function handleShowAll() {
    fetchAllSuppliers();
  }

  function handleShowPaginated() {
    setShowAll(false);
    fetchSuppliers(1);
  }

  function handleAddToCart(product) {
    setNotification({ type: "success", message: `Added ${product.product.generic_name} to cart!` });
    // Integrate with your cart logic as needed
  }

  return (
    <div className="supplier-container">
      {/* Notification bar, shows ONLY if notification is set */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={closeNotification}
        />
      )}

      <h1>Supplier Management</h1>
      <SupplierForm
        form={form}
        onChange={handleChange}
        onSubmit={handleSubmit}
        onCancel={() => {
          setEditId(null);
          setForm(emptySupplier);
        }}
        editing={Boolean(editId)}
      />
      <SupplierSearch
        search={search}
        onChange={handleSearchChange}
        onSearch={handleSearch}
        onClear={() => {
          setSearch({});
          setShowAll(false);
          fetchSuppliers(1);
        }}
        onToggleView={showAll ? handleShowPaginated : handleShowAll}
        showAll={showAll}
      />
      <SupplierList
        suppliers={suppliers}
        loading={loading}
        onEdit={startEdit}
        onDelete={handleDelete}
        onLink={handleLinkSupplier}
        onShowProducts={fetchSupplierProducts}
      />
      {!showAll && (
        <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
      )}
      {showProducts && selectedSupplier && (
        <div className="supplier-products-modal">
          <button className="close-btn" onClick={closeProductList}>
            &times;
          </button>
          <h2>Products of {selectedSupplier.supplier_name}</h2>
          {loading && <p>Loading products...</p>}
          {!loading && supplierProducts.length === 0 && <p>No products found for this supplier.</p>}
          <div className="product-list">
            {supplierProducts.map((sp) => (
              <div key={sp.supplier_product_id} className="product-card">
                {sp.product.image ? (
                  <img
                    src={`data:${sp.product.image_mime};base64,${sp.product.image}`}
                    alt={sp.product.generic_name}
                    className="product-image"
                  />
                ) : (
                  <div className="no-image">No Image</div>
                )}
                <div className="product-info">
                  <h3>
                    {sp.product.brand} - {sp.product.generic_name}
                  </h3>
                  <p>Dosage: {sp.product.dosage}</p>
                  <p>Form: {sp.product.form}</p>
                  <p>Category: {sp.product.category}</p>
                  <p>Lead Time: {sp.lead_time_days} days</p>
                  <p>Price: Rs{sp.price}</p>
                  <button
                    onClick={() => handleAddToCart(sp)}
                    className="add-to-cart-btn"
                  >
                    Add to Cart
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

