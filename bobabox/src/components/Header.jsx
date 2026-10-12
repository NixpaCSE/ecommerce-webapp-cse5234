import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { FiMenu, FiShoppingBag, FiX } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'

const navLinks = [
  { to: '/', label: 'Home', end: true },
  { to: '/purchase', label: 'Products' },
  { to: '/about', label: 'About Us' },
  { to: '/contact', label: 'Contact Us' },
]

function Header({ onCartClick }) {
  const { cartCount } = useOrder()
  const [menuOpen, setMenuOpen] = useState(false)
  const closeMenu = () => setMenuOpen(false)

  return (
    <header className="header">
      <Link to="/" className="brand" aria-label="boba.box home" onClick={closeMenu}>
        boba<span className="brand-dot" aria-hidden="true" />box
      </Link>

      <nav className={`main-nav ${menuOpen ? 'open' : ''}`} aria-label="Main">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            onClick={closeMenu}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="header-actions">
        <button type="button" className="cart-button" onClick={onCartClick}>
          <FiShoppingBag size={18} />
          <span>cart</span>
          {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
        </button>
        <button
          type="button"
          className="icon-button menu-toggle"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
        >
          {menuOpen ? <FiX size={22} /> : <FiMenu size={22} />}
        </button>
      </div>
    </header>
  )
}

export default Header
