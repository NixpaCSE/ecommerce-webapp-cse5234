import { Link } from 'react-router-dom'
import Bubbles from './Bubbles.jsx'

const columns = [
  {
    title: 'shop',
    links: [
      { to: '/', label: 'Home' },
      { to: '/purchase', label: 'All kits' },
    ],
  },
  {
    title: 'company',
    links: [
      { to: '/about', label: 'About us' },
      { to: '/contact', label: 'Contact us' },
    ],
  },
  {
    title: 'help',
    links: [
      { to: '/contact', label: 'Returns' },
      { to: '/contact', label: 'FAQ' },
    ],
  },
]

function Footer() {
  return (
    <footer className="footer">
      <Bubbles />
      <div className="footer-inner">
        <div className="footer-top">
          <div className="footer-about">
            <Link to="/" className="brand" aria-label="boba.box home">
              boba<span className="brand-dot" aria-hidden="true" />box
            </Link>
            <p>The perfect kit, delivered to your door.</p>
          </div>

          <nav className="footer-columns" aria-label="Footer">
            {columns.map((column) => (
              <div key={column.title} className="footer-column">
                <h2>{column.title}</h2>
                {column.links.map((link) => (
                  <Link key={link.label} to={link.to}>
                    {link.label}
                  </Link>
                ))}
              </div>
            ))}
          </nav>
        </div>

        <div className="footer-bottom">
          <span>© 2026 boba.box</span>
          <span>A class project for CSE 5234. Not a real store.</span>
        </div>
      </div>
    </footer>
  )
}

export default Footer
