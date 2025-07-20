import styles from './CtaBanner.module.css';

const CtaBanner = () => (
  <section className={styles.ctaBanner}>
    <h2 className={styles.headline}>Ready to boost your social presence?</h2>
    <button className={styles.ctaBtn}>Try Free for 14 Days</button>
  </section>
);

export default CtaBanner;
