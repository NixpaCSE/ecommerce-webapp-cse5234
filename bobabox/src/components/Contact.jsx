import { Link } from 'react-router-dom'
import { FiArrowRight, FiMail } from 'react-icons/fi'
import Bubbles from './Bubbles.jsx'

const faqs = [
  {
    question: 'How do I check on my order?',
    answer:
      'Email our support team with your order number and the email address used at checkout. We can help with order status, delivery questions, and address issues.',
  },
  {
    question: 'My order arrived damaged, incorrect, or incomplete. What should I do?',
    answer:
      'Contact us within 7 days of delivery at support@bobabox.example. Include your order number, a brief description, and clear photos of the shipping box and items so we can review the issue and arrange a suitable replacement or refund.',
  },
  {
    question: 'Can I return a kit?',
    answer:
      'For this store’s sample policy, unopened kits may be eligible for return within 30 days of delivery. Email us before sending anything back so we can confirm eligibility and provide return instructions. Return shipping may be the customer’s responsibility.',
  },
  {
    question: 'What if a kit has been opened or there is a food-quality concern?',
    answer:
      'Opened food items cannot be returned for hygiene and safety reasons. If anything seems unsafe, damaged, or below expectations, please stop using it and contact us with your order number and photos. We will review the concern and help with next steps.',
  },
  {
    question: 'When will I receive a refund?',
    answer:
      'After an approved return or issue is reviewed, refunds are sent to the original payment method. It may take 5–10 business days for your bank or card provider to post the refund.',
  },
]

function Contact() {
  return (
    <section className="contact">
      <div className="hero">
        <Bubbles />
        <h1 className="hero-title">here to help</h1>
        <div className="hero-row">
          <FiArrowRight className="hero-arrow" aria-hidden="true" />
          <p className="hero-text">
            Need help after your order? Tell us what happened and our support
            team will help make it right.
          </p>
        </div>
      </div>

      <div className="contact-grid">
        <article className="contact-card contact-card-primary">
          <span className="contact-kicker">Order support</span>
          <h2>Let’s sort it out.</h2>
          <p>
            For order status, delivery questions, returns, damaged items, or
            anything else, email our customer support team. Include your order
            number so we can help faster.
          </p>
          <a
            className="contact-email"
            href="mailto:support@bobabox.example?subject=boba.box%20order%20support"
          >
            <FiMail aria-hidden="true" />
            support@bobabox.example
          </a>
          <p className="contact-response">
            We aim to reply within 1–2 business days.
          </p>
        </article>

        <article className="contact-card">
          <span className="contact-kicker">A smoother resolution</span>
          <h2>What to include</h2>
          <ul className="contact-list">
            <li>Your order number and checkout email</li>
            <li>A short description of the issue and when it arrived</li>
            <li>Photos for damage, missing items, or product concerns</li>
          </ul>
        </article>
      </div>

      <section className="contact-policy" aria-labelledby="returns-heading">
        <div>
          <span className="contact-kicker">Returns &amp; issues</span>
          <h2 id="returns-heading">A fair, straightforward policy.</h2>
        </div>
        <div className="contact-policy-copy">
          <p>
            Unopened kits may be eligible for return within 30 days of delivery.
            Please contact us first for approval and return instructions; items
            sent back without authorization may not be accepted.
          </p>
          <p>
            If an order arrives damaged, incorrect, or incomplete, let us know
            within 7 days. Opened food items are not returnable, but we will
            review quality and safety concerns and help with an appropriate
            resolution.
          </p>
          <p>
            Approved refunds go to the original payment method and can take
            5–10 business days to appear, depending on your provider.
          </p>
        </div>
      </section>

      <section className="contact-faq" aria-labelledby="faq-heading">
        <div className="contact-faq-heading">
          <span className="contact-kicker">Quick answers</span>
          <h2 id="faq-heading">Frequently asked questions</h2>
        </div>
        <div className="faq-list">
          {faqs.map(({ question, answer }) => (
            <details className="faq-item" key={question}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </section>

      <p className="contact-disclaimer">
        boba.box is a class project. This sample support address is not
        monitored, and the policies above are for demonstration only.
      </p>

      <div className="contact-cta">
        <Link to="/purchase" className="primary-button">
          back to the kits <FiArrowRight aria-hidden="true" />
        </Link>
      </div>
    </section>
  )
}

export default Contact
