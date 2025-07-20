import styles from './IntegrationsSection.module.css';

const integrations = [
  { name: 'Instagram', src: '/assets/logos/instagram.svg' },
  { name: 'TikTok', src: '/assets/logos/tiktok.svg' },
  { name: 'Twitter', src: '/assets/logos/twitter.svg' },
  { name: 'Facebook', src: '/assets/logos/facebook.svg' },
  { name: 'LinkedIn', src: '/assets/logos/linkedin.svg' }
];

const IntegrationsSection = () => (
  <section className={styles.integrations}>
    <h2 className={styles.heading}>Seamless Integrations</h2>
    <div className={styles.logosRow}>
      {integrations.map((i, idx) => (
        <img key={idx} src={i.src} alt={i.name} className={styles.logo} />
      ))}
    </div>
  </section>
);

export default IntegrationsSection;
