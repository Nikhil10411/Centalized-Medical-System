import React, { useEffect, useState, useCallback, useMemo } from "react";
import { X, CheckCircle, AlertTriangle } from "lucide-react";

// The base URL for the backend API
const API_BASE = "http://localhost:8000/api";

/**
 * Custom Notification Component
 */
const Notification = ({ type, message, onClose }) => {
  if (!message) return null;

  let icon, baseClasses, typeClasses;

  switch (type) {
    case "success":
      icon = <CheckCircle size={20} />;
      typeClasses = "bg-green-500 border-green-700";
      break;
    case "error":
      icon = <AlertTriangle size={20} />;
      typeClasses = "bg-red-500 border-red-700";
      break;
    case "info":
    default:
      icon = <AlertTriangle size={20} />;
      typeClasses = "bg-blue-500 border-blue-700";
      break;
  }

  baseClasses =
    "fixed bottom-5 right-5 p-4 rounded-lg shadow-2xl z-50 transition-transform duration-300 transform translate-y-0 text-white flex items-center space-x-3 max-w-sm border-l-4";

  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [message, onClose]);

  return (
    <div className={`${baseClasses} ${typeClasses}`}>
      {icon}
      <span>{message}</span>
      <button onClick={onClose} className="ml-auto p-1 rounded-full hover:bg-white hover:bg-opacity-20 transition">
        <X size={16} />
      </button>
    </div>
  );
};

/**
 * Main Cart View Component
 */
