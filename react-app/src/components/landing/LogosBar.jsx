import styles from './LogosBar.module.css';

const LogosBar = () => (
  <div className={styles.logosBar}>
    <img src="/icons/instagram.svg" alt="Instagram" className={styles.logo} />
    <img src="/icons/tiktok.svg" alt="TikTok" className={styles.logo} />
    <img src="/icons/x.svg" alt="x" className={styles.logo} />
    <img src="/icons/facebook.svg" alt="Facebook" className={styles.logo} />
    <img src="/icons/linkedin.svg" alt="LinkedIn" className={styles.logo} />
    <img src="/icons/bluesky.svg" alt="Bluesky" className={styles.logo} />
  </div>
);

export default LogosBar;
