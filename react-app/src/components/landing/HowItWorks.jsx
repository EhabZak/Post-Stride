import styles from './HowItWorks.module.css';

const steps = [
  { title: 'Connect Accounts', desc: 'Link all your social media profiles in seconds.' },
  { title: 'Plan & Create', desc: 'Use AI to plan, write, and schedule your posts.' },
  { title: 'Analyze & Grow', desc: 'Track performance and optimize your strategy.' }
];

const HowItWorks = () => (
  <section className={styles.howItWorks}>
    <h2 className={styles.heading}>How It Works</h2>
    <div className={styles.steps}>
      {steps.map((step, i) => (
        <div className={styles.step} key={i}>
          <div className={styles.stepNumber}>{i + 1}</div>
          <h3>{step.title}</h3>
          <p>{step.desc}</p>
        </div>
      ))}
    </div>
  </section>
);

export default HowItWorks;
