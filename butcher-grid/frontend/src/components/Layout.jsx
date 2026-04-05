import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const loc = useLocation()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const isRegulator = user?.role === 'regulator'

  const navItems = isRegulator
    ? [{ label: 'Dashboard', path: '/regulator' }, { label: 'Alerts', path: '/regulator/alerts' }]
    : [{ label: 'Dashboard', path: '/farm' }, { label: 'Log Medication', path: '/farm/medication' }, { label: 'Log Waste', path: '/farm/waste' }]

  return (
    <div style={styles.shell}>
      <nav style={styles.nav}>
        <div style={styles.navLeft}>
          <div style={styles.logo}>BG</div>
          <span style={styles.brand}>Butcher Grid</span>
          <div style={styles.navLinks}>
            {navItems.map(item => (
              <button
                key={item.path}
                style={{ ...styles.navLink, ...(loc.pathname === item.path ? styles.navLinkActive : {}) }}
                onClick={() => navigate(item.path)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <div style={styles.navRight}>
          <span style={styles.roleTag}>{user?.role?.replace('_', ' ')}</span>
          <span style={styles.userName}>{user?.username}</span>
          <button style={styles.logoutBtn} onClick={handleLogout}>Sign out</button>
        </div>
      </nav>
      <main style={styles.main}>{children}</main>
    </div>
  )
}

const styles = {
  shell: { display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' },
  nav: {
    height: 56, borderBottom: '1px solid var(--border)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '0 24px', background: 'var(--bg2)', flexShrink: 0,
  },
  navLeft: { display: 'flex', alignItems: 'center', gap: 24 },
  logo: {
    width: 32, height: 32, background: 'var(--accent)', borderRadius: 8,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontFamily: 'var(--font-head)', fontWeight: 800, fontSize: 13, color: '#0a0a0a',
  },
  brand: { fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 16 },
  navLinks: { display: 'flex', gap: 4 },
  navLink: {
    padding: '6px 14px', background: 'none', border: 'none',
    color: 'var(--muted)', borderRadius: 6, fontSize: 13,
    transition: 'color 0.2s, background 0.2s',
  },
  navLinkActive: { color: 'var(--text)', background: 'var(--bg3)' },
  navRight: { display: 'flex', alignItems: 'center', gap: 12 },
  roleTag: {
    padding: '3px 10px', borderRadius: 999, border: '1px solid var(--border2)',
    fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--accent)', textTransform: 'uppercase',
  },
  userName: { color: 'var(--muted)', fontSize: 13 },
  logoutBtn: {
    padding: '6px 14px', background: 'none', border: '1px solid var(--border2)',
    borderRadius: 6, color: 'var(--muted)', fontSize: 12,
  },
  main: { flex: 1, overflow: 'auto', padding: 28 },
}
