import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../components/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const user = await login(form.username, form.password)
      if (user.role === 'regulator') navigate('/regulator')
      else navigate('/farm')
    } catch (err) {
      setError('Invalid credentials. Try again.')
    } finally {
      setLoading(false)
    }
  }

  function fillDemo(username) {
    setForm({ username, password: 'demo1234' })
  }

  return (
    <div style={styles.page}>
      <div style={styles.left}>
        <div style={styles.brand}>
          <div style={styles.logo}>BG</div>
          <h1 style={styles.title}>Butcher Grid</h1>
          <p style={styles.tagline}>Making every rupee worthy of your health and moral conscience.</p>
        </div>
        <div style={styles.pills}>
          {['One Health', 'AMR Monitoring', 'Real-time Risk', 'Consumer Trust'].map(t => (
            <span key={t} style={styles.pill}>{t}</span>
          ))}
        </div>
        <div style={styles.stats}>
          <div style={styles.stat}><span style={styles.statNum}>6</span><span style={styles.statLabel}>Facilities</span></div>
          <div style={styles.stat}><span style={styles.statNum}>8</span><span style={styles.statLabel}>Batches</span></div>
          <div style={styles.stat}><span style={styles.statNum}>AI</span><span style={styles.statLabel}>Risk Scoring</span></div>
        </div>
      </div>

      <div style={styles.right}>
        <form style={styles.form} onSubmit={handleSubmit}>
          <h2 style={styles.formTitle}>Sign in</h2>
          <p style={styles.formSub}>Choose a demo account below or enter credentials</p>

          <div style={styles.demoRow}>
            {[
              { label: 'Regulator', user: 'fssai_inspector' },
              { label: 'Farm Owner', user: 'rajan_poultry' },
              { label: 'Non-compliant', user: 'meera_meats' },
            ].map(d => (
              <button key={d.user} type="button" style={styles.demoBtn} onClick={() => fillDemo(d.user)}>
                {d.label}
              </button>
            ))}
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Username</label>
            <input
              style={styles.input}
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              placeholder="username"
              autoComplete="username"
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              style={styles.input}
              type="password"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          {error && <p style={styles.error}>{error}</p>}

          <button style={styles.submit} type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in →'}
          </button>

          <p style={{ color: 'var(--muted)', marginTop: 16, fontSize: 12, textAlign: 'center' }}>
            All passwords: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>demo1234</span>
          </p>
        </form>
      </div>
    </div>
  )
}

const styles = {
  page: { display: 'flex', height: '100vh', overflow: 'hidden' },
  left: {
    flex: 1, background: 'var(--bg2)', borderRight: '1px solid var(--border)',
    display: 'flex', flexDirection: 'column', justifyContent: 'center',
    padding: '60px 56px', gap: 40,
  },
  brand: { display: 'flex', flexDirection: 'column', gap: 16 },
  logo: {
    width: 56, height: 56, background: 'var(--accent)', borderRadius: 12,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontFamily: 'var(--font-head)', fontWeight: 800, fontSize: 20, color: '#0a0a0a',
  },
  title: { fontFamily: 'var(--font-head)', fontSize: 40, fontWeight: 800, lineHeight: 1.1 },
  tagline: { color: 'var(--muted)', fontSize: 15, maxWidth: 360, lineHeight: 1.6 },
  pills: { display: 'flex', flexWrap: 'wrap', gap: 8 },
  pill: {
    padding: '6px 14px', borderRadius: 999, border: '1px solid var(--border2)',
    fontSize: 12, color: 'var(--muted)', fontFamily: 'var(--font-mono)',
  },
  stats: { display: 'flex', gap: 32 },
  stat: { display: 'flex', flexDirection: 'column', gap: 2 },
  statNum: { fontFamily: 'var(--font-head)', fontSize: 32, fontWeight: 800, color: 'var(--accent)' },
  statLabel: { color: 'var(--muted)', fontSize: 12 },
  right: {
    width: 480, display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: 40,
  },
  form: { width: '100%', maxWidth: 360, display: 'flex', flexDirection: 'column', gap: 16 },
  formTitle: { fontFamily: 'var(--font-head)', fontSize: 28, fontWeight: 700 },
  formSub: { color: 'var(--muted)', fontSize: 13, marginTop: -8 },
  demoRow: { display: 'flex', gap: 8 },
  demoBtn: {
    flex: 1, padding: '8px 0', background: 'var(--bg3)', border: '1px solid var(--border2)',
    borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: 12,
    fontFamily: 'var(--font-mono)', transition: 'border-color 0.2s',
  },
  field: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 12, color: 'var(--muted)', fontFamily: 'var(--font-mono)' },
  input: {
    padding: '12px 14px', background: 'var(--bg3)', border: '1px solid var(--border2)',
    borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: 14, outline: 'none',
    transition: 'border-color 0.2s',
  },
  error: { color: 'var(--danger)', fontSize: 13 },
  submit: {
    padding: '14px', background: 'var(--accent)', border: 'none',
    borderRadius: 'var(--radius)', color: '#0a0a0a', fontWeight: 600,
    fontSize: 15, fontFamily: 'var(--font-head)', transition: 'background 0.2s',
  },
}
