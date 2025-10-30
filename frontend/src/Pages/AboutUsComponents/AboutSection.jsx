// src/Pages/About/AboutSection.jsx
import React from "react";
import "./About.css";

function AboutSection({ title, children }) {
  return (
    <div className="about-section">
      <h2>{title}</h2>
      <div className="about-section-content">{children}</div>
    </div>
  );
}

export default AboutSection;
