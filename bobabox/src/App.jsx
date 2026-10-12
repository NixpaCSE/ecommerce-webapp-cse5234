import { useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import './App.css'
import Header from './components/Header.jsx'
import Cart from './components/Cart.jsx'
import Home from './components/Home.jsx'
import Purchase from './components/Purchase.jsx'
import PaymentEntry from './components/PaymentEntry.jsx'
import ShippingEntry from './components/ShippingEntry.jsx'
import ViewOrder from './components/ViewOrder.jsx'
import Confirmation from './components/Confirmation.jsx'
import About from './components/About.jsx'
import Contact from './components/Contact.jsx'
import Footer from './components/Footer.jsx'

function App() {
  const [cartOpen, setCartOpen] = useState(false)
  const { pathname } = useLocation()

  return (
    <div className="app">
      <Header onCartClick={() => setCartOpen(true)} />
      <Cart open={cartOpen} onClose={() => setCartOpen(false)} />

      <main className={pathname === '/' ? 'page-full' : 'page'}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/purchase" element={<Purchase />} />
          <Route path="/purchase/paymentEntry" element={<PaymentEntry />} />
          <Route path="/purchase/shippingEntry" element={<ShippingEntry />} />
          <Route path="/purchase/viewOrder" element={<ViewOrder />} />
          <Route path="/purchase/viewConfirmation" element={<Confirmation />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <Footer />
    </div>
  )
}

export default App
