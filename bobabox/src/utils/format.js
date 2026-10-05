const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export function formatPrice(amount) {
  return currency.format(amount)
}
