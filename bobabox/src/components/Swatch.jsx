function Swatch({ gradient, image, alt, size = 'large' }) {
  return (
    <div className={`swatch swatch-${size}`} style={{ '--swatch': gradient }}>
      <div className="swatch-glow" aria-hidden="true" />
      <div className="swatch-circle" />
      {image && <img className="swatch-image" src={image} alt={alt} />}
    </div>
  )
}

export default Swatch
