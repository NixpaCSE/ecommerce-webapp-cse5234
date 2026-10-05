const pearlPositions = [
  [38, 112], [50, 116], [62, 112], [74, 116], [86, 112],
  [44, 102], [56, 106], [68, 102], [80, 106],
]

function BobaCup({ teaColor, pearlColor, size = 120 }) {
  return (
    <svg
      width={size}
      height={size * 1.15}
      viewBox="0 0 124 142"
      role="img"
      aria-hidden="true"
    >
      <rect x="66" y="2" width="9" height="56" rx="3" fill="#e46a6a" transform="rotate(12 70 30)" />
      <path d="M20 34 H104 L94 132 Q93 138 87 138 H37 Q31 138 30 132 Z" fill="#ffffff" opacity="0.65" />
      <path d="M24 50 H100 L92 130 Q91 134 86 134 H38 Q33 134 32 130 Z" fill={teaColor} />
      {pearlPositions.map(([cx, cy]) => (
        <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="6" fill={pearlColor} />
      ))}
      <rect x="14" y="28" width="96" height="10" rx="5" fill="#ffffff" stroke="#e9dccb" />
    </svg>
  )
}

export default BobaCup
