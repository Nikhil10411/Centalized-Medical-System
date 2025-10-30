import React, { useState, useEffect } from "react";
import axios from "axios";
import ProductCard from "./ProductCard";
import Notification from "../../Notification/Notification";
import "./Store.css";

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [notification, setNotification] = useState({ message: "", type: "", isVisible: false });
  const [authToken, setAuthToken] = useState("");

  // Show notification helper
  const showNotification = (message, type = "info") => {
    setNotification({ message, type, isVisible: true });
    setTimeout(() => setNotification({ message: "", type: "", isVisible: false }), 3500);
  };

  // Fetch all products on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      showNotification("Please log in to view products.", "warning");
      return;
    }
    setAuthToken(token);

    const fetchProducts = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/inventory/all_stores", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setProducts(res.data);
      } catch (err) {
        if (err.response?.status === 401) {
          showNotification("Session expired. Please log in again.", "error");
        } else {
          showNotification("Failed to load products.", "error");
        }
      }
    };
    fetchProducts();
  }, []);

  // Fetch cart count from backend
  const fetchCartCount = async () => {
    try {
      // Fetch current cart contents
      const res = await axios.get('http://127.0.0.1:8000/api/cart/view', {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (Array.isArray(res.data)) {
        // Flatten all cart items to count total products (across stores)
        let count = 0;
        res.data.forEach(storeCart => {
          if (Array.isArray(storeCart.items)) count += storeCart.items.length;
        });
        // Save to localStorage and fire event to update NavBar
        localStorage.setItem("cart_count", count);
        window.dispatchEvent(new CustomEvent("cartUpdated", { detail: count }));
      }
    } catch {
      // fallback: reset displayed count
      localStorage.setItem("cart_count", 0);
      window.dispatchEvent(new CustomEvent("cartUpdated", { detail: 0 }));
    }
  };

  // Add product to cart via backend API, then update cart count
  const handleAddToCart = async (product) => {
    try {
      const url = `http://127.0.0.1:8000/api/add/cart/${product.product_id}?store_id=${product.store_id}`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      if (res.ok) {
        showNotification("Product added to cart.", "success");
        // After successful add, fetch cart count from backend
        fetchCartCount();
      } else {
        showNotification("Failed to add product to cart.", "error");
      }
    } catch {
      showNotification("Failed to add product to cart.", "error");
    }
  };

  return (
    <div className="store-container">
      <Notification
        message={notification.message}
        type={notification.type}
        duration={3500}
        onClose={() => setNotification({ message: "", type: "", isVisible: false })}
      />

      <h2 className="page-title">
        <span role="img" aria-label="med">🩺</span> Medical Store Products
      </h2>

      <div className="product-grid">
        {products.length === 0 ? (
          <p style={{ width: "100%", textAlign: "center" }}>No products available.</p>
        ) : (
          products.map((product) => (
            <ProductCard
              key={`${product.product_id}_${product.store_id}_${product.inventory_id}`}
              product={product}
              onAddToCart={handleAddToCart}
              authToken={authToken}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ProductList;
