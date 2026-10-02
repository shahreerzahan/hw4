import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import DanTheBulldog from '../components/DanTheBulldog'
import { useAuth } from '../auth'

const MIN_PASSWORD_LENGTH = 8

export default function CreateAccount() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!form.first_name.trim() || !form.last_name.trim()) return setError('Please enter your first and last name.')
    if (form.password.length < MIN_PASSWORD_LENGTH)
      return setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`)
    if (form.password !== form.confirm) return setError("Those passwords don't match.")

    setSubmitting(true)
    try {
      const { confirm: _confirm, ...input } = form
      await register(input)
      navigate('/products')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  const mismatch = form.confirm.length > 0 && form.password !== form.confirm

  return (
    <section className="section auth-page">
      <div className="auth-card">
        <DanTheBulldog className="dan" />
        <h1>Join the Bulldog family.</h1>
        <p className="muted">Create an account in seconds. Dan's already wagging his tail.</p>

        <form className="auth-form" onSubmit={onSubmit} noValidate>
          <div className="field-row">
            <label className="field">
              <span>First name</span>
              <input autoComplete="given-name" value={form.first_name} onChange={update('first_name')} required />
            </label>
            <label className="field">
              <span>Last name</span>
              <input autoComplete="family-name" value={form.last_name} onChange={update('last_name')} required />
            </label>
          </div>
          <label className="field">
            <span>Email</span>
            <input type="email" autoComplete="email" value={form.email} onChange={update('email')} required />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={update('password')}
              minLength={MIN_PASSWORD_LENGTH}
              required
            />
            <small className="field-hint">At least {MIN_PASSWORD_LENGTH} characters.</small>
          </label>
          <label className="field">
            <span>Confirm password</span>
            <input
              type="password"
              autoComplete="new-password"
              value={form.confirm}
              onChange={update('confirm')}
              aria-invalid={mismatch}
              required
            />
            {mismatch && <small className="field-hint field-hint-error">Passwords don't match yet.</small>}
          </label>

          {error && <p className="form-error" role="alert">{error}</p>}

          <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={submitting}>
            {submitting ? 'Creating your account…' : 'Create account'}
          </button>
        </form>

        <p className="muted auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </section>
  )
}
