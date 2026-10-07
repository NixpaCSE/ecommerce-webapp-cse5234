import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiCheck, FiShoppingBag } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'

function Confirmation() {
  const { cart, cartTotal, payment, shipping, resetOrder } = useOrder()
  const navigate = useNavigate()

  const confirmationNumber = useMemo(
    () => `BBA-${Date.now().toString().slice(-8)}`,
    [],
  )

  function handleNewOrder() {
    resetOrder()
    navigate('/purchase')
  }

  return (
    <section className="checkout-page confirmation-page">
      <div className="confirmation-status">
        <div className="confirmation-icon">
          <FiCheck />
        </div>
        <p className="checkout-kicker">order received</p>
        <h1 className="checkout-title">thank you, {shipping.name.split(' ')[0]}.</h1>
        <p className="confirmation-message">
          Your order is confirmed and a receipt has been sent to {payment.cardHolderName}.
        </p>
      </div>

      <div className="checkout-card confirmation-card">
        <div className="confirmation-number">
          <span>confirmation number</span>
          <strong>{confirmationNumber}</strong>
        </div>

        <div className="confirmation-summary">
          <div className="confirmation-summary-header">
            <FiShoppingBag />
            <span>{cart.reduce((sum, line) => sum + line.quantity, 0)} items</span>
          </div>

          <ul className="order-lines">
            {cart.map((line) => (
              <li key={line.id} className="order-line">
                <div className="order-line-main">
                  <span className="order-line-name">{line.name}</span>
                  <span className="order-line-meta">
                    Qty {line.quantity} · {formatPrice(line.price)} each
                  </span>
                </div>
                <strong>{formatPrice(line.price * line.quantity)}</strong>
              </li>
            ))}
          </ul>

          <div className="order-total">
            <span>total paid</span>
            <strong>{formatPrice(cartTotal)}</strong>
          </div>
        </div>

        <div className="confirmation-address">
          <h2>shipping to</h2>
          <p>
            {shipping.name}
            <br />
            {shipping.addressLine1}
            {shipping.addressLine2 && `, ${shipping.addressLine2}`}
            <br />
            {shipping.city}, {shipping.state} {shipping.zip}
          </p>
        </div>
      </div>

      <button type="button" className="primary-button confirmation-button" onClick={handleNewOrder}>
        Start another order
      </button>
    </section>
  )
}

export default Confirmation
