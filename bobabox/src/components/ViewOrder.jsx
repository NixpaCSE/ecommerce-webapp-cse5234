import { useNavigate } from 'react-router-dom'
import { FiArrowLeft, FiArrowRight, FiCheck } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'

function formatCardNumber(value) {
  const digits = value.replace(/\D/g, '')
  return `•••• ${digits.slice(-4)}`
}

function ViewOrder() {
  const { cart, cartTotal, payment, shipping } = useOrder()
  const navigate = useNavigate()

  function handleConfirm() {
    navigate('/purchase/viewConfirmation')
  }

  return (
    <section className="checkout-page">
      <div className="checkout-heading">
        <p className="checkout-kicker">step 3 of 3</p>
        <h1 className="checkout-title">review your order</h1>
      </div>

      <div className="checkout-grid">
        <div className="checkout-card review-card">
          <div className="section-heading">
            <h2>order summary</h2>
            <button type="button" className="text-button" onClick={() => navigate('/purchase')}>
              edit cart
            </button>
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
            <span>total</span>
            <strong>{formatPrice(cartTotal)}</strong>
          </div>
        </div>

        <div className="checkout-card details-card">
          <div className="section-heading">
            <h2>payment</h2>
            <button
              type="button"
              className="text-button"
              onClick={() => navigate('/purchase/paymentEntry')}
            >
              edit
            </button>
          </div>
          <dl className="details-list">
            <div>
              <dt>cardholder</dt>
              <dd>{payment.cardHolderName}</dd>
            </div>
            <div>
              <dt>card number</dt>
              <dd>{formatCardNumber(payment.creditCardNumber)}</dd>
            </div>
            <div>
              <dt>expiration</dt>
              <dd>{payment.expirationDate}</dd>
            </div>
          </dl>

          <div className="section-heading details-heading">
            <h2>shipping</h2>
            <button
              type="button"
              className="text-button"
              onClick={() => navigate('/purchase/shippingEntry')}
            >
              edit
            </button>
          </div>
          <dl className="details-list">
            <div>
              <dt>recipient</dt>
              <dd>{shipping.name}</dd>
            </div>
            <div>
              <dt>address</dt>
              <dd>
                {shipping.addressLine1}
                {shipping.addressLine2 && `, ${shipping.addressLine2}`}
                <br />
                {shipping.city}, {shipping.state} {shipping.zip}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="checkout-actions review-actions">
        <button type="button" className="secondary-button" onClick={() => navigate('/purchase/shippingEntry')}>
          <FiArrowLeft /> Back
        </button>
        <button type="button" className="primary-button" onClick={handleConfirm}>
          Place order <FiArrowRight />
        </button>
      </div>

      <p className="checkout-note">
        <FiCheck /> Secure checkout. Your payment details are never stored by this demo.
      </p>
    </section>
  )
}

export default ViewOrder
