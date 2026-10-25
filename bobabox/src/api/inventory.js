const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'https://74ltdmx4t1.execute-api.us-east-1.amazonaws.com/test'
).replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

async function request(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  let payload

  try {
    payload = await response.json()
  } catch {
    throw new Error(`The API returned an invalid JSON response (${response.status}).`)
  }

  if (!response.ok) {
    throw new ApiError(payload.message || `The API request failed (${response.status}).`, response.status, payload)
  }

  return payload
}

export async function fetchInventory(options) {
  const inventory = await request('/inventory-management/inventory/', options)
  if (!Array.isArray(inventory)) {
    throw new Error('The inventory API returned an unexpected response.')
  }
  return inventory
}

export function submitOrder({ cart, payment, shipping }) {
  // text/plain keeps this a simple CORS request. The deployed OPTIONS method
  // currently allows GET and OPTIONS only, so an application/json POST is
  // blocked by the browser before the confirmation number can come back.
  // The Lambda still parses the JSON string body.
  return request('/order-processing/order', {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: JSON.stringify({
      items: cart.map(({ id, quantity }) => ({ id, quantity })),
      // This demo API does not process payments. Never send CVV or full card details.
      payment: { creditCardNumber: payment.creditCardNumber.slice(-4) },
      shipping,
    }),
  })
}
