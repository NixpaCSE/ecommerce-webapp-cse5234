import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiArrowRight, FiCheck, FiEye, FiShoppingBag } from 'react-icons/fi'
import products from '../data/products.js'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'
import { fetchInventory } from '../api/inventory.js'
import ProductPreview from './ProductPreview.jsx'
import Bubbles from './Bubbles.jsx'

function Purchase() {
  const { cart, cartCount, cartTotal, addToCart } = useOrder()
  const navigate = useNavigate()
  const [inventory, setInventory] = useState({})
  const [inventoryError, setInventoryError] = useState('')
  const [inventoryLoading, setInventoryLoading] = useState(true)

  // Quantity typed into each card, keyed by product id (not yet in the cart).
  const [quantities, setQuantities] = useState(() =>
    Object.fromEntries(products.map((p) => [p.id, 1])),
  )
  const [justAddedId, setJustAddedId] = useState(null)
  const [previewProduct, setPreviewProduct] = useState(null)
  const closePreview = useCallback(() => setPreviewProduct(null), [])

  useEffect(() => {
    const controller = new AbortController()
    fetchInventory({ signal: controller.signal })
      .then((items) => {
        setInventory(Object.fromEntries(items.map((item) => [item.id, item.quantity])))
        setInventoryError('')
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setInventoryError(error.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setInventoryLoading(false)
      })
    return () => controller.abort()
  }, [])

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
        <Bubbles />
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
                  <img src={product.image} alt={product.name} loading="lazy" />
                  <span className="preview-hint">
                    <FiEye /> click to preview
                  </span>
                </button>
                {inCart > 0 && <span className="in-cart-badge">{inCart} in cart</span>}
              </div>

              <div className="product-body">
                <h2 className="product-name">
                  <span
                    className="flavor-dot"
                    style={{ '--swatch': product.gradient }}
                    aria-hidden="true"
                  />
                  {product.name}
                </h2>
                <p className="product-description">{product.description}</p>
                <p className="product-price">{formatPrice(product.price)}</p>
                {inventory[product.id] !== undefined && (
                  <p className="product-description" aria-live="polite">
                    {inventory[product.id]} in stock
                  </p>
                )}
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
                  disabled={quantities[product.id] <= 0 || (
                    inventory[product.id] !== undefined &&
                    quantities[product.id] + inCart > inventory[product.id]
                  )}
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

      {inventoryLoading && <p role="status">Loading inventory…</p>}
      {inventoryError && <p className="form-error-summary" role="alert">Could not load inventory: {inventoryError}</p>}

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
          available={
            inventory[previewProduct.id] === undefined
              ? undefined
              : inventory[previewProduct.id] - quantityInCart(previewProduct.id)
          }
          onClose={closePreview}
        />
      )}
    </section>
  )
}

export default Purchase
