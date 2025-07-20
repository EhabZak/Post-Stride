import styles from './LogosBar.module.css';

const LogosBar = () => (
  <div className={styles.logosBar}>
    <img src="/assets/logos/instagram.svg" alt="Instagram" className={styles.logo} />
    <img src="/assets/logos/tiktok.svg" alt="TikTok" className={styles.logo} />
    <img src="/assets/logos/twitter.svg" alt="Twitter" className={styles.logo} />
    <img src="/assets/logos/facebook.svg" alt="Facebook" className={styles.logo} />
    <img src="/assets/logos/linkedin.svg" alt="LinkedIn" className={styles.logo} />
  </div>
);

export default LogosBar;
