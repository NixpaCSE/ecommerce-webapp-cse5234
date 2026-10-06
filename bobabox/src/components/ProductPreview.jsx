import { useEffect, useState } from 'react'
import { FiCheck, FiX } from 'react-icons/fi'
import { useOrder } from '../context/useOrder.js'
import { formatPrice } from '../utils/format.js'

// Quick-view popup with the product photo. Lets the user add to cart from here too.
function ProductPreview({ product, onClose }) {
  const { addToCart } = useOrder()
  const [quantity, setQuantity] = useState(1)
  const [added, setAdded] = useState(false)

  useEffect(() => {
    function handleKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [onClose])

  function handleSubmit(e) {
    e.preventDefault()
    if (quantity <= 0) return
    addToCart(product, quantity)
    setAdded(true)
    setTimeout(onClose, 700)
  }

  return (
    <div className="preview-overlay" onClick={onClose}>
      <div
        className="preview-modal"
        role="dialog"
        aria-modal="true"
        aria-label={product.name}
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="icon-button preview-close" onClick={onClose} aria-label="Close preview">
          <FiX size={22} />
        </button>

        <div className="preview-image" style={{ '--swatch': product.gradient }}>
          <img src={product.image} alt={product.name} />
        </div>

        <form className="preview-details" onSubmit={handleSubmit}>
          <h2 className="preview-name">{product.name}</h2>
          <p className="preview-price">{formatPrice(product.price)}</p>
          <p className="preview-description">{product.description}</p>

          <div className="preview-actions">
            <label className="qty-label">
              Qty
              <input
                type="number"
                min="0"
                className="qty-input"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(0, Math.floor(Number(e.target.value) || 0)))}
              />
            </label>
            <button type="submit" className="primary-button" disabled={quantity <= 0 || added}>
              {added ? (
                <>
                  <FiCheck /> Added
                </>
              ) : (
                'Add to cart'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ProductPreview
