import React ,{ useState }from 'react';
import './NavBar.css';
import {BrowserRouter as Router,Route,Routes,Link, NavLink} from 'react-router-dom';
import {FaSearch} from 'react-icons/fa';
import Home from '../Pages/Home';
import About from '../Pages/About';
import Contact from '../Pages/Contact';
import Services from '../Pages/Services';
import Login from '../Pages/Login';
import SignUp from '../Pages/SignUp';
import UserRegistrationForm from '../Formes/UserRegistrationForm';
import DoctorRegistrationForm from '../Formes/DoctorRegistrationForm';

function NavBar() {
  const [menuOpen, setMenuOpen] = useState(false)
  return (
    <> <Router>
     
       
        <nav>
        <Link to="/" className='title'>Meadical App</Link>
          <div className='menu' onClick={() => {
            setMenuOpen(!menuOpen);
          }}>
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div className='search'>
        <input type='text' placeholder='Search...' className='search-input'/>
        
      </div>
      <ul className={menuOpen ? "open" : ""}>
        <li><NavLink to="/">Home</NavLink></li>
        <li><NavLink to="/about">About</NavLink></li>
        <li><NavLink to="/contact">Contact Us</NavLink></li>
        <li><NavLink to="/services">Services</NavLink></li>
        <li><NavLink to="/log in">Log in</NavLink></li>
        <li><NavLink to="/sign up">Sign Up</NavLink></li>
      </ul>
      
    </nav>
    
       
    <Routes>
      <Route path='/' element={<Home />}/>
      <Route path='/about' element={<About />}/>
      <Route path='/contact' element={<Contact />}/>
      <Route path='/services' element={<Services />}/>
      <Route path='/log in' element={<Login/>}/>
      <Route path='/sign up' element={<SignUp/>}/>
     <Route path='/user registration' element={<UserRegistrationForm/>}/>
     <Route path='/doctor registration' element={<DoctorRegistrationForm/>}/>
     
    </Routes>
  </Router>
    

    </>
  )
}

export default NavBar