import styles from './CtaBanner.module.css';

const CtaBanner = () => (
  <section className={styles.ctaBanner}>
    <h2 className={styles.headline}>Ready to boost your social presence?</h2>
    <button className={styles.ctaBtn}>Start your free 7-Day trial</button>
  </section>
);

export default CtaBanner;
