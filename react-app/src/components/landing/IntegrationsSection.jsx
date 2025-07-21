import styles from './IntegrationsSection.module.css';

const integrations = [
  { name: 'Instagram', src: '/icons/instagram.svg' },
  { name: 'TikTok', src: '/icons/tiktok.svg' },
  { name: 'x', src: '/icons/x.svg' },
  { name: 'Facebook', src: '/icons/facebook.svg' },
  { name: 'LinkedIn', src: '/icons/linkedin.svg' },
  { name: 'BlueSky', src: '/icons/bluesky.svg' },
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
