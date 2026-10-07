import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOrder } from '../context/useOrder.js'

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN',
  'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
  'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT',
  'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
]

// Allow digits and a hyphen only, e.g. "43215" or "43215-1234"
const formatZip = (value) => value.replace(/[^\d-]/g, '').slice(0, 10)

function validate({ name, addressLine1, city, state, zip }) {
  const errors = {}
  if (name.trim().length < 2) errors.name = 'Enter the recipient\u2019s full name.'
  if (addressLine1.trim().length < 3) errors.addressLine1 = 'Enter a street address.'
  if (city.trim().length < 2) errors.city = 'Enter a city.'
  if (!US_STATES.includes(state)) errors.state = 'Choose a state.'
  if (!/^\d{5}(-\d{4})?$/.test(zip)) errors.zip = 'Enter a 5 digit ZIP code or ZIP+4.'
  return errors
}

function ShippingEntry() {
  const { setShipping } = useOrder()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    zip: '',
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

    setShipping({
      name: form.name.trim(),
      addressLine1: form.addressLine1.trim(),
      addressLine2: form.addressLine2.trim(),
      city: form.city.trim(),
      state: form.state,
      zip: form.zip,
    })
    navigate('/purchase/viewOrder')
  }

  return (
    <section>
      <h1>Shipping Information</h1>

      <form className="checkout-form" onSubmit={handleSubmit} noValidate>
        {Object.keys(errors).length > 0 && (
          <p className="form-error-summary" role="alert">
            Please correct the highlighted shipping details.
          </p>
        )}

        <div className="form-field">
          <label htmlFor="name">Full name</label>
          <input
            id="name"
            type="text"
            autoComplete="name"
            className={errors.name ? 'invalid' : ''}
            value={form.name}
            onChange={handleChange('name')}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? 'name-error' : undefined}
          />
          {errors.name && <p id="name-error" className="field-error" role="alert">{errors.name}</p>}
        </div>

        <div className="form-field">
          <label htmlFor="addressLine1">Address line 1</label>
          <input
            id="addressLine1"
            type="text"
            autoComplete="address-line1"
            className={errors.addressLine1 ? 'invalid' : ''}
            value={form.addressLine1}
            onChange={handleChange('addressLine1')}
            aria-invalid={Boolean(errors.addressLine1)}
            aria-describedby={errors.addressLine1 ? 'addressLine1-error' : undefined}
          />
          {errors.addressLine1 && (
            <p id="addressLine1-error" className="field-error" role="alert">
              {errors.addressLine1}
            </p>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="addressLine2">Address line 2 (optional)</label>
          <input
            id="addressLine2"
            type="text"
            autoComplete="address-line2"
            placeholder="Apt, suite, unit"
            value={form.addressLine2}
            onChange={handleChange('addressLine2')}
          />
        </div>

        <div className="form-field">
          <label htmlFor="city">City</label>
          <input
            id="city"
            type="text"
            autoComplete="address-level2"
            className={errors.city ? 'invalid' : ''}
            value={form.city}
            onChange={handleChange('city')}
            aria-invalid={Boolean(errors.city)}
            aria-describedby={errors.city ? 'city-error' : undefined}
          />
          {errors.city && <p id="city-error" className="field-error" role="alert">{errors.city}</p>}
        </div>

        <div className="form-field">
          <label htmlFor="state">State</label>
          <select
            id="state"
            autoComplete="address-level1"
            className={errors.state ? 'invalid' : ''}
            value={form.state}
            onChange={handleChange('state')}
            aria-invalid={Boolean(errors.state)}
            aria-describedby={errors.state ? 'state-error' : undefined}
          >
            <option value="">Select a state</option>
            {US_STATES.map((abbr) => (
              <option key={abbr} value={abbr}>{abbr}</option>
            ))}
          </select>
          {errors.state && <p id="state-error" className="field-error" role="alert">{errors.state}</p>}
        </div>

        <div className="form-field">
          <label htmlFor="zip">ZIP code</label>
          <input
            id="zip"
            type="text"
            inputMode="numeric"
            autoComplete="postal-code"
            placeholder="43215"
            className={errors.zip ? 'invalid' : ''}
            value={form.zip}
            onChange={handleChange('zip', formatZip)}
            aria-invalid={Boolean(errors.zip)}
            aria-describedby={errors.zip ? 'zip-error' : undefined}
          />
          {errors.zip && <p id="zip-error" className="field-error" role="alert">{errors.zip}</p>}
        </div>

        <button type="submit" className="primary-button">Review order</button>
      </form>
    </section>
  )
}

export default ShippingEntry
