// src/Pages/About/MissionVision.jsx
import React from "react";
import "./About.css";

function MissionVision() {
  return (
    <div className="mission-vision">
      <div className="mission-card">
        <h3>Our Mission</h3>
        <p>
          To make healthcare accessible, affordable, and efficient for every person, 
          whether in metropolitan cities or remote villages.
        </p>
      </div>
      <div className="vision-card">
        <h3>Our Vision</h3>
        <p>
          To be the leading healthcare connector platform, trusted by millions globally.
        </p>
      </div>
    </div>
  );
}

export default MissionVision;
