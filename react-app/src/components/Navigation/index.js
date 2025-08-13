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

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-logo">
          <NavLink exact to="/">
            <img id="logo-image" src={logo} alt="Logo" />
          </NavLink>
        </div>
        
        <div className="nav-links">
          {navLinks.map(link => (
            <button 
              key={link.label}
              onClick={() => scrollToSection(link.href.replace('#', ''))} 
              className="link"
            >
              {link.label}
            </button>
          ))}
        </div>

        <div className="nav-auth">
          {isLoaded && (
            <ProfileButton user={sessionUser} />
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navigation;