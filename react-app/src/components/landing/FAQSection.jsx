import { useState } from 'react';
import styles from './FAQSection.module.css';

const FAQSection = () => {
  const [openItems, setOpenItems] = useState(new Set());

  const toggleItem = (index) => {
    const newOpenItems = new Set(openItems);
    if (newOpenItems.has(index)) {
      newOpenItems.delete(index);
    } else {
      newOpenItems.add(index);
    }
    setOpenItems(newOpenItems);
  };

  const faqData = [
    {
      question: "What social platforms do you support?",
      answer: "Currently we support Twitter/X, Instagram, LinkedIn, Facebook, TikTok, YouTube, Bluesky, Threads, Pinterest for scheduled posting and instant posting. To see all platforms we offer and that are coming soon click here. If you have a request please feel free to email us."
    },
    {
      question: "How many social accounts can I connect?",
      answer: "Depends on your plan, see the pricing section for more details... You will not find a more fair price anywhere else."
    },
    {
      question: "What is a social account?",
      answer: "Social accounts are accounts of supported social media platforms. For example: Connecting your instagram account = connecting 1 social account."
    },
    {
      question: "Can I connect 2 accounts to the same platform?",
      answer: "Yes. Example: Starter plan can connect 5 total accounts, all of them can be tiktok accounts, or 3 of them could be tiktok and 2 instagram accounts for their cap of 5."
    },
    {
      question: "How many posts can I make and schedule per month?",
      answer: "Unlimited for paying users. 5 for free users. 1 post to 4 platforms = 4 posts total."
    },
    {
      question: "What types of content can I post?",
      answer: "You can create and schedule various types of posts including: videos, images, text posts, carousels (multiple images), and reels. This gives you the flexibility to share all types of content across your social media platforms."
    },
    {
      question: "Will my posts get less reach using this app?",
      answer: "No, you will have the same reach as if you posted manually. We understand you may be wary that the algorithm favors manual posting, we were too! However, under our own testing we have found no difference in reach between manual posting and posting from post bridge. Also checkout our blog post here to make sure you are using a warm account with best practices for getting your content to go viral."
    },
    {
      question: "Can I cancel anytime?",
      answer: "Yes, there's no lock-in and you can cancel your subscription at anytime of the month. When cancelling it will cancel at the end of your current billing period; you can still use the pro features until the end of your billing period."
    },
    {
      question: "Can I get a refund?",
      answer: "Yes! You can request a refund within 7 days of being charged. Just reach out by email in this time frame."
    },
    {
      question: "Do I need to share my social media passwords with you?",
      answer: "No, we never ask for or store your passwords directly. We use official authentication methods provided by each social platform, which means you log in securely through their official login pages. This is the same secure method used by all legitimate social media management tools."
    },
    {
      question: "I have another question",
      answer: "Sure, contact us by email: support@poststride.com"
    }
  ];

  return (
    <section className={styles.faqSection}>
      <div className={styles.container}>
        <h2 className={styles.heading}>FAQ</h2>
        <h3 className={styles.subheading}>Frequently Asked Questions</h3>
        
        <div className={styles.faqList}>
          {faqData.map((item, index) => (
            <div key={index} className={styles.faqItem}>
              <button
                className={`${styles.question} ${openItems.has(index) ? styles.open : ''}`}
                onClick={() => toggleItem(index)}
                aria-expanded={openItems.has(index)}
              >
                <span>{item.question}</span>
                <svg 
                  className={`${styles.arrow} ${openItems.has(index) ? styles.rotated : ''}`}
                  width="20" 
                  height="20" 
                  viewBox="0 0 20 20" 
                  fill="currentColor"
                >
                  <path d="M5 7l5 5 5-5z"/>
                </svg>
              </button>
              
              <div className={`${styles.answer} ${openItems.has(index) ? styles.show : ''}`}>
                <p>{item.answer}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQSection;
