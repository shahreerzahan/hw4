import { Link, NavLink, useNavigate } from 'react-router-dom'
import DanTheBulldog from './DanTheBulldog'
import { useAuth } from '../auth'

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'nav-link active' : 'nav-link'

export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="brand">
          <DanTheBulldog className="brand-dan" />
          <span className="brand-name">Campus Customs</span>
        </Link>
        <nav className="nav-links">
          <NavLink to="/" end className={navClass}>Home</NavLink>
          <NavLink to="/products" className={navClass}>Products</NavLink>
          <NavLink to="/about" className={navClass}>About Us</NavLink>
        </nav>
        <div className="nav-auth">
          {loading ? null : user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button type="button" className="btn btn-ghost" onClick={onLogout}>Log out</button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={navClass}>Log in</NavLink>
              <NavLink to="/create-account" className="btn btn-primary">Create account</NavLink>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
