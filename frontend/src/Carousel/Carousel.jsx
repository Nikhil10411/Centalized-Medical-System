import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import React from "react";

import "./Carousel.css";
import { Link } from 'react-router-dom';
import user from "../assets/User.jpeg"
import doctor from "../assets/Doctor.jpeg";
import hospital from "../assets/Hospital.jpeg";
import lab from "../assets/Lab.jpeg";
import medical from "../assets/Medical.jpeg";
import pharmacy from "../assets/Pharmacy.jpeg";
import nurse from "../assets/Nurse3.jpeg";
import radiologist from "../assets/Radiologist4.jpeg";
const Carousel = () => {
  const settings = {
    dots: true,  // Display dots for navigation
    infinite: true,  // Enables infinite loop
    speed: 500,
    slidesToShow: 1,  // Show one slide at a time
    slidesToScroll: 1,  // Scroll one slide at a time
    autoplay: true,  // Enable auto-play
    autoplaySpeed: 3000,  // Auto-play speed in ms
    arrows: true  // Show next/prev arrows
  };

  return (
    <>
   <div className="carousel-container">
  <Slider {...settings}>
    <div style={{ position: 'relative' }}>
      <img src={user} alt="user" />
      <div className="overlay">
        <h2>Register as User</h2>
        <Link to="/user registration">
        <button>Register</button>
        </Link>
       
      </div>
    </div>
    <div style={{ position: 'relative' }}>
      <img src={doctor} alt="doctor" />
      <div className="overlay">
        <h2>Register as Doctor</h2>
        <Link to ="/doctor registration">
        <button>Register</button>
        </Link>
       
      </div>
    </div>
    <div style={{ position: 'relative' }}>
      <img src={hospital} alt="hospital" />
      <div className="overlay">
        <h2>Register as Hospital</h2>
        <Link to =''>
        <button>Register</button>
        </Link>
        
      </div>
    </div>
    <div style={{ position: 'relative' }}>
      <img src={lab} alt="lab" />
      <div className="overlay">
        <h2>Register as Lab</h2>
        <button>Register</button>
      </div>
    </div>
    <div style={{ position: 'relative' }}>
      <img src={medical} alt="medical" />
      <div className="overlay">
        <h2>Register as Medical</h2>
        <button>Register</button>
      </div>
    </div>
    <div style={{ position: 'relative' }}>
      <img src={pharmacy} alt="pharmacy" />
      <div className="overlay">
        <h2>Register as Pharmacy</h2>
        <button>Register</button>
      </div>
    </div>
    <div style={{ position: 'relative' }}>
      <img src={nurse} alt="nurse" />
      <div className="overlay">
        <h2>Register as Nurse</h2>
        <button>Register</button>
      </div>
    </div>
    <div style={{ position: 'relative' }}>
      <img src={radiologist} alt="radiologist" />
      <div className="overlay">
        <h2>Register as Radiologist</h2>
        <button>Register</button>
      </div>
    </div>
  </Slider>
</div>

    
    </>
   
  );
};

export default Carousel;
