// src/Pages/About/About.jsx
import React, { useEffect } from "react";
import AOS from "aos";
import "aos/dist/aos.css";
import "./About.css";

import AboutHero from "./AboutHero";
import AboutSection from "./AboutSection";
import MissionVision from "./MissionVision";
import TeamSection from "./TeamSection";
import Carousel from "../../Carousel/Carousel";

function About() {
  useEffect(() => {
    AOS.init({ duration: 1000, once: true });
  }, []);

  return (
    <>
      <Carousel/>
      <div className="about-container">
        <AboutHero />

        <div data-aos="fade-up">
          <AboutSection title="Our Story">
            <p>
              Founded with the mission to revolutionize healthcare access,
              Aroven Healthcare brings together all key stakeholders in
              the health ecosystem for seamless, tech-driven collaboration.
            </p>
          </AboutSection>
        </div>

        <div data-aos="fade-right">
          <MissionVision />
        </div>

        <div data-aos="zoom-in">
          <TeamSection />
        </div>

        <div data-aos="fade-up">
          <AboutSection title="Core Values">
            <ul>
              <li>⚕ Excellence</li>
              <li>💡 Innovation</li>
              <li>🤝 Trust & Transparency</li>
              <li>🌍 Accessibility</li>
            </ul>
          </AboutSection>
        </div>
      </div>

      
    </>
  );
}

export default About;
