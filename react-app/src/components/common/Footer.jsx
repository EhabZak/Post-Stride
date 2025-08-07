import React from 'react';
import logo from '../../assets/logos/post-logo.png';
import './Footer.css';

const Footer = () => {
  const footerLinks = {
    links: [
      { name: 'Support', href: '#support' },
      { name: 'Pricing', href: '#pricing' },
      { name: 'Blog', href: '#blog' },
      { name: 'Affiliates', href: '#affiliates' }
    ],
    platforms: [
      { name: 'Twitter/X scheduler', href: '#twitter' },
      { name: 'Instagram scheduler', href: '#instagram' },
      { name: 'LinkedIn scheduler', href: '#linkedin' },
      { name: 'Facebook scheduler', href: '#facebook' },
      { name: 'TikTok scheduler', href: '#tiktok' },
      { name: 'YouTube scheduler', href: '#youtube' },
      { name: 'Bluesky scheduler', href: '#bluesky' },
      { name: 'Threads scheduler', href: '#threads' },
      { name: 'Pinterest scheduler', href: '#pinterest' }
    ],
    freeTools: [
      { name: 'Instagram Grid Maker', href: '#grid-maker' },
      { name: 'Instagram Handle Checker', href: '#handle-checker' },
      { name: 'TikTok Username Checker', href: '#username-checker' },
      { name: 'TikTok Caption Generator', href: '#caption-generator' },
      { name: 'YouTube Title Checker', href: '#title-checker' }
    ],
    legal: [
      { name: 'Terms of services', href: '#terms' },
      { name: 'Privacy policy', href: '#privacy' }
    ]
  };

  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-left">
          <div className="footer-logo">
            <img src={logo} alt="Post Stride Logo" />
          </div>
          <p className="footer-description">
            Post content to multiple social media platforms at the same time, all-in one place. Cross posting made easy.
          </p>
          <p className="footer-copyright">
            Copyright © 2025 – All rights reserved
          </p>
        </div>
        
        <div className="footer-columns">
          <div className="footer-column">
            <h3>LINKS</h3>
            <ul>
              {footerLinks.links.map((link, index) => (
                <li key={index}>
                  <a href={link.href}>{link.name}</a>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="footer-column">
            <h3>PLATFORMS</h3>
            <ul>
              {footerLinks.platforms.map((link, index) => (
                <li key={index}>
                  <a href={link.href}>{link.name}</a>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="footer-column">
            <h3>FREE TOOLS</h3>
            <ul>
              {footerLinks.freeTools.map((link, index) => (
                <li key={index}>
                  <a href={link.href}>{link.name}</a>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="footer-column">
            <h3>LEGAL</h3>
            <ul>
              {footerLinks.legal.map((link, index) => (
                <li key={index}>
                  <a href={link.href}>{link.name}</a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
