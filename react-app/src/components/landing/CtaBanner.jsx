import styles from './CtaBanner.module.css';
// import pinguin from '../../assets/logos/pinguin.png';
import pinguin from '../../assets/logos/pinguin.png';

const CtaBanner = () => (
  <section className={styles.ctaBanner}>
    <div className={styles.ctaContainer}>
      <div className={styles.ctaContent}>
        <div className={styles.ctaLeft}>
          <img src={pinguin} alt="Post Stride Logo" className={styles.ctaLogo} />
        </div>
        <div className={styles.ctaRight}>
          <h2 className={styles.headline}>Try Post Stride Now</h2>
          <button className={styles.ctaBtn}>
            Start your free 7-Day trial
          </button>
        </div>
      </div>
    </div>
  </section>
);

export default CtaBanner;
