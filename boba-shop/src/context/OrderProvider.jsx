import { useEffect, useState } from 'react'
import { OrderContext } from './OrderContext.js'

// Shared order state for all 5 pages (cart, payment, shipping).
// Use it in any component with: const { cart, payment, setPayment, ... } = useOrder()

const CART_STORAGE_KEY = 'boba-shop-cart'

const emptyPayment = {
  creditCardNumber: '',
  expirationDate: '',
  cvvCode: '',
  cardHolderName: '',
}

const emptyShipping = {
  name: '',
  addressLine1: '',
  addressLine2: '',
  city: '',
  state: '',
  zip: '',
}

function loadCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_STORAGE_KEY)) ?? []
  } catch {
    return []
  }
}

export function OrderProvider({ children }) {
  // cart: [{ id, name, price, quantity }]
  const [cart, setCart] = useState(loadCart)
  const [payment, setPayment] = useState(emptyPayment)
  const [shipping, setShipping] = useState(emptyShipping)

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart))
  }, [cart])

  function addToCart(product, quantity) {
    if (quantity <= 0) return
    setCart((prev) => {
      const existing = prev.find((line) => line.id === product.id)
      if (existing) {
        return prev.map((line) =>
          line.id === product.id ? { ...line, quantity: line.quantity + quantity } : line,
        )
      }
      return [...prev, { id: product.id, name: product.name, price: product.price, quantity }]
    })
  }

  function updateQuantity(id, quantity) {
    if (quantity <= 0) {
      removeFromCart(id)
      return
    }
    setCart((prev) => prev.map((line) => (line.id === id ? { ...line, quantity } : line)))
  }

  function removeFromCart(id) {
    setCart((prev) => prev.filter((line) => line.id !== id))
  }

  function resetOrder() {
    setCart([])
    setPayment(emptyPayment)
    setShipping(emptyShipping)
  }

  const cartCount = cart.reduce((sum, line) => sum + line.quantity, 0)
  const cartTotal = cart.reduce((sum, line) => sum + line.price * line.quantity, 0)

  const value = {
    cart,
    cartCount,
    cartTotal,
    addToCart,
    updateQuantity,
    removeFromCart,
    payment,
    setPayment,
    shipping,
    setShipping,
    resetOrder,
  }

  return <OrderContext.Provider value={value}>{children}</OrderContext.Provider>
}
