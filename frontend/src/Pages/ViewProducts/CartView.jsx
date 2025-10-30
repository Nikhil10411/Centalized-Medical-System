import React, { useEffect, useState } from "react";
import Notification from "../../Notification/Notification";
import "./Store.css";

const API_BASE = "http://127.0.0.1:8000/api";

const CartView = () => {
  const [carts, setCarts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState({ type: "", message: "" });
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedStore, setSelectedStore] = useState(null);
  const [selectedAmount, setSelectedAmount] = useState(0);
  const token = localStorage.getItem("access_token");

  // ---------------------------------
  // Update Cart Count in Navbar
  // ---------------------------------
  const updateCartCount = async () => {
    try {
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
      window.dispatchEvent(new CustomEvent("cartUpdated", { detail: count }));
    } catch {
      localStorage.setItem("cart_count", "0");
      window.dispatchEvent(new CustomEvent("cartUpdated", { detail: 0 }));
    }
  };

  // ---------------------------------
  // Fetch Cart Items
  // ---------------------------------
  const fetchCart = async () => {
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
        ? data.map((store) => ({
            store_id: store.store_id,
            items: store.items || [],
            total:
              store.items?.reduce(
                (sum, item) => sum + item.price * item.quantity,
                0
              ) || 0,
          }))
        : [];

      setCarts(normalized);
      setNotification({ type: "", message: "" });
    } catch {
      setNotification({ type: "error", message: "Failed to load cart data" });
      setCarts([]);
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------
  // Remove Item from Cart
  // ---------------------------------
  const handleRemoveItem = async (productId) => {
    try {
      const response = await fetch(`${API_BASE}/cart/remove/${productId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to remove item");

      setNotification({ type: "success", message: "Item removed successfully" });
      await fetchCart();
      await updateCartCount();
    } catch {
      setNotification({ type: "error", message: "Failed to remove item" });
    }
  };

  // ---------------------------------
  // Payment Modal
  // ---------------------------------
  const openPaymentModal = (storeId, amount) => {
    setSelectedStore(storeId);
    setSelectedAmount(amount);
    setShowPaymentModal(true);
  };

  // ---------------------------------
  // Handle Razorpay / COD Option
  // ---------------------------------
  const handlePaymentOption = async (method) => {
    setShowPaymentModal(false);

    if (method === "Razorpay") {
      try {
        setNotification({ type: "info", message: "Creating Razorpay order..." });

        // ✅ Step 1: Create Razorpay order (with correct backend route)
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

        // ✅ Step 2: Open Razorpay payment window
        const options = {
          key: order.key,
          amount: order.amount,
          currency: order.currency,
          name: "Niksain Medical Store",
          description: "Purchase from your favorite store",
          order_id: order.id,
          handler: async (response) => {
            try {
              // ✅ Step 3: Verify payment on backend
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

              // ✅ Step 4: Checkout and clear cart
              await handleCheckout(selectedStore);
            } catch (error) {
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
        setNotification({ type: "error", message: error.message });
      }
    } else if (method === "Cash on Delivery") {
      await handleCheckout(selectedStore);
    } else {
      setNotification({ type: "info", message: `${method} coming soon!` });
    }
  };

  // ---------------------------------
  // Checkout After Payment
  // ---------------------------------
  const handleCheckout = async (storeId) => {
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
  };

  // ---------------------------------
  // Clear Entire Cart
  // ---------------------------------
  const handleClearCart = async () => {
    try {
      await fetch(`${API_BASE}/cart/clear`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setCarts([]);
      setNotification({ type: "success", message: "Cart cleared successfully" });
      localStorage.removeItem("cart_items");
      await updateCartCount();
      await fetchCart();
    } catch {
      setCarts([]);
      setNotification({ type: "success", message: "Cart cleared." });
      await updateCartCount();
    }
  };

  // ---------------------------------
  // Initial Load
  // ---------------------------------
  useEffect(() => {
    fetchCart();
    updateCartCount();
  }, []);

  if (loading) {
    return (
      <div className="cart-container">
        <div className="cart-card">
          <p style={{ textAlign: "center", color: "#00d8ff" }}>Loading cart...</p>
        </div>
      </div>
    );
  }

  if (!carts.length) {
    return (
      <div className="cart-container">
        <Notification {...notification} />
        <div className="cart-card">
          <p style={{ textAlign: "center", color: "#00d8ff" }}>Your cart is empty 🛒</p>
        </div>
      </div>
    );
  }

  const grandTotal = carts.reduce((sum, cart) => sum + cart.total, 0);

  // ---------------------------------
  // Render Component
  // ---------------------------------
  return (
    <div className="cart-container">
      <Notification {...notification} />
      <div style={{ textAlign: "right", margin: "0 0 1rem" }}>
        <button className="clear-cart-btn" onClick={handleClearCart}>
          Clear Cart
        </button>
      </div>

      {carts.map((cart) => (
        <div className="cart-card" key={cart.store_id}>
          <h3>
            Store: <span style={{ color: "#00d8ff" }}>{cart.store_id}</span>
          </h3>
          <table className="cart-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Subtotal</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {cart.items.map((item) => (
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
            <span className="cart-total">Total: ₹{cart.total.toFixed(2)}</span>
            <button
              className="simple-checkout-btn"
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

      {/* -------------------- PAYMENT MODAL -------------------- */}
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

