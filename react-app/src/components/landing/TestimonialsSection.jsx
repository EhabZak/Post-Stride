import styles from './TestimonialsSection.module.css';

const testimonials = [
  {
    text: 'Post Stride made managing my clients’ social media a breeze!',
    user: 'Alex, Agency Owner'
  },
  {
    text: 'The AI suggestions are spot on. My engagement is up 40%!',
    user: 'Jamie, Influencer'
  }
];

const TestimonialsSection = () => (
  <section className={styles.testimonials}>
    <h2 className={styles.heading}>What Our Users Say</h2>
    <div className={styles.testimonialCards}>
      {testimonials.map((t, i) => (
        <div className={styles.testimonial} key={i}>
          <p>“{t.text}”</p>
          <span>- {t.user}</span>
        </div>
      ))}
    </div>
  </section>
);

export default TestimonialsSection;
