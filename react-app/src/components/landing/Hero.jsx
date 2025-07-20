import styles from './Hero.module.css';

const Hero = () => (
  <section className={styles.hero}>
    <h1 className={styles.headline}>Effortless Social Media Management</h1>
    <p className={styles.subheadline}>Schedule, plan, and analyze your content across all platforms with AI-powered insights.</p>
    <button className={styles.cta}>Start your free 7-Day trial</button>
  </section>
);

export default Hero;
