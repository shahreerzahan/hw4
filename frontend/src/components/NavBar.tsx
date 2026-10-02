import { Link, NavLink } from 'react-router-dom'

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'nav-link active' : 'nav-link'

export default function NavBar() {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">CC</span>
          <span className="brand-name">Campus Customs</span>
        </Link>
        <nav className="nav-links">
          <NavLink to="/" end className={navClass}>Home</NavLink>
          <NavLink to="/products" className={navClass}>Products</NavLink>
          <NavLink to="/about" className={navClass}>About Us</NavLink>
        </nav>
        <div className="nav-auth">
          <NavLink to="/login" className={navClass}>Log in</NavLink>
          <NavLink to="/create-account" className="btn btn-light">Create account</NavLink>
        </div>
      </div>
    </header>
  )
}
