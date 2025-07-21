import { useState } from 'react';
import styles from './Navbar.module.css';

const navLinks = [
  { label: 'Pricing', href: '#pricing' },
  { label: 'Reviews', href: '#reviews' },
  { label: 'Features', href: '#features' },
  { label: 'Platforms', href: '#platforms' },
  { label: 'FAQ', href: '#faq' },
  { label: 'Tools', href: '#tools' },
  { label: 'Blog', href: '#blog' },
];

const Navbar = () => {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <nav className={styles.navbar}>
      <div className={styles.left}>
        <span className={styles.logo}>Post <span className={styles.logoAccent}>Stride</span></span>
      </div>
      <button className={styles.hamburger} onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
        <span className={styles.bar}></span>
        <span className={styles.bar}></span>
        <span className={styles.bar}></span>
      </button>
      <div className={menuOpen ? styles.menuOpen : styles.linksWrapper}>
        <ul className={styles.links}>
          {navLinks.map(link => (
            <li key={link.label}>
              <a href={link.href} className={styles.link}>{link.label}</a>
            </li>
          ))}
        </ul>
        <div className={styles.authButtons}>
          <button className={styles.signIn}>Sign In</button>
          <button className={styles.getStarted}>Get Started</button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
