// src/Pages/About/TeamSection.jsx
import React from "react";
import "./About.css";
import CEOImage from '../../assets/CEO.jpeg';
import CTOImage from '../../assets/CTO.jpeg';
import DesignerImage from '../../assets/Designer.png'

const teamMembers = [
  { name: "Dr. Nikhil Saini", role: "Founder & CEO", img: CEOImage },
];

function TeamSection() {
  return (
    <div className="team-section">
      <h2>Meet Our CEO</h2>
      <div className="team-grid">
        {teamMembers.map((member, idx) => (
          <div key={idx} className="team-card">
            <img src={member.img} alt={member.name} />
            <h4>{member.name}</h4>
            <p>{member.role}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TeamSection;
