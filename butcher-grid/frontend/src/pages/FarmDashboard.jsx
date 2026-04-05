import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import Layout from '../components/Layout'

function RiskBadge({ score }) {
  const color = score >= 0.75 ? 'var(--danger)' : score >= 0.45 ? 'var(--warn)' : 'var(--safe)'
  const label = score >= 0.75 ? 'High Risk' : score >= 0.45 ? 'Warning' : 'Safe'
  return (
    <span style={{ color, fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 500 }}>
      ● {label} ({score.toFixed(2)})
    </span>
  )
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div style={styles.statCard}>
      <span style={{ ...styles.statNum, color: accent || 'var(--accent)' }}>{value}</span>
      <span style={styles.statLabel}>{label}</span>
      {sub && <span style={styles.statSub}>{sub}</span>}
    </div>
  )
}

export default function FarmDashboard() {
  const navigate = useNavigate()
  const [facilities, setFacilities] = useState([])
  const [batches, setBatches] = useState([])
  const [alerts, setAlerts] = useState([])
  const [medications, setMedications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getFacilities(),
      api.getBatches(),
      api.getAlerts(),
      api.getMedications(),
    ]).then(([f, b, a, m]) => {
      setFacilities(f)
      setBatches(b)
      setAlerts(a)
      setMedications(m)
    }).finally(() => setLoading(false))
  }, [])

  const openAlerts = alerts.filter(a => !a.is_resolved)
  const flaggedMeds = medications.filter(m => m.risk_flag)

  if (loading) return <Layout><div style={styles.loading}>Loading...</div></Layout>

  return (
    <Layout>
      <div style={styles.page}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>Farm Dashboard</h1>
            <p style={styles.sub}>Monitor your facilities, batches and compliance status</p>
          </div>
          <div style={styles.actions}>
            <button style={styles.btnSecondary} onClick={() => navigate('/farm/medication')}>+ Log Medication</button>
            <button style={styles.btnPrimary} onClick={() => navigate('/farm/waste')}>+ Log Waste</button>
          </div>
        </div>

        {/* Stats */}
        <div style={styles.statsRow}>
          <StatCard label="Facilities" value={facilities.length} />
          <StatCard label="Active Batches" value={batches.filter(b => b.status === 'active').length} />
          <StatCard label="Open Alerts" value={openAlerts.length} accent={openAlerts.length > 0 ? 'var(--warn)' : 'var(--safe)'} />
          <StatCard label="Flagged Meds" value={flaggedMeds.length} accent={flaggedMeds.length > 0 ? 'var(--danger)' : 'var(--safe)'} />
        </div>

        <div style={styles.grid}>
          {/* Facilities */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>Facilities</h2>
            <div style={styles.list}>
              {facilities.map(f => (
                <div key={f.id} style={styles.listItem}>
                  <div>
                    <div style={styles.listName}>{f.name}</div>
                    <div style={styles.listSub}>{f.fssai_license} · {f.state}</div>
                  </div>
                  <RiskBadge score={f.risk_score} />
                </div>
              ))}
            </div>
          </div>

          {/* Batches */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>Animal Batches</h2>
            <div style={styles.list}>
              {batches.map(b => (
                <div key={b.id} style={styles.listItem}>
                  <div>
                    <div style={styles.listName}>{b.batch_code}</div>
                    <div style={styles.listSub}>{b.facility_name} · {b.species} · {b.count} animals</div>
                  </div>
                  <span style={{ ...styles.badge, background: b.status === 'active' ? 'rgba(77,255,145,0.1)' : 'rgba(136,136,136,0.1)', color: b.status === 'active' ? 'var(--safe)' : 'var(--muted)' }}>
                    {b.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Alerts */}
          <div style={{ ...styles.card, gridColumn: '1 / -1' }}>
            <h2 style={styles.cardTitle}>Open Alerts</h2>
            {openAlerts.length === 0
              ? <p style={styles.empty}>No open alerts — all clear ✓</p>
              : (
                <div style={styles.list}>
                  {openAlerts.slice(0, 8).map(a => (
                    <div key={a.id} style={styles.alertItem}>
                      <div style={{ ...styles.alertDot, background: a.severity === 'critical' ? 'var(--danger)' : a.severity === 'high' ? 'var(--warn)' : 'var(--blue)' }} />
                      <div style={{ flex: 1 }}>
                        <div style={styles.alertMsg}>{a.message}</div>
                        <div style={styles.listSub}>{a.facility_name} · {a.alert_type.replace(/_/g, ' ')} · {new Date(a.created_at).toLocaleDateString()}</div>
                      </div>
                      <span style={{ ...styles.badge, color: severityColor(a.severity), background: severityBg(a.severity) }}>
                        {a.severity}
                      </span>
                    </div>
                  ))}
                </div>
              )
            }
          </div>

          {/* Recent Medications */}
          <div style={{ ...styles.card, gridColumn: '1 / -1' }}>
            <h2 style={styles.cardTitle}>Recent Medication Logs</h2>
            <table style={styles.table}>
              <thead>
                <tr>
                  {['Batch', 'Facility', 'Medication', 'Type', 'Dosage', 'Risk Score', 'Flag'].map(h => (
                    <th key={h} style={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {medications.slice(0, 10).map(m => (
                  <tr key={m.id} style={styles.tr}>
                    <td style={styles.td}><span style={styles.mono}>{m.batch_code}</span></td>
                    <td style={styles.td}>{m.facility_name}</td>
                    <td style={styles.td}>{m.medication_name}</td>
                    <td style={styles.td}><span style={styles.typeTag}>{m.medication_type}</span></td>
                    <td style={styles.td}>{m.dosage_mg}mg</td>
                    <td style={styles.td}>
                      <span style={{ color: m.risk_score >= 0.5 ? 'var(--danger)' : 'var(--safe)', fontFamily: 'var(--font-mono)' }}>
                        {m.risk_score.toFixed(3)}
                      </span>
                    </td>
                    <td style={styles.td}>
                      {m.risk_flag
                        ? <span style={{ color: 'var(--danger)' }}>⚠ Flagged</span>
                        : <span style={{ color: 'var(--safe)' }}>✓ Clear</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  )
}

function severityColor(s) {
  return s === 'critical' ? 'var(--danger)' : s === 'high' ? 'var(--warn)' : 'var(--blue)'
}
function severityBg(s) {
  return s === 'critical' ? 'rgba(255,77,77,0.1)' : s === 'high' ? 'rgba(255,184,77,0.1)' : 'rgba(77,159,255,0.1)'
}

const styles = {
  page: { display: 'flex', flexDirection: 'column', gap: 24, animation: 'fadeUp 0.4s ease' },
  loading: { color: 'var(--muted)', padding: 40 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' },
  title: { fontFamily: 'var(--font-head)', fontSize: 28, fontWeight: 700 },
  sub: { color: 'var(--muted)', marginTop: 4, fontSize: 13 },
  actions: { display: 'flex', gap: 10 },
  btnPrimary: { padding: '10px 20px', background: 'var(--accent)', border: 'none', borderRadius: 8, color: '#0a0a0a', fontWeight: 600, fontSize: 13, fontFamily: 'var(--font-head)' },
  btnSecondary: { padding: '10px 20px', background: 'none', border: '1px solid var(--border2)', borderRadius: 8, color: 'var(--text)', fontSize: 13 },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 },
  statCard: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 4 },
  statNum: { fontFamily: 'var(--font-head)', fontSize: 36, fontWeight: 800, color: 'var(--accent)' },
  statLabel: { fontSize: 13, color: 'var(--muted)' },
  statSub: { fontSize: 11, color: 'var(--muted2)' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  card: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 },
  cardTitle: { fontFamily: 'var(--font-head)', fontSize: 16, fontWeight: 600 },
  list: { display: 'flex', flexDirection: 'column', gap: 1 },
  listItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border)' },
  listName: { fontWeight: 500, fontSize: 14 },
  listSub: { color: 'var(--muted)', fontSize: 12, marginTop: 2, fontFamily: 'var(--font-mono)' },
  alertItem: { display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 0', borderBottom: '1px solid var(--border)' },
  alertDot: { width: 8, height: 8, borderRadius: '50%', marginTop: 6, flexShrink: 0 },
  alertMsg: { fontSize: 13, lineHeight: 1.5 },
  badge: { padding: '3px 10px', borderRadius: 999, fontSize: 11, fontFamily: 'var(--font-mono)' },
  empty: { color: 'var(--muted)', fontSize: 13 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', padding: '8px 12px', fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', borderBottom: '1px solid var(--border)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  td: { padding: '10px 12px', fontSize: 13, borderBottom: '1px solid var(--border)' },
  tr: {},
  mono: { fontFamily: 'var(--font-mono)', fontSize: 12 },
  typeTag: { padding: '2px 8px', background: 'var(--bg3)', borderRadius: 4, fontSize: 11, fontFamily: 'var(--font-mono)' },
}
