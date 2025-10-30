import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import Notification from "../../Notification/Notification";
import style from "./ProductManagement.module.css";

const emptyProduct = {
  name: "",
  brand: "",
  generic_name: "",
  dosage: "",
  form: "",
  category: "",
  hsn_code: "",
  image: null,
};

export default function ProductManagement() {
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState(emptyProduct);
  const [editId, setEditId] = useState(null);
  const [editName, setEditName] = useState(null);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);
  const [searchName, setSearchName] = useState("");
  const [searchBrand, setSearchBrand] = useState("");
  const [searchCategory, setSearchCategory] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const token = localStorage.getItem("access_token");

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchProducts(page);
  }, [page]);

  async function fetchProducts(pageNum = 1) {
    setLoading(true);
    try {
      const params = {
        page: pageNum,
        size: 10,
        name: searchName || undefined,
        brand: searchBrand || undefined,
        category: searchCategory || undefined,
      };
      const res = await axios.get(
        "http://127.0.0.1:8000/medical_store/products/search",
        {
          params,
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setProducts(res.data.items || []);
      setTotalPages(res.data.pages || 1);
      setPage(res.data.page || 1);
    } catch (error) {
      if (error.response?.status === 401) {
        navigate("/auth", { state: { from: location } });
      } else {
        setNotification({ type: "error", message: "Failed to load products" });
      }
    }
    setLoading(false);
  }

  function handleChange(e) {
    const { name, value, files } = e.target;
    if (name === "image") {
      setForm((f) => ({ ...f, image: files[0] }));
    } else {
      setForm((f) => ({ ...f, [name]: value }));
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    setPage(1);
    fetchProducts(1);
  }

  function handleEdit(product) {
    setEditId(product.product_id);
    setEditName(product.name);
    setForm({ ...product, image: null });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;
    setLoading(true);

    try {
      const formData = new FormData();
      Object.entries(form).forEach(([key, value]) => {
        if (value !== "" && value !== null) formData.append(key, value);
      });

      const config = {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      };

      if (editId) {
        await axios.put(
          `http://127.0.0.1:8000/medical_store/product-update/${editId}`,
          formData,
          config
        );
        setNotification({ type: "success", message: "Product updated!" });
      } else {
        await axios.post(
          "http://127.0.0.1:8000/medical_store/products",
          formData,
          config
        );
        setNotification({ type: "success", message: "Product created!" });
      }
      setForm(emptyProduct);
      setEditId(null);
      setEditName(null);
      fetchProducts(page);
    } catch (error) {
      if (error.response?.status === 401) {
        navigate("/login", { state: { from: location } });
      } else {
        setNotification({
          type: "error",
          message:
            error.response?.data?.detail?.toString() || "Error saving product",
        });
      }
    }
    setLoading(false);
  }

  async function handleDelete(product_id) {
    if (!window.confirm("Delete this product?")) return;
    setLoading(true);

    try {
      await axios.delete(
        `http://127.0.0.1:8000/medical_store/product_delete/${encodeURIComponent(product_id)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNotification({ type: "success", message: "Product deleted!" });
      fetchProducts(page);
    } catch (error) {
      if (error.response?.status === 401) {
        navigate("/login", { state: { from: location } });
      } else {
        setNotification({ type: "error", message: "Could not delete product" });
      }
    }
    setLoading(false);
  }

  function handleCancel() {
    setForm(emptyProduct);
    setEditId(null);
    setEditName(null);
  }

  function goToPrevPage() {
    if (page > 1) setPage(page - 1);
  }

  function goToNextPage() {
    if (page < totalPages) setPage(page + 1);
  }

  return (
    <div className={style["product-management-root"]}>
      <Notification notification={notification} setNotification={setNotification} />
      <h1 className={style["pm-title"]}>Product Management</h1>

      <form
        className={`${style["pm-form"]} ${editId ? style.editing : ""}`}
        onSubmit={handleSubmit}
        autoComplete="off"
      >
        <div className={style["pm-row"]}>
          <input
            type="text"
            name="name"
            placeholder="Name*"
            value={form.name}
            onChange={handleChange}
            disabled={!!editId}
            required
            className={style["pm-input"]}
          />
          <input
            type="text"
            name="brand"
            placeholder="Brand"
            value={form.brand}
            onChange={handleChange}
            className={style["pm-input"]}
          />
          <input
            type="text"
            name="generic_name"
            placeholder="Generic Name"
            value={form.generic_name}
            onChange={handleChange}
            className={style["pm-input"]}
          />
        </div>
        <div className={style["pm-row"]}>
          <input
            type="text"
            name="dosage"
            placeholder="Dosage"
            value={form.dosage}
            onChange={handleChange}
            className={style["pm-input"]}
          />
          <input
            type="text"
            name="form"
            placeholder="Form"
            value={form.form}
            onChange={handleChange}
            className={style["pm-input"]}
          />
          <input
            type="text"
            name="category"
            placeholder="Category"
            value={form.category}
            onChange={handleChange}
            className={style["pm-input"]}
          />
          <input
            type="text"
            name="hsn_code"
            placeholder="HSN Code"
            value={form.hsn_code}
            onChange={handleChange}
            className={style["pm-input"]}
          />
        </div>
        <div className={style["pm-row"]}>
          <input
            type="file"
            name="image"
            accept="image/*"
            onChange={handleChange}
            className={`${style["pm-input"]} ${style["pm-file"]}`}
          />
        </div>
        <div className={style["pm-actions"]}>
          <button
            type="submit"
            disabled={loading}
            className={`${style["pm-btn"]} ${style["pm-btn-main"]} ${
              loading ? style["pm-btn-disabled"] : ""
            }`}
          >
            {editId ? "Update Product" : "Add Product"}
          </button>
          {editId && (
            <button
              type="button"
              disabled={loading}
              className={`${style["pm-btn"]} ${style["pm-btn-cancel"]}`}
              onClick={handleCancel}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <form className={style["pm-searchbar"]} onSubmit={handleSearch}>
        <input
          type="search"
          className={style["pm-search"]}
          placeholder="Search by product name"
          value={searchName}
          onChange={(e) => setSearchName(e.target.value)}
        />
        <input
          type="search"
          className={style["pm-search"]}
          placeholder="Search by brand"
          value={searchBrand}
          onChange={(e) => setSearchBrand(e.target.value)}
        />
        <input
          type="search"
          className={style["pm-search"]}
          placeholder="Search by category"
          value={searchCategory}
          onChange={(e) => setSearchCategory(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className={`${style["pm-btn"]} ${style["pm-btn-main"]}`}
        >
          Search
        </button>
      </form>

      <div className={`${style["pm-products"]} ${loading ? style.loading : ""}`}>
        {loading ? (
          <div className={style["pm-loader"]} />
        ) : products.length === 0 ? (
          <div className={style["pm-empty"]}>No products found.</div>
        ) : (
          <>
            <table className={style["pm-table"]}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Brand</th>
                  <th>Dosage</th>
                  <th>Generic Name</th>
                  <th>Form</th>
                  <th>Category</th>
                  <th>HSN</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.product_id}>
                    <td>{product.name}</td>
                    <td>{product.brand}</td>
                    <td>{product.dosage}</td>
                    <td>{product.generic_name}</td>
                    <td>{product.form}</td>
                    <td>{product.category}</td>
                    <td>{product.hsn_code}</td>
                    <td>
                      <button
                        className={`${style["pm-btn-edit"]} ${style["pm-btn-mini"]}`}
                        onClick={() => handleEdit(product)}
                      >
                        Edit
                      </button>
                      <button
                        className={`${style["pm-btn"]} ${style["pm-btn-mini"]} ${style["pm-btn-danger"]}`}
                        onClick={() => handleDelete(product.product_id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className={style["pm-pagination"]}>
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>
                Prev
              </button>
              <span>
                Page {page} of {totalPages}
              </span>
              <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
