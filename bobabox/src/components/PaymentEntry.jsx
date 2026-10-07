import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOrder } from '../context/useOrder.js'

// Strip non-digits and group card number as "1234 5678 9012 3456"
const formatCardNumber = (value) =>
  value
    .replace(/\D/g, '')
    .slice(0, 19)
    .replace(/(.{4})/g, '$1 ')
    .trim()

// Auto-insert the slash: "1225" -> "12/25"
const formatExpiration = (value) => {
  const digits = value.replace(/\D/g, '').slice(0, 4)
  return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits
}

// Luhn checksum: catches most mistyped card numbers
const passesLuhn = (number) => {
  const digits = number.replace(/\s/g, '')
  let sum = 0
  let double = false
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = Number(digits[i])
    if (double) {
      d *= 2
      if (d > 9) d -= 9
    }
    sum += d
    double = !double
  }
  return digits.length >= 13 && sum % 10 === 0
}

const isExpirationValid = (value) => {
  const match = /^(\d{2})\/(\d{2})$/.exec(value)
  if (!match) return false
  const month = Number(match[1])
  const year = 2000 + Number(match[2])
  if (month < 1 || month > 12) return false
  // Card is valid through the last day of its expiration month
  const endOfMonth = new Date(year, month, 0, 23, 59, 59)
  return endOfMonth >= new Date()
}

function validate({ creditCardNumber, expirationDate, cvvCode, cardHolderName }) {
  const errors = {}
  if (!passesLuhn(creditCardNumber)) {
    errors.creditCardNumber = 'Enter a valid card number.'
  }
  if (!isExpirationValid(expirationDate)) {
    errors.expirationDate = 'Enter a future date as MM/YY.'
  }
  if (!/^\d{3,4}$/.test(cvvCode)) {
    errors.cvvCode = 'Enter the 3 or 4 digit code on your card.'
  }
  if (cardHolderName.trim().length < 2) {
    errors.cardHolderName = 'Enter the name as it appears on the card.'
  }
  return errors
}

function PaymentEntry() {
  const { setPayment } = useOrder()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    creditCardNumber: '',
    expirationDate: '',
    cvvCode: '',
    cardHolderName: '',
  })
  const [errors, setErrors] = useState({})

  const handleChange = (field, formatter) => (event) => {
    const value = formatter ? formatter(event.target.value) : event.target.value
    setForm((prev) => ({ ...prev, [field]: value }))
    // Clear the error for a field as soon as the person edits it
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const found = validate(form)
    setErrors(found)
    if (Object.keys(found).length > 0) return

    setPayment({
      creditCardNumber: form.creditCardNumber.replace(/\s/g, ''),
      expirationDate: form.expirationDate,
      cvvCode: form.cvvCode,
      cardHolderName: form.cardHolderName.trim(),
    })
    navigate('/purchase/shippingEntry')
  }

  return (
    <section>
      <h1>Payment Information</h1>

      <form className="checkout-form" onSubmit={handleSubmit} noValidate>
        {Object.keys(errors).length > 0 && (
          <p className="form-error-summary" role="alert">
            Please correct the highlighted payment details.
          </p>
        )}

        <div className="form-field">
          <label htmlFor="cardHolderName">Name on card</label>
          <input
            id="cardHolderName"
            type="text"
            autoComplete="cc-name"
            className={errors.cardHolderName ? 'invalid' : ''}
            value={form.cardHolderName}
            onChange={handleChange('cardHolderName')}
            aria-invalid={Boolean(errors.cardHolderName)}
            aria-describedby={errors.cardHolderName ? 'cardHolderName-error' : undefined}
          />
          {errors.cardHolderName && (
            <p id="cardHolderName-error" className="field-error" role="alert">
              {errors.cardHolderName}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="creditCardNumber">Card number</label>
          <input
            id="creditCardNumber"
            type="text"
            inputMode="numeric"
            autoComplete="cc-number"
            placeholder="1234 5678 9012 3456"
            className={errors.creditCardNumber ? 'invalid' : ''}
            value={form.creditCardNumber}
            onChange={handleChange('creditCardNumber', formatCardNumber)}
            aria-invalid={Boolean(errors.creditCardNumber)}
            aria-describedby={errors.creditCardNumber ? 'creditCardNumber-error' : undefined}
          />
          {errors.creditCardNumber && (
            <p id="creditCardNumber-error" className="field-error" role="alert">
              {errors.creditCardNumber}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="expirationDate">Expiration date</label>
          <input
            id="expirationDate"
            type="text"
            inputMode="numeric"
            autoComplete="cc-exp"
            placeholder="MM/YY"
            className={errors.expirationDate ? 'invalid' : ''}
            value={form.expirationDate}
            onChange={handleChange('expirationDate', formatExpiration)}
            aria-invalid={Boolean(errors.expirationDate)}
            aria-describedby={errors.expirationDate ? 'expirationDate-error' : undefined}
          />
          {errors.expirationDate && (
            <p id="expirationDate-error" className="field-error" role="alert">
              {errors.expirationDate}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="cvvCode">Security code (CVV)</label>
          <input
            id="cvvCode"
            type="password"
            inputMode="numeric"
            autoComplete="cc-csc"
            maxLength={4}
            className={errors.cvvCode ? 'invalid' : ''}
            value={form.cvvCode}
            onChange={handleChange('cvvCode', (v) => v.replace(/\D/g, ''))}
            aria-invalid={Boolean(errors.cvvCode)}
            aria-describedby={errors.cvvCode ? 'cvvCode-error' : undefined}
          />
          {errors.cvvCode && (
            <p id="cvvCode-error" className="field-error" role="alert">
              {errors.cvvCode}
            </p>
          )}
        </div>

        <button type="submit" className="primary-button">Continue to shipping</button>
      </form>
    </section>
  )
}

export default PaymentEntry