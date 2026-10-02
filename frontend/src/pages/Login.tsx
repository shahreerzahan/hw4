import { Link } from 'react-router-dom'

// Placeholder: login is built in Problem 4.
export default function Login() {
  return (
    <section className="section auth-page">
      <div className="auth-card">
        <h1>Welcome back! 👋</h1>
        <p className="muted">Logging in is coming soon. Hang tight, Bulldog.</p>
        <p className="muted">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </div>
    </section>
  )
}
