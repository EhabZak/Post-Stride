import { useState, useEffect } from 'react';
import styles from './PricingSection.module.css';

const pricingData = {
  monthly: [
    { 
      name: 'Starter', 
      price: '$5/mo', 
      description: 'Best for beginner creators',
      features: [
        '5 connected social accounts',
        'Multiple accounts per platform',
        'Unlimited posts',
        'Schedule posts',
        'Carousel posts',
        '250MB file uploads'
      ] 
    },
    { 
      name: 'Creator', 
      price: '$12/mo', 
      description: 'Best for growing creators',
      features: [
        '15 connected social accounts',
        'Multiple accounts per platform',
        'Unlimited posts',
        'Schedule posts',
        'Carousel posts',
        '500MB file uploads',
        'Bulk video scheduling',
        'Content studio access'
      ] 
    },
    { 
      name: 'Pro', 
      price: '$22/mo', 
      description: 'Best for scaling brands',
      features: [
        'Unlimited connected accounts',
        'Multiple accounts per platform',
        'Unlimited posts',
        'Schedule posts',
        'Carousel posts',
        '500MB file uploads',
        'Bulk video scheduling',
        'Content studio access',
        'Viral growth consulting'
      ] 
    },
  ],
  yearly: [
    { 
      name: 'Starter', 
      price: '$48/yr', 
      description: 'Best for beginner creators',
      features: [
        '5 connected social accounts',
        'Multiple accounts per platform',
        'Unlimited posts',
        'Schedule posts',
        'Carousel posts',
        '250MB file uploads'
      ] 
    },
    { 
      name: 'Creator', 
      price: '$110/yr', 
      description: 'Best for growing creators',
      features: [
        '15 connected social accounts',
        'Multiple accounts per platform',
        'Unlimited posts',
        'Schedule posts',
        'Carousel posts',
        '500MB file uploads',
        'Bulk video scheduling',
        'Content studio access'
      ] 
    },
    { 
      name: 'Pro', 
      price: '$170/yr', 
      description: 'Best for scaling brands',
      features: [
        'Unlimited connected accounts',
        'Multiple accounts per platform',
        'Unlimited posts',
        'Schedule posts',
        'Carousel posts',
        '500MB file uploads',
        'Bulk video scheduling',
        'Content studio access',
        'Viral growth consulting'
      ] 
    },
  ]
};

const PricingSection = () => {
  const [plan, setPlan] = useState('monthly');
  const [selectedCard, setSelectedCard] = useState(null);

  const handleCardClick = (cardIndex, event) => {
    event.stopPropagation();
    setSelectedCard(cardIndex);
  };

  const handleOutsideClick = () => {
    setSelectedCard(null);
  };

  useEffect(() => {
    document.addEventListener('click', handleOutsideClick);
    return () => {
      document.removeEventListener('click', handleOutsideClick);
    };
  }, []);

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
          <div 
            className={`${styles.pricingCard} ${selectedCard === i ? styles.selected : ''}`} 
            key={i}
            onClick={(event) => handleCardClick(i, event)}
          >
            <div className={styles.cardHeader}>
              <h3>{tier.name}</h3>
              {tier.name === 'Creator' && (
                <span className={styles.popularBadge}>Most Popular</span>
              )}
              {tier.name === 'Pro' && (
                <span className={styles.valueBadge}>Great value</span>
              )}
            </div>
            {tier.description && <p className={styles.description}>{tier.description}</p>}
            <div className={styles.price}>{tier.price}</div>
            <ul>
              {tier.features.map((f, j) => (
                <li key={j}>
                  <div className={styles.featureItem}>
                    <svg className={styles.checkmark} width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 6L9 17L4 12" stroke="#059669" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    <span>{f}</span>
                  </div>
                </li>
              ))}
            </ul>
            <button className={styles.chooseBtn}>Start free 7-Day trial</button>
          </div>
        ))}
      </div>
    </section>
  );
};

export default PricingSection;
