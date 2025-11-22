import React, { useEffect, useState } from "react";
import axios from "axios";
import "./SupplierManagement.css";

const API_BASE = "http://localhost:8000/api/medical_store";

const SupplierProductList = ({ supplierId, token }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Simulate cart state inside this component or lift state up if needed globally
  const [cart, setCart] = useState([]);

  useEffect(() => {
    if (!supplierId) return;
    setCart([]); // clear cart on supplier change
    const fetchProducts = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(
          `${API_BASE}/get_all_supplier/${supplierId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setProducts(res.data || []);
      } catch {
        setError("Failed to fetch products");
        setProducts([]);
      }
      setLoading(false);
    };
    fetchProducts();
  }, [supplierId, token]);

  const addToCart = (product) => {
    if (!cart.find(p => p.supplier_product_id === product.supplier_product_id)) {
      setCart([...cart, product]);
      alert(`${product.product.generic_name} added to cart`);
    } else {
      alert(`${product.product.generic_name} is already in the cart`);
    }
  };

  if (loading) return <p style={{ textAlign: "center" }}>Loading products...</p>;
  if (error) return <p style={{ color: "red", textAlign: "center" }}>{error}</p>;
  if (products.length === 0) return <p style={{ textAlign: "center" }}>No products found for this supplier.</p>;

  return (
    <section className="supplier-section supplier-product-list">
      <h2>Products by Supplier</h2>
      <table className="supplier-table">
        <thead>
          <tr>
            <th>SKU</th>
            <th>Brand</th>
            <th>Generic Name</th>
            <th>Dosage</th>
            <th>Form</th>
            <th>Category</th>
            <th>Lead Time (days)</th>
            <th>Price (₹)</th>
            <th>Created At</th>
            <th>Image</th>
            <th>Supplier Name</th>
            <th>Add to Cart</th>
          </tr>
        </thead>
        <tbody>
          {products.map((sp) => (
            <tr key={sp.supplier_product_id}>
              <td>{sp.supplier_sku}</td>
              <td>{sp.product.brand}</td>
              <td>{sp.product.generic_name}</td>
              <td>{sp.product.dosage}</td>
              <td>{sp.product.form}</td>
              <td>{sp.product.category}</td>
              <td>{sp.lead_time_days}</td>
              <td>{sp.price}</td>
              <td>{new Date(sp.created_at).toLocaleDateString()}</td>
              <td style={{ width: "60px" }}>
                {sp.product.image_mime && sp.product.image_base64 ? (
                  <img
                    src={`data:${sp.product.image_mime};base64,${sp.product.image_base64}`}
                    alt={sp.product.generic_name}
                    style={{ width: "50px", height: "auto", borderRadius: "6px" }}
                  />
                ) : (
                  <span style={{ fontStyle: "italic", color: "#ccc" }}>No Image</span>
                )}
              </td>
              <td>{sp.supplier.supplier_name}</td>
              <td>
                <button className="link-btn" onClick={() => addToCart(sp)}>
                  Add to Cart
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {cart.length > 0 && (
        <div className="supplier-section" style={{ marginTop: "1rem" }}>
          <h3>Cart Items</h3>
          <ul>
            {cart.map(item => (
              <li key={item.supplier_product_id}>
                {item.product.generic_name} - ₹{item.price}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

export default SupplierProductList;
