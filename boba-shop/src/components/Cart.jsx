import { useNavigate } from 'react-router-dom'
import { FiMinus, FiPlus, FiTrash2, FiX } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'

// Slide-out cart available from every page. Lets the user change quantities
// or remove line items at any time.
function Cart({ open, onClose }) {
  const { cart, cartTotal, updateQuantity, removeFromCart } = useOrder()
  const navigate = useNavigate()

  function handleCheckout() {
    onClose()
    navigate('/purchase/paymentEntry')
  }

  return (
    <>
      <div className={`cart-overlay ${open ? 'open' : ''}`} onClick={onClose} />
      <aside className={`cart-drawer ${open ? 'open' : ''}`} aria-hidden={!open}>
        <div className="cart-header">
          <h2>Your Cart</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close cart">
            <FiX size={22} />
          </button>
        </div>

        {cart.length === 0 ? (
          <p className="cart-empty">Your cart is empty. Add some boba!</p>
        ) : (
          <ul className="cart-lines">
            {cart.map((line) => (
              <li key={line.id} className="cart-line">
                <div className="cart-line-info">
                  <span className="cart-line-name">{line.name}</span>
                  <span className="cart-line-price">{formatPrice(line.price)} each</span>
                </div>

                <div className="cart-line-controls">
                  <button
                    type="button"
                    className="icon-button"
                    onClick={() => updateQuantity(line.id, line.quantity - 1)}
                    aria-label={`Decrease ${line.name}`}
                  >
                    <FiMinus />
                  </button>
                  <input
                    type="number"
                    min="0"
                    className="qty-input small"
                    value={line.quantity}
                    onChange={(e) => updateQuantity(line.id, Number(e.target.value))}
                    aria-label={`${line.name} quantity`}
                  />
                  <button
                    type="button"
                    className="icon-button"
                    onClick={() => updateQuantity(line.id, line.quantity + 1)}
                    aria-label={`Increase ${line.name}`}
                  >
                    <FiPlus />
                  </button>
                  <button
                    type="button"
                    className="icon-button danger"
                    onClick={() => removeFromCart(line.id)}
                    aria-label={`Remove ${line.name}`}
                  >
                    <FiTrash2 />
                  </button>
                </div>

                <span className="cart-line-total">{formatPrice(line.price * line.quantity)}</span>
              </li>
            ))}
          </ul>
        )}

        <div className="cart-footer">
          <div className="cart-total">
            <span>Subtotal</span>
            <span>{formatPrice(cartTotal)}</span>
          </div>
          <button
            type="button"
            className="primary-button"
            disabled={cart.length === 0}
            onClick={handleCheckout}
          >
            Checkout
          </button>
        </div>
      </aside>
    </>
  )
}

export default Cart
