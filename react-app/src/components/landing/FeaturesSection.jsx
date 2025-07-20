import styles from './FeaturesSection.module.css';

const features = [
  {
    title: 'Multi-Platform Scheduling',
    desc: 'Plan and publish posts to Instagram, TikTok, Twitter, and more from one dashboard.'
  },
  {
    title: 'AI Content Planning',
    desc: 'Get smart suggestions and optimal posting times with our AI assistant.'
  },
  {
    title: 'Performance Insights',
    desc: 'Track engagement and growth with real-time analytics and beautiful reports.'
  }
];

const FeaturesSection = () => (
  <section className={styles.features}>
    <h2 className={styles.heading}>Core Features</h2>
    <div className={styles.featureCards}>
      {features.map((f, i) => (
        <div className={styles.card} key={i}>
          <h3>{f.title}</h3>
          <p>{f.desc}</p>
        </div>
      ))}
    </div>
  </section>
);

export default FeaturesSection;
