import { useCallback, useEffect, useState } from 'react'
import { OrderContext } from './OrderContext.js'
import { fetchInventory } from '../api/inventory.js'

// Shared state for the whole site: products (from the inventory API), cart, payment, shipping.
// Use it in any component with: const { products, cart, payment, setPayment, ... } = useOrder()

const CART_STORAGE_KEY = 'bobabox-cart'

const emptyPayment = {
  creditCardNumber: '',
  expirationDate: '',
  cvvCode: '',
  cardHolderName: '',
}

const emptyShipping = {
  name: '',
  email: '',
  addressLine1: '',
  addressLine2: '',
  city: '',
  state: '',
  zip: '',
}

// The API uses string ids; carts saved before Lab 7 used numbers.
function loadCart() {
  try {
    const saved = JSON.parse(localStorage.getItem(CART_STORAGE_KEY)) ?? []
    return saved.map((line) => ({ ...line, id: String(line.id) }))
  } catch {
    return []
  }
}

export function OrderProvider({ children }) {
  // products: [{ id, name, image, description, price, quantity, gradient }] from the inventory API
  const [products, setProducts] = useState([])
  const [productsLoading, setProductsLoading] = useState(true)
  const [productsError, setProductsError] = useState('')
  // cart: [{ id, name, price, quantity }]
  const [cart, setCart] = useState(loadCart)
  const [payment, setPayment] = useState(emptyPayment)
  const [shipping, setShipping] = useState(emptyShipping)
  const [orderConfirmation, setOrderConfirmation] = useState(null)

  const loadProducts = useCallback((signal) => {
    return fetchInventory({ signal })
      .then((items) => {
        setProducts(items.map((item) => ({ ...item, id: String(item.id) })))
        setProductsError('')
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setProductsError(error.message)
      })
      .finally(() => {
        if (!signal?.aborted) setProductsLoading(false)
      })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    loadProducts(controller.signal)
    return () => controller.abort()
  }, [loadProducts])

  // Re-fetch stock after an order so the products page shows the new quantities.
  const reloadProducts = useCallback(() => loadProducts(), [loadProducts])

  const getProduct = (id) => products.find((product) => product.id === String(id))

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart))
  }, [cart])

  function addToCart(product, quantity) {
    if (quantity <= 0) return
    const id = String(product.id)
    setCart((prev) => {
      const existing = prev.find((line) => line.id === id)
      if (existing) {
        return prev.map((line) =>
          line.id === id ? { ...line, quantity: line.quantity + quantity } : line,
        )
      }
      return [...prev, { id, name: product.name, price: product.price, quantity }]
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

  function clearCart() {
    setCart([])
  }

  function resetOrder() {
    clearCart()
    setPayment(emptyPayment)
    setShipping(emptyShipping)
    setOrderConfirmation(null)
  }

  const cartCount = cart.reduce((sum, line) => sum + line.quantity, 0)
  const cartTotal = cart.reduce((sum, line) => sum + line.price * line.quantity, 0)

  const value = {
    products,
    productsLoading,
    productsError,
    getProduct,
    reloadProducts,
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
    orderConfirmation,
    setOrderConfirmation,
    clearCart,
    resetOrder,
  }

  return <OrderContext.Provider value={value}>{children}</OrderContext.Provider>
}
