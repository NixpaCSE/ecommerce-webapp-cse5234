import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FiArrowRight,
  FiCheckCircle,
  FiEye,
  FiMinus,
  FiPlus,
  FiShoppingBag,
} from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'
import ProductPreview from './ProductPreview.jsx'
import Bubbles from './Bubbles.jsx'

const LOW_STOCK = 10

function Purchase() {
  const {
    products,
    productsLoading,
    productsError,
    cart,
    cartCount,
    cartTotal,
    addToCart,
    updateQuantity,
  } = useOrder()
  const navigate = useNavigate()

  const [previewProduct, setPreviewProduct] = useState(null)
  const closePreview = useCallback(() => setPreviewProduct(null), [])

  function quantityInCart(id) {
    return cart.find((line) => line.id === id)?.quantity ?? 0
  }

  return (
    <section>
      <div className="hero">
        <Bubbles />
        <h1 className="hero-title">boba kits</h1>
        <div className="hero-row">
          <FiArrowRight className="hero-arrow" aria-hidden="true" />
          <p className="hero-text">
            Everything you need to make boba at home, shipped to your door.
          </p>
        </div>
      </div>

      {productsLoading && <p role="status">Loading kits…</p>}
      {productsError && (
        <p className="form-error-summary" role="alert">
          Could not load kits from the inventory service: {productsError}
        </p>
      )}

      <div className="product-grid">
        {products.map((product) => {
          const inCart = quantityInCart(product.id)
          const soldOut = product.quantity <= 0
          return (
            <article
              key={product.id}
              className={`product-card ${inCart > 0 ? 'selected' : ''}`}
            >
              <div className="product-image">
                <button
                  type="button"
                  className="preview-trigger"
                  onClick={() => setPreviewProduct(product)}
                  aria-label={`Preview ${product.name}`}
                >
                  <img src={product.image} alt={product.name} loading="lazy" />
                  <span className="preview-hint">
                    <FiEye /> click to preview
                  </span>
                </button>
                {inCart > 0 && (
                  <span className="in-cart-badge">
                    <FiCheckCircle aria-hidden="true" /> {inCart} in cart
                  </span>
                )}
              </div>

              <div className="product-body">
                <div className="product-title-row">
                  <h2 className="product-name">
                    <span
                      className="flavor-dot"
                      style={{ '--swatch': product.gradient }}
                      aria-hidden="true"
                    />
                    {product.name}
                  </h2>
                  <p className="product-price">{formatPrice(product.price)}</p>
                </div>
                <p className="product-description">{product.description}</p>
                <ul className="product-tags" aria-live="polite">
                  <li className={product.quantity <= LOW_STOCK ? 'low' : ''}>
                    {soldOut ? 'Sold out' : `${product.quantity} in stock`}
                  </li>
                </ul>
              </div>

              <div className="product-actions">
                {inCart === 0 ? (
                  <button
                    type="button"
                    className="product-add"
                    disabled={soldOut}
                    onClick={() => addToCart(product, 1)}
                  >
                    <FiPlus aria-hidden="true" /> Add to cart
                  </button>
                ) : (
                  <div className="product-stepper">
                    <button
                      type="button"
                      onClick={() => updateQuantity(product.id, inCart - 1)}
                      aria-label={`Remove one ${product.name}`}
                    >
                      <FiMinus />
                    </button>
                    <span aria-live="polite">{inCart} in cart</span>
                    <button
                      type="button"
                      onClick={() => updateQuantity(product.id, inCart + 1)}
                      disabled={inCart >= product.quantity}
                      aria-label={`Add one more ${product.name}`}
                    >
                      <FiPlus />
                    </button>
                  </div>
                )}
              </div>
            </article>
          )
        })}
        {products.length > 0 && (
          <article className="product-card coming-soon-card">
            <img
              className="coming-soon-art"
              src="/images/illustrations/coming-soon.svg"
              alt=""
            />
            <span className="coming-soon-kicker">In the works</span>
            <h2>More flavors coming soon</h2>
            <p>
              We’re testing new recipes in our kitchen. Check back for seasonal
              and limited-run kits.
            </p>
          </article>
        )}
      </div>

      <div className="checkout-bar">
        <div className="checkout-summary">
          <FiShoppingBag />
          <span>
            {cartCount} {cartCount === 1 ? 'item' : 'items'} · {formatPrice(cartTotal)}
          </span>
        </div>
        <button
          type="button"
          className="primary-button"
          disabled={cartCount === 0}
          onClick={() => navigate('/purchase/paymentEntry')}
        >
          Checkout <FiArrowRight />
        </button>
      </div>

      {previewProduct && (
        <ProductPreview
          product={previewProduct}
          available={previewProduct.quantity - quantityInCart(previewProduct.id)}
          onClose={closePreview}
        />
      )}
    </section>
  )
}

export default Purchase
