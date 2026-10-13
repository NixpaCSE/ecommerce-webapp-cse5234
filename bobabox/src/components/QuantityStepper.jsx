export const MAX_QUANTITY = 99

export function clampQuantity(value) {
  return Math.min(MAX_QUANTITY, Math.max(0, value))
}

function QuantityStepper({ id, value, onStep }) {
  const atMin = value <= 0
  const atMax = value >= MAX_QUANTITY

  return (
    <div className="qty-stepper">
      <button
        type="button"
        className="qty-step"
        onClick={() => onStep(-1)}
        disabled={atMin}
        aria-label="Decrease quantity"
        aria-controls={id}
      >
        −
      </button>
      <span id={id} className="qty-value" aria-live="polite">
        {value}
      </span>
      <button
        type="button"
        className="qty-step"
        onClick={() => onStep(1)}
        disabled={atMax}
        aria-label="Increase quantity"
        aria-controls={id}
      >
        +
      </button>
    </div>
  )
}

export default QuantityStepper