const CartView = () => {
  const [carts, setCarts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState({ type: "", message: "" });
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedStore, setSelectedStore] = useState(null);
  const [selectedAmount, setSelectedAmount] = useState(0);
  // NOTE: Using localStorage as per original code, but generally discouraged in favor of context/global state or secure storage.
  const token = useMemo(() => localStorage.getItem("access_token"), []);

  const handleCloseNotification = useCallback(() => {
    setNotification({ type: "", message: "" });
  }, []);

  const updateCartCount = useCallback(async () => {
    try {
      if (!token) return;
      const response = await fetch(`${API_BASE}/cart/view`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      let count = 0;
      if (Array.isArray(data)) {
        data.forEach((cart) => {
          if (Array.isArray(cart.items)) count += cart.items.length;
        });
      }
      localStorage.setItem("cart_count", count);
      // In a full application, this event would update a global cart indicator.
      window.dispatchEvent(new CustomEvent("cartUpdated", { detail: count }));
    } catch (e) {
      console.error("Failed to update cart count:", e);
      localStorage.setItem("cart_count", "0");
      window.dispatchEvent(new CustomEvent("cartUpdated", { detail: 0 }));
    }
  }, [token]);

  const fetchCart = useCallback(async () => {
    if (!token) {
        setLoading(false);
        setNotification({ type: "error", message: "User not authenticated. Please log in." });
        return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/cart/view`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch cart");
      const data = await response.json();

      const normalized = Array.isArray(data)
        ? data.map((store) => {
            const items = Array.isArray(store.items) ? store.items : [];
            const total = items.reduce(
                (sum, item) => sum + item.price * item.quantity,
                0
              ) || 0;
            return {
                store_id: store.store_id || 'Unknown Store',
                items: items,
                total: total,
            };
          })
        : [];

      setCarts(normalized);
      setNotification({ type: "", message: "" });
    } catch (e) {
      console.error("Cart fetch error:", e);
      setNotification({ type: "error", message: e.message || "Failed to load cart data" });
      setCarts([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const handleCheckout = useCallback(async (storeId) => {
    if (!token) return setNotification({ type: "error", message: "Authentication required for checkout." });

    try {
      const response = await fetch(`${API_BASE}/checkout/${storeId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Checkout failed");
      }
      const data = await response.json();
      setNotification({
        type: "success",
        message: `Checkout successful! Bill ID: ${data.bill_id}`,
      });
      await fetchCart();
      await updateCartCount();
    } catch (error) {
      setNotification({
        type: "error",
        message: error.message || "Checkout failed",
      });
    }
  }, [token, fetchCart, updateCartCount]);

  const handleRemoveItem = useCallback(async (productId) => {
    if (!token) return setNotification({ type: "error", message: "Authentication required to remove items." });
    
    try {
      const response = await fetch(`${API_BASE}/cart/remove/${productId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to remove item");

      setNotification({ type: "success", message: "Item removed successfully" });
      await fetchCart();
      await updateCartCount();
    } catch (e) {
      setNotification({ type: "error", message: e.message || "Failed to remove item" });
    }
  }, [token, fetchCart, updateCartCount]);

  const handlePaymentOption = useCallback(async (method) => {
    setShowPaymentModal(false);
    if (!token) {
        setNotification({ type: "error", message: "Authentication required for payment." });
        return;
    }
    
    if (method === "Razorpay") {
      try {
        setNotification({ type: "info", message: "Creating Razorpay order..." });
        const res = await fetch(`${API_BASE}/payment/create-order`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            store_id: selectedStore,
            amount: selectedAmount,
            currency: "INR",
            description: "Store Checkout Payment",
          }),
        });
        if (!res.ok) throw new Error("Failed to create Razorpay order");
        const order = await res.json();
        
        // Check for Razorpay script load (simulating external dependency management)
        if (typeof window.Razorpay === "undefined") {
          throw new Error("Razorpay script not loaded. Cannot proceed with payment.");
        }
        
        const options = {
          key: order.key, // Your actual key from the API response
          amount: order.amount,
          currency: order.currency,
          name: "Niksain Medical Store",
          description: "Purchase from your favorite store",
          order_id: order.id,
          handler: async (response) => {
            try {
              const verifyRes = await fetch(`${API_BASE}/payment/verify-payment`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                }),
              });
              if (!verifyRes.ok) throw new Error("Payment verification failed");
              const verifyData = await verifyRes.json();
              setNotification({
                type: "success",
                message: verifyData.message || "Payment successful!",
              });
              await handleCheckout(selectedStore);
            } catch (error) {
              console.error("Razorpay verification error:", error);
              setNotification({
                type: "error",
                message: error.message || "Payment verification failed.",
              });
            }
          },
          prefill: {
            name: "Nikhil Saini",
            email: "user@example.com",
            contact: "9999999999",
          },
          theme: { color: "#00d8ff" },
        };
        const rzp = new window.Razorpay(options);
        rzp.open();
      } catch (error) {
        setNotification({ type: "error", message: error.message || "Failed to initiate Razorpay payment." });
      }
    } else if (method === "Cash on Delivery") {
      await handleCheckout(selectedStore);
    } else {
      setNotification({ type: "info", message: `${method} coming soon!` });
    }
  }, [token, selectedStore, selectedAmount, handleCheckout]);

  const handleClearCart = useCallback(async () => {
    if (!token) return setNotification({ type: "error", message: "Authentication required to clear cart." });
    
    try {
      const response = await fetch(`${API_BASE}/cart/clear`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      // Assuming 200/204 means success, even if the body is empty
      if (!response.ok && response.status !== 204) throw new Error("Failed to clear cart.");

      setCarts([]);
      setNotification({ type: "success", message: "Cart cleared successfully" });
      localStorage.removeItem("cart_items");
      await updateCartCount();
    } catch (e) {
      setNotification({ type: "error", message: e.message || "Failed to clear cart." });
    }
  }, [token, updateCartCount]);

  const openPaymentModal = (storeId, amount) => {
    setSelectedStore(storeId);
    setSelectedAmount(amount);
    setShowPaymentModal(true);
  };

  useEffect(() => {
    fetchCart();
    updateCartCount();
  }, [fetchCart, updateCartCount]);

  const grandTotal = useMemo(() => carts.reduce((sum, cart) => sum + cart.total, 0), [carts]);

  if (loading) {
    return (
      <div className="cart-container">
        <div className="cart-card">
          <p className="text-center text-blue-500 font-semibold">Loading cart...</p>
        </div>
        <Notification {...notification} onClose={handleCloseNotification} />
      </div>
    );
  }

  if (!Array.isArray(carts) || carts.length === 0) {
    return (
      <div className="cart-container">
        <Notification {...notification} onClose={handleCloseNotification} />
        <div className="cart-card">
          <p className="text-center text-blue-500 font-semibold">Your cart is empty 🛒</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 font-sans">
      <style jsx="true">{`
        .cart-container {
          max-width: 1000px;
          margin: 0 auto;
        }
        .cart-card {
          background-color: #fff;
          padding: 1.5rem;
          border-radius: 0.75rem;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          margin-bottom: 1.5rem;
        }
        .cart-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 1rem;
        }
        .cart-table th, .cart-table td {
          padding: 0.75rem 0.5rem;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }
        .cart-table th {
          background-color: #f3f4f6;
          font-weight: 600;
          color: #374151;
        }
        .cart-table tr:last-child td {
          border-bottom: none;
        }
        .cart-footer-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px dashed #e5e7eb;
        }
        .cart-total {
          font-size: 1.25rem;
          font-weight: 700;
          color: #1f2937;
        }
        .cart-grand-total {
          text-align: right;
          font-size: 1.75rem;
          font-weight: 800;
          color: #00d8ff;
          padding: 1.5rem;
          background-color: #fff;
          border-radius: 0.75rem;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .cart-grand-total span {
          color: #00d8ff;
        }
        
        /* Buttons */
        .base-btn {
          padding: 0.5rem 1rem;
          border-radius: 0.5rem;
          font-weight: 600;
          transition: all 0.2s ease-in-out;
          cursor: pointer;
          border: none;
        }
        .clear-cart-btn {
          background-color: #fecaca;
          color: #dc2626;
          border: 1px solid #f87171;
        }
        .clear-cart-btn:hover {
          background-color: #fca5a5;
        }
        .simple-remove-btn {
          background-color: transparent;
          color: #ef4444;
          font-weight: 500;
          padding: 0.25rem 0.5rem;
          border-radius: 0.25rem;
          border: 1px solid #fca5a5;
        }
        .simple-remove-btn:hover {
          background-color: #fee2e2;
        }
        .simple-checkout-btn {
          background-color: #00d8ff;
          color: #fff;
          padding: 0.75rem 1.5rem;
          border-radius: 9999px;
          box-shadow: 0 4px 6px rgba(0, 216, 255, 0.4);
        }
        .simple-checkout-btn:hover {
          background-color: #00b8e6;
        }

        /* Modal */
        .payment-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.6);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 100;
        }
        .payment-modal {
          background: #fff;
          padding: 2rem;
          border-radius: 1rem;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
          width: 90%;
          max-width: 400px;
          text-align: center;
        }
        .payment-modal h3 {
          font-size: 1.5rem;
          font-weight: 700;
          margin-bottom: 1rem;
          color: #1f2937;
        }
        .payment-modal p {
          font-size: 1.25rem;
          font-weight: 500;
          margin-bottom: 1.5rem;
          color: #4b5563;
        }
        .payment-options button {
          display: block;
          width: 100%;
          margin-bottom: 0.75rem;
          padding: 0.75rem;
          border-radius: 0.5rem;
          font-weight: 600;
          transition: background-color 0.2s;
          background-color: #00d8ff;
          color: white;
          border: none;
        }
        .payment-options button:hover {
          background-color: #00b8e6;
        }
        .close-modal-btn {
          background-color: #9ca3af;
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 0.5rem;
          margin-top: 1rem;
          border: none;
          cursor: pointer;
        }
        .close-modal-btn:hover {
          background-color: #6b7280;
        }
      `}</style>

      <Notification {...notification} onClose={handleCloseNotification} />
      
      <div className="cart-container">
        <div style={{ textAlign: "right", margin: "0 0 1.5rem" }}>
          <button className="base-btn clear-cart-btn" onClick={handleClearCart}>
            Clear All Carts
          </button>
        </div>

        {carts.map((cart) => (
          <div className="cart-card" key={cart.store_id}>
            <h3 className="text-xl font-bold mb-4">
              Store: <span style={{ color: "#00d8ff" }}>{cart.store_id}</span>
            </h3>
            <table className="cart-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th className="w-16">Qty</th>
                  <th className="w-24">Price</th>
                  <th className="w-28">Subtotal</th>
                  <th className="w-20">Action</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(cart.items) && cart.items.map((item) => (
                  <tr key={item.product_id}>
                    <td>{item.product_name || item.product_id}</td>
                    <td>{item.quantity}</td>
                    <td>₹{item.price.toFixed(2)}</td>
                    <td>₹{(item.price * item.quantity).toFixed(2)}</td>
                    <td>
                      <button
                        className="simple-remove-btn"
                        onClick={() => handleRemoveItem(item.product_id)}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="cart-footer-row">
              <span className="cart-total">Store Total: ₹{cart.total.toFixed(2)}</span>
              <button
                className="base-btn simple-checkout-btn"
                onClick={() => openPaymentModal(cart.store_id, cart.total)}
              >
                Checkout Store
              </button>
            </div>
          </div>
        ))}

        <div className="cart-grand-total">
          Grand Total: <span>₹{grandTotal.toFixed(2)}</span>
        </div>
      </div>

      {showPaymentModal && (
        <div className="payment-modal-overlay">
          <div className="payment-modal">
            <h3>Choose Payment Method</h3>
            <p>Total Amount: ₹{selectedAmount.toFixed(2)}</p>
            <div className="payment-options">
              <button onClick={() => handlePaymentOption("Razorpay")}>
                Pay with Razorpay
              </button>
              <button onClick={() => handlePaymentOption("Cash on Delivery")}>
                Cash on Delivery
              </button>
            </div>
            <button
              className="close-modal-btn"
              onClick={() => setShowPaymentModal(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CartView;
