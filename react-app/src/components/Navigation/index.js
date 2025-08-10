import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useSelector } from 'react-redux';
import ProfileButton from './ProfileButton';
import logo from '../../assets/logos/post-logo.png';


const navLinks = [
  { label: 'Pricing', href: '#pricing' },
  { label: 'Reviews', href: '#reviews' },
  { label: 'Features', href: '#features' },
  { label: 'Platforms', href: '#platforms' },
  { label: 'FAQ', href: '#faq' },
  { label: 'Tools', href: '#tools' },
  { label: 'Blog', href: '#blog' },
];

function Navigation({ isLoaded }) {
  const sessionUser = useSelector(state => state.session.user);
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="navbar">
      
      {/* <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
        <span className="bar"></span>
        <span className="bar"></span>
        <span className="bar"></span>
      </button> */}
      {/* <ul className={menuOpen ? 'menuOpen' : 'linksWrapper'}> */}
        <li>
          <NavLink exact to="/">
            <img id="logo-image" src={logo} alt="Logo" />
          </NavLink>
		  
        </li>
        {navLinks.map(link => (
          <li key={link.label}>
            <a href={link.href} className="link">{link.label}</a>
          </li>
        ))}


        {isLoaded && (
          <li>
            <ProfileButton user={sessionUser} />
          </li>
        )}

		
      {/* </ul> */}
    </nav>
  );
}

export default Navigation;