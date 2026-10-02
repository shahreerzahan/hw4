import { Link } from 'react-router-dom'
import DanTheBulldog from '../components/DanTheBulldog'

export default function NotFound() {
  return (
    <section className="section auth-page">
      <div className="auth-card">
        <DanTheBulldog className="dan" />
        <h1>Oops, wrong turn.</h1>
        <p className="muted">This page wandered off campus.</p>
        <Link to="/" className="btn btn-primary">Take me home</Link>
      </div>
    </section>
  )
}
