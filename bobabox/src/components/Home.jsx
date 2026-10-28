import { Link } from 'react-router-dom'
import { FiArrowRight } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'
import Bubbles from './Bubbles.jsx'

const steps = [
  {
    image: '/images/steps/pick.svg',
    title: 'Pick your kits',
    text: 'Choose from five café-style flavors, from classic taro to brown sugar.',
  },
  {
    image: '/images/steps/ship.svg',
    title: 'We ship it',
    text: 'Everything arrives in one box: tea, syrups, and quick-cook tapioca pearls.',
  },
  {
    image: '/images/steps/make.svg',
    title: 'Make boba at home',
    text: 'Ready in about 10 minutes. Each kit makes 6 drinks.',
  },
]

function Home() {
  const { products, productsLoading, productsError } = useOrder()

  return (
    <div className="home">
      <section className="home-hero">
        <Bubbles />

        <div className="home-hero-inner">
          <div className="home-hero-copy">
            <h1 className="home-hero-brand">
              boba<span className="brand-dot" aria-hidden="true" />box
            </h1>
            <p className="home-hero-tagline">
              The perfect kit,
              <br />
              delivered to your door
            </p>
            <p className="home-hero-text">
              Café-quality boba at home. Real tea, slow-cooked syrups, and chewy pearls
              in one box.
            </p>
            <div className="home-hero-actions">
              <Link to="/purchase" className="primary-button">
                shop kits <FiArrowRight />
              </Link>
              <a href="#how-it-works" className="secondary-link">
                how it works
              </a>
            </div>
          </div>
        </div>

        <div className="home-hero-image">
          <img
            src="/images/hero-box.jpg"
            alt="A light blue boba.box kit box next to a brown sugar boba milk tea"
          />
        </div>
      </section>

      <section id="how-it-works" className="home-section">
        <div className="steps-heading">
          <h2 className="home-section-title">how it works</h2>
          <p>From our box to your cup in three steps.</p>
        </div>
        <div className="steps">
          {steps.map(({ image, title, text }, index) => (
            <div key={title} className="step-card">
              <img className="step-art" src={image} alt="" />
              <span className="step-number">Step {index + 1}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="home-section">
        <div className="home-section-heading">
          <h2 className="home-section-title">the flavors</h2>
          <Link to="/purchase" className="secondary-link">
            see all kits <FiArrowRight />
          </Link>
        </div>
        {productsLoading && <p role="status">Loading flavors…</p>}
        {productsError && (
          <p className="form-error-summary" role="alert">
            Could not load flavors from the inventory service: {productsError}
          </p>
        )}
        <div className="flavor-strip">
          {products.map((product) => (
            <Link key={product.id} to="/purchase" className="flavor-card">
              <span className="flavor-photo">
                <img src={product.image} alt="" loading="lazy" />
              </span>
              <span className="flavor-info">
                <span className="flavor-name">
                  <span
                    className="flavor-dot"
                    style={{ '--swatch': product.gradient }}
                    aria-hidden="true"
                  />
                  {product.name.replace(' Kit', '')}
                </span>
                <span className="flavor-price">{formatPrice(product.price)}</span>
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

export default Home
