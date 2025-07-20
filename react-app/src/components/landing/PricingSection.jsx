import { useState } from 'react';
import styles from './PricingSection.module.css';

const pricingData = {
  monthly: [
    { name: 'Starter', price: '$5/mo', features: ['3 social profiles', 'Basic analytics', 'AI suggestions'] },
    { name: 'Creator', price: '$12/mo', features: ['10 social profiles', 'Advanced analytics', 'AI content planner', 'Priority support'] },
    { name: 'Pro', price: '$22/mo', features: ['Unlimited profiles', 'White-label', 'Team collaboration', 'Dedicated manager'] },
  ],
  yearly: [
    { name: 'Starter', price: '$48/yr', features: ['3 social profiles', 'Basic analytics', 'AI suggestions'] },
    { name: 'Creator', price: '$110/yr', features: ['10 social profiles', 'Advanced analytics', 'AI content planner', 'Priority support'] },
    { name: 'Pro', price: '$170/yr', features: ['Unlimited profiles', 'White-label', 'Team collaboration', 'Dedicated manager'] },
  ]
};

const PricingSection = () => {
  const [plan, setPlan] = useState('monthly');
  return (
    <section className={styles.pricing}>
      <h2 className={styles.heading}>Pricing Plans</h2>
      <div className={styles.segmentedToggle}>
        <button
          className={plan === 'monthly' ? styles.segmentedActive : styles.segmentedBtn}
          onClick={() => setPlan('monthly')}
          type="button"
        >
          Monthly
        </button>
        <button
          className={plan === 'yearly' ? styles.segmentedActive : styles.segmentedBtn}
          onClick={() => setPlan('yearly')}
          type="button"
        >
          Yearly
        </button>
      </div>
      <div className={styles.pricingCards}>
        {pricingData[plan].map((tier, i) => (
          <div className={styles.pricingCard} key={i}>
            <h3>{tier.name}</h3>
            <div className={styles.price}>{tier.price}</div>
            <ul>
              {tier.features.map((f, j) => <li key={j}>{f}</li>)}
            </ul>
            <button className={styles.chooseBtn}>Start free 7-Day trial</button>
          </div>
        ))}
      </div>
    </section>
  );
};

export default PricingSection;
