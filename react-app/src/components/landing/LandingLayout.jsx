import Hero from './Hero';
import LogosBar from './LogosBar';
import FeaturesSection from './FeaturesSection';
import ComparisonSection from './ComparisonSection';
import HowItWorks from './HowItWorks';
import IntegrationsSection from './IntegrationsSection';
import TestimonialsSection from './TestimonialsSection';
import PricingSection from './PricingSection';
import FAQSection from './FAQSection';
import CtaBanner from './CtaBanner';
import Footer from '../common/Footer';
const LandingLayout = () => (
  <>
    <Hero />
    <LogosBar />
    <div id="features">
      <FeaturesSection />
    </div>
    <ComparisonSection />
    <HowItWorks />
    <div id="platforms">
      <IntegrationsSection />
    </div>
    <div id="reviews">
      <TestimonialsSection />
    </div>
    <div id="pricing">
      <PricingSection />
    </div>
    <div id="faq">
      <FAQSection />
    </div>
    <CtaBanner />
    <Footer />
  </>
);

export default LandingLayout;
