function Swatch({ gradient, size = 'large' }) {
  return (
    <div className={`swatch swatch-${size}`} style={{ '--swatch': gradient }}>
      <div className="swatch-glow" aria-hidden="true" />
      <div className="swatch-circle" />
    </div>
  )
}

export default Swatch
