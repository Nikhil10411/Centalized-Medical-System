import React from 'react';
import { Link } from 'react-router-dom';
import { FaFacebookF, FaTwitter, FaLinkedinIn } from 'react-icons/fa';
import './Footer.css';

const Footer = () => (
  <footer className="footer-container">
    <div className="footer-content">
      <div className="footer-logo">
        <Link to="/" className="title">Aroven</Link>
      </div>
      <div className="footer-links">
        <Link to="/about">About Us</Link>
        <Link to="/services">Services</Link>
        <Link to="/contact">Contact</Link>
      </div>
      <div className="footer-socials">
        <a href="https://facebook.com" target="_blank" rel="noopener noreferrer">
          <FaFacebookF />
        </a>
        <a href="https://twitter.com" target="_blank" rel="noopener noreferrer">
          <FaTwitter />
        </a>
        <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer">
          <FaLinkedinIn />
        </a>
      </div>
      <div className="footer-legal">
        <p>&copy; 2024 Aroven. All Rights Reserved.</p>
        <Link to="/privacy">Privacy Policy</Link>
        <Link to="/terms">Terms of Service</Link>
      </div>
    </div>
  </footer>
);

export default Footer;
