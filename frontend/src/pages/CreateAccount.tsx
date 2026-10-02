import { Link } from 'react-router-dom'

// Placeholder: account creation is built in Problem 4.
export default function CreateAccount() {
  return (
    <section className="section auth-page">
      <div className="auth-card">
        <h1>Join the Bulldog Family 💙</h1>
        <p className="muted">Creating an account is coming soon. We can't wait to have you!</p>
        <p className="muted">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </section>
  )
}
