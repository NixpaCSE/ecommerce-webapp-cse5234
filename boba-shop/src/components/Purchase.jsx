import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiCheck, FiShoppingCart } from 'react-icons/fi'
import products from '../data/products.js'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'
import BobaCup from './BobaCup.jsx'

function Purchase() {
  const { cart, cartCount, cartTotal, addToCart } = useOrder()
  const navigate = useNavigate()

  // Quantity typed into each card, keyed by product id (not yet in the cart).
  const [quantities, setQuantities] = useState(() =>
    Object.fromEntries(products.map((p) => [p.id, 1])),
  )
  const [justAddedId, setJustAddedId] = useState(null)

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
      <div className="page-intro">
        <h1>Our Menu</h1>
        <p>Pick your drinks and how many you want, then add them to your cart.</p>
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
                <BobaCup teaColor={product.teaColor} pearlColor={product.pearlColor} />
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

              {inCart > 0 && <p className="in-cart-note">{inCart} in cart</p>}
            </form>
          )
        })}
      </div>

      <div className="checkout-bar">
        <div className="checkout-summary">
          <FiShoppingCart />
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
          Proceed to Checkout
        </button>
      </div>
    </section>
  )
}

export default Purchase
