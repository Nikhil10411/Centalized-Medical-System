import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import ProductCard from "./ProductCard";
import Notification from "../../Notification/Notification";
import "./Store.css";

const API_BASE = "http://localhost:8000/api";

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [notification, setNotification] = useState({ message: "", type: "", isVisible: false });
  const [authToken, setAuthToken] = useState("");
  const [userRole, setUserRole] = useState(null);

  const showNotification = useCallback((message, type = "info") => {
    setNotification({ message, type, isVisible: true });
    setTimeout(() => setNotification({ message: "", type: "", isVisible: false }), 3500);
  }, []);

  // Fetch user role and product list on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      showNotification("Please log in to view products.", "warning");
      return;
    }
    setAuthToken(token);

    const fetchUserRole = async () => {
      try {
        const res = await axios.get(`${API_BASE}/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUserRole(res.data.role);
      } catch {
        setUserRole(null);
        showNotification("Failed to fetch user info.", "error");
      }
    };

    const fetchProducts = async () => {
      try {
        const res = await axios.get(`${API_BASE}/inventory/all_stores`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (Array.isArray(res.data)) {
          setProducts(res.data);
        } else if (res.data.message === "No products available.") {
          setProducts([]);
          showNotification("No products available.", "info");
        } else {
          setProducts([]);
          showNotification("Unexpected product data format", "error");
        }
      } catch (err) {
        setProducts([]);
        if (err.response?.status === 401) {
          showNotification("Session expired. Please log in again.", "error");
        } else {
          showNotification("Failed to load products.", "error");
        }
      }
    };

    fetchUserRole();
    fetchProducts();
  }, [showNotification]);

  // Fetch cart count to update global cart badge
  const fetchCartCount = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/cart/view`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.data.items) {
        const count = res.data.items.reduce((sum, i) => sum + i.quantity, 0);
        localStorage.setItem("cart_count", count);
        window.dispatchEvent(new CustomEvent("cartUpdated", { detail: count }));
      }
    } catch {
      localStorage.setItem("cart_count", 0);
      window.dispatchEvent(new CustomEvent("cartUpdated", { detail: 0 }));
    }
  }, [authToken]);

  // Add to cart handler with role and source awareness
  const handleAddToCart = useCallback(
    async (product) => {
      if (!authToken) {
        showNotification("Please log in to add items to cart.", "error");
        return;
      }

      const isSupplierProduct = product.type === "supplier_product";

      // Only chemists can add supplier products
      if (isSupplierProduct && userRole !== "chemist") {
        showNotification("Only chemists can add supplier products.", "error");
        return;
      }

      // Validate store ID for inventory products
      if (!isSupplierProduct && !product.store_id) {
        showNotification("Invalid store ID for this inventory product.", "error");
        return;
      }

      try {
        const source = isSupplierProduct ? "supplier" : "inventory";

        // Compose add to cart URL with store_id query param if inventory
        const params = new URLSearchParams();
        if (source === "inventory") params.append("store_id", product.store_id);

        const url = `${API_BASE}/add/cart/${product.product_id}?${params.toString()}`;

        const res = await fetch(url, {
          method: "POST",
          headers: { Authorization: `Bearer ${authToken}` },
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Failed to add product to cart.");
        }

        showNotification("Product added to cart.", "success");
        fetchCartCount();
      } catch (e) {
        showNotification(e.message || "Network error adding product.", "error");
      }
    },
    [authToken, userRole, showNotification, fetchCartCount]
  );

  return (
    <div className="store-container">
      <Notification
        message={notification.message}
        type={notification.type}
        duration={3500}
        onClose={() => setNotification({ message: "", type: "", isVisible: false })}
        isVisible={notification.isVisible}
      />

      <h2 className="page-title">
        <span role="img" aria-label="med">
          🩺
        </span>{" "}
        Medical Store Products
      </h2>

      <div className="product-grid">
        {products.length === 0 ? (
          <p style={{ width: "100%", textAlign: "center" }}>No products available.</p>
        ) : (
          products.map((product) => (
            <ProductCard
              key={`${product.product_id}_${product.store_id || "none"}_${product.inventory_id || product.supplier_product_id}`}
              product={product}
              onAddToCart={handleAddToCart}
              authToken={authToken}
              userRole={userRole}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ProductList;

