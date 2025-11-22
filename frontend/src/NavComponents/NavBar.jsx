import React, { useState, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { FaSearch, FaUserCircle, FaShoppingCart } from 'react-icons/fa';
import styles from './NavBar.module.css';

function NavBar({ isLoggedIn = false, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [cartCount, setCartCount] = useState(0);
  const navigate = useNavigate();

  // ✅ Load initial cart count from localStorage
  useEffect(() => {
    const savedCount = parseInt(localStorage.getItem("cart_count")) || 0;
    setCartCount(savedCount);

    // ✅ Listen to custom cart updates (from ProductList)
    const handleCartUpdate = (e) => {
      // Assuming e.detail is the new count
      const newCount = e.detail || 0;
      setCartCount(newCount);
      // Optional: Update localStorage here if the event source (e.g., ProductList)
      // doesn't handle it, to keep the initial load count accurate.
      // localStorage.setItem("cart_count", newCount.toString());
    };

    window.addEventListener("cartUpdated", handleCartUpdate);
    return () => window.removeEventListener("cartUpdated", handleCartUpdate);
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchText.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchText.trim())}`);
    }
    setMenuOpen(false);
  };

  const handleLogout = () => {
    onLogout?.();
    localStorage.removeItem("access_token");
    setMenuOpen(false);
  };

  const handleCartClick = () => {
    navigate('/cart');
    setMenuOpen(false);
  };

  return (
    <nav className={styles.navbar}>
      {/* Logo */}
      <Link to="/" className={styles.logoContainer} aria-label="Aroven Home">
        <img src="/Aroven2.jpeg" alt="Aroven Logo" className={styles.logoImg} />
      </Link>

      {/* Search (Desktop) */}
      <form
        onSubmit={handleSearchSubmit}
        className={`${styles.search} ${styles.desktopSearch}`}
        aria-label="Search"
      >
        <input
          type="text"
          placeholder="Search..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          className={styles.searchInput}
        />
        <button type="submit" className={styles.searchBtn}>
          <FaSearch />
        </button>
      </form>

      {/* Nav Links (Includes Mobile Menu Content) */}
      <ul className={`${styles.navLinks} ${menuOpen ? styles.open : ''}`}>
        <li className={styles.navItem}>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.activeNav}` : styles.navLink
            }
            onClick={() => setMenuOpen(false)}
          >
            Home
          </NavLink>
        </li>
        <li className={styles.navItem}>
          <NavLink
            to="/about"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.activeNav}` : styles.navLink
            }
            onClick={() => setMenuOpen(false)}
          >
            About
          </NavLink>
        </li>
        <li className={styles.navItem}>
          <NavLink
            to="/contact"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.activeNav}` : styles.navLink
            }
            onClick={() => setMenuOpen(false)}
          >
            Contact Us
          </NavLink>
        </li>
        <li className={styles.navItem}>
          <NavLink
            to="/services"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.activeNav}` : styles.navLink
            }
            onClick={() => setMenuOpen(false)}
          >
            Services
          </NavLink>
        </li>

        {/* --- NEW: Cart Link for Mobile Menu --- */}
        <li className={`${styles.navItem} ${styles.mobileCartItem}`}>
          <div
            className={styles.navLink} // Using div and custom click handler
            onClick={handleCartClick}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && handleCartClick()}
          >
            Cart
            {cartCount > 0 && (
              <span className={styles.cartCountMobile}>({cartCount})</span>
            )}
          </div>
        </li>
        {/* --- END NEW --- */}

        {/* Login / Logout */}
        <li className={styles.navItem}>
          {isLoggedIn ? (
            <span
              className={`${styles.navLink} ${styles.logoutLink}`}
              onClick={handleLogout}
            >
              Log out
            </span>
          ) : (
            <NavLink
              to="/auth"
              className={({ isActive }) =>
                isActive ? `${styles.navLink} ${styles.activeNav}` : styles.navLink
              }
              onClick={() => setMenuOpen(false)}
            >
              Log in
            </NavLink>
          )}
        </li>
      </ul>

      {/* Icons: Cart (Desktop/Tablet) + User */}
      <div className={styles.iconsContainer}>
        {/* Existing Cart Icon (Desktop/Tablet) */}
        <Link to="/cart" className={styles.cartIcon}>
          <FaShoppingCart size={26} />
          {cartCount > 0 && (
            <span className={styles.cartCount}>{cartCount}</span>
          )}
        </Link>
        <div className={styles.userIcon}>
          <FaUserCircle size={27} />
        </div>
      </div>

      {/* Mobile Menu Toggle */}
      <div
        className={`${styles.menuToggle} ${menuOpen ? styles.open : ''}`}
        onClick={() => setMenuOpen(!menuOpen)}
        role="button"
        tabIndex={0}
        aria-expanded={menuOpen}
        aria-label={menuOpen ? 'Close menu' : 'Open menu'}
        onKeyDown={(e) => e.key === 'Enter' && setMenuOpen(!menuOpen)}
      >
        <span className={styles.menuBar}></span>
        <span className={styles.menuBar}></span>
        <span className={styles.menuBar}></span>
      </div>
    </nav>
  );
}

export default NavBar;

