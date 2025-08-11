import styles from './ComparisonSection.module.css';

const ComparisonSection = () => {
  const painPoints = [
    {
      headline: "Manual Posting Mayhem",
      content: "Wasting hours uploading the same content to each platform one-by-one — time you'll never get back."
    },
    {
      headline: "Paying More Than You Should",
      content: "You're not a corporate giant — so why get charged like one?"
    },
    {
      headline: "Paying for the Extras You'll Never Use",
      content: "A hundred features you'll never touch — but you're still footing the bill for every single one."
    },
    {
      headline: "Unnecessarily Complicated Tools",
      content: "So complex, you spend more time figuring them out than actually getting work done."
    }
  ];

  const solutions = [
    {
      title: "Cross-posting",
      description: "Upload your content to post bridge and post it to any of your connected social media accounts; including posting to all platforms at the same time."
    },
    {
      title: "Scheduling",
      description: "Plan and schedule your content in advance, so you can focus on creating while we handle the posting."
    },
    {
      title: "Content management",
      description: "Organize and manage all your social media content in one centralized location for easy access and editing."
    },
    {
      title: "Content Studio",
      description: "Create, edit, and optimize your content with our intuitive tools designed for social media success."
    }
  ];

  return (
    <section className={styles.comparisonSection}>
      <div className={styles.container}>
        {/* Problem Statement */}
        <div className={styles.problemSection}>
          <h1 className={styles.mainHeading}>
            Posting content shouldn't be this hard
          </h1>
          
          <h2 className={styles.sectionHeading}>What's out there now…</h2>
          
          <div className={styles.painPointsGrid}>
            {painPoints.map((point, index) => (
              <div key={index} className={styles.painPointCard}>
                <div className={styles.painPointHeader}>
                  <div className={styles.xIcon}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M18 6L6 18M6 6L18 18" stroke="#DC2626" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <h3 className={styles.cardHeadline}>{point.headline}</h3>
                </div>
                <p className={styles.cardContent}>{point.content}</p>
              </div>
            ))}
          </div>
          
          <p className={styles.problemSummary}>
            Lose hours of your day or drain your wallet? Neither should be the answer.
          </p>
        </div>

        {/* Solution Section */}
        <div className={styles.solutionSection}>
          <h1 className={styles.mainHeading}>
            Reach more people without the extra work or big spend
          </h1>
          
          <h2 className={styles.sectionHeading}>What Post Stride can do for you:</h2>
          
          <div className={styles.solutionsGrid}>
            {solutions.map((solution, index) => (
              <div key={index} className={styles.solutionCard}>
                <div className={styles.solutionHeader}>
                  <div className={styles.checkmarkIcon}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 6L9 17L4 12" stroke="#059669" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <h3 className={styles.solutionTitle}>{solution.title}</h3>
                </div>
                <p className={styles.solutionDescription}>{solution.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default ComparisonSection;
