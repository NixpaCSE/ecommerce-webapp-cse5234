import { Link } from 'react-router-dom'
import { FiShoppingBag } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'

function Header({ onCartClick }) {
  const { cartCount } = useOrder()

  return (
    <header className="header">
      <Link to="/purchase" className="brand" aria-label="boba.box home">
        boba<span className="brand-dot" aria-hidden="true" />box
      </Link>

      <button type="button" className="cart-button" onClick={onCartClick}>
        <FiShoppingBag size={18} />
        <span>cart</span>
        {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
      </button>
    </header>
  )
}

export default Header
