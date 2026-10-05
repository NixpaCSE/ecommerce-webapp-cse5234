import { useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import Header from './components/Header.jsx'
import Cart from './components/Cart.jsx'
import Purchase from './components/Purchase.jsx'
import PaymentEntry from './components/PaymentEntry.jsx'
import ShippingEntry from './components/ShippingEntry.jsx'
import ViewOrder from './components/ViewOrder.jsx'
import Confirmation from './components/Confirmation.jsx'

function App() {
  const [cartOpen, setCartOpen] = useState(false)

  return (
    <div className="app">
      <Header onCartClick={() => setCartOpen(true)} />
      <Cart open={cartOpen} onClose={() => setCartOpen(false)} />

      <main className="page">
        <Routes>
          <Route path="/" element={<Navigate to="/purchase" replace />} />
          <Route path="/purchase" element={<Purchase />} />
          <Route path="/purchase/paymentEntry" element={<PaymentEntry />} />
          <Route path="/purchase/shippingEntry" element={<ShippingEntry />} />
          <Route path="/purchase/viewOrder" element={<ViewOrder />} />
          <Route path="/purchase/viewConfirmation" element={<Confirmation />} />
          <Route path="*" element={<Navigate to="/purchase" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
