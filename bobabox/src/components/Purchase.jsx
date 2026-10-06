import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiArrowRight, FiCheck, FiEye, FiShoppingBag } from 'react-icons/fi'
import products from '../data/products.js'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'
import Swatch from './Swatch.jsx'
import ProductPreview from './ProductPreview.jsx'

function Purchase() {
  const { cart, cartCount, cartTotal, addToCart } = useOrder()
  const navigate = useNavigate()

  // Quantity typed into each card, keyed by product id (not yet in the cart).
  const [quantities, setQuantities] = useState(() =>
    Object.fromEntries(products.map((p) => [p.id, 1])),
  )
  const [justAddedId, setJustAddedId] = useState(null)
  const [previewProduct, setPreviewProduct] = useState(null)
  const closePreview = useCallback(() => setPreviewProduct(null), [])

  function handleQuantityChange(id, value) {
    const quantity = Math.max(0, Math.floor(Number(value) || 0))
    setQuantities((prev) => ({ ...prev, [id]: quantity }))
  }

  function handleAddToCart(e, product) {
    e.preventDefault()
    const quantity = quantities[product.id]
    if (quantity <= 0) return
    addToCart(product, quantity)
    setQuantities((prev) => ({ ...prev, [product.id]: 1 }))
    setJustAddedId(product.id)
    setTimeout(() => setJustAddedId((id) => (id === product.id ? null : id)), 1200)
  }

  function quantityInCart(id) {
    return cart.find((line) => line.id === id)?.quantity ?? 0
  }

  return (
    <section>
      <div className="hero">
        <h1 className="hero-title">boba kits</h1>
        <div className="hero-row">
          <FiArrowRight className="hero-arrow" aria-hidden="true" />
          <p className="hero-text">
            Everything you need to make boba at home, shipped to your door.
          </p>
        </div>
      </div>

      <div className="product-grid">
        {products.map((product) => {
          const inCart = quantityInCart(product.id)
          return (
            <form
              key={product.id}
              className="product-card"
              onSubmit={(e) => handleAddToCart(e, product)}
            >
              <div className="product-image">
                <button
                  type="button"
                  className="preview-trigger"
                  onClick={() => setPreviewProduct(product)}
                  aria-label={`Preview ${product.name}`}
                >
                  <Swatch gradient={product.gradient} />
                  <span className="preview-hint">
                    <FiEye /> click to preview
                  </span>
                </button>
                <FiEye className="preview-icon" aria-hidden="true" />
                {inCart > 0 && <span className="in-cart-badge">{inCart} in cart</span>}
              </div>

              <div className="product-body">
                <h2 className="product-name">{product.name}</h2>
                <p className="product-description">{product.description}</p>
                <p className="product-price">{formatPrice(product.price)}</p>
              </div>

              <div className="product-actions">
                <label className="qty-label">
                  Qty
                  <input
                    type="number"
                    min="0"
                    className="qty-input"
                    value={quantities[product.id]}
                    onChange={(e) => handleQuantityChange(product.id, e.target.value)}
                  />
                </label>
                <button
                  type="submit"
                  className="primary-button"
                  disabled={quantities[product.id] <= 0}
                >
                  {justAddedId === product.id ? (
                    <>
                      <FiCheck /> Added
                    </>
                  ) : (
                    'Add to cart'
                  )}
                </button>
              </div>
            </form>
          )
        })}
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

      {previewProduct && <ProductPreview product={previewProduct} onClose={closePreview} />}
    </section>
  )
}

export default Purchase
