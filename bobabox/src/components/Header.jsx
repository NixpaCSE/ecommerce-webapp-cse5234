import { Link } from 'react-router-dom'
import { FiShoppingCart } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'

function Header({ onCartClick }) {
  const { cartCount } = useOrder()

  return (
    <header className="header">
      <Link to="/purchase" className="brand">
        <span className="brand-dot" aria-hidden="true" />
        BobaBox
      </Link>

      <button type="button" className="cart-button" onClick={onCartClick}>
        <FiShoppingCart size={20} />
        <span>Cart</span>
        {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
      </button>
    </header>
  )
}

export default Header
