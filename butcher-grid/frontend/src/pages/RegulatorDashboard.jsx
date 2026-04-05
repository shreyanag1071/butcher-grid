import { useState, useEffect } from 'react'
import { api } from '../services/api'
import Layout from '../components/Layout'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function RegulatorDashboard() {
  const [data, setData] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [resolving, setResolving] = useState(null)

  async function load() {
    const [d, a] = await Promise.all([api.getDashboard(), api.getAlerts()])
    setData(d)
    setAlerts(a.filter(x => !x.is_resolved))
  }

  useEffect(() => { load().finally(() => setLoading(false)) }, [])

  async function resolve(id) {
    setResolving(id)
    await api.resolveAlert(id)
    await load()
    setResolving(null)
  }

  if (loading) return <Layout><div style={{ color: 'var(--muted)', padding: 40 }}>Loading national data...</div></Layout>

  const complianceData = [
    { name: 'Compliant', value: data.compliance_breakdown.compliant, color: 'var(--safe)' },
    { name: 'Warning', value: data.compliance_breakdown.warning, color: 'var(--warn)' },
    { name: 'Non-Compliant', value: data.compliance_breakdown.non_compliant, color: 'var(--danger)' },
  ]

  return (
    <Layout>
      <div style={styles.page}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>National Dashboard</h1>
            <p style={styles.sub}>Real-time One Health monitoring across all registered facilities</p>
          </div>
          <div style={styles.liveBadge}>
            <span style={styles.liveDot} />
            Live
          </div>
        </div>

        {/* Top stats */}
        <div style={styles.statsRow}>
          {[
            { label: 'Total Facilities', value: data.total_facilities, color: 'var(--accent)' },
            { label: 'Avg Risk Score', value: data.average_risk_score.toFixed(3), color: data.average_risk_score >= 0.5 ? 'var(--danger)' : 'var(--safe)' },
            { label: 'Open Alerts', value: data.open_alerts, color: data.open_alerts > 0 ? 'var(--warn)' : 'var(--safe)' },
            { label: 'Critical Alerts', value: data.critical_alerts, color: data.critical_alerts > 0 ? 'var(--danger)' : 'var(--safe)' },
            { label: 'Flagged Meds', value: data.flagged_medication_logs, color: data.flagged_medication_logs > 0 ? 'var(--warn)' : 'var(--safe)' },
            { label: 'Waste Anomalies', value: data.waste_anomalies, color: data.waste_anomalies > 0 ? 'var(--warn)' : 'var(--safe)' },
          ].map(s => (
            <div key={s.label} style={styles.statCard}>
              <span style={{ ...styles.statNum, color: s.color }}>{s.value}</span>
              <span style={styles.statLabel}>{s.label}</span>
            </div>
          ))}
        </div>

        <div style={styles.grid}>
          {/* Compliance chart */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>Compliance Breakdown</h2>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={complianceData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fill: '#888', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#888', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, color: '#f0ece4' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {complianceData.map((entry, i) => <Cell key={i} fill={entry.color} fillOpacity={0.8} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div style={styles.legendRow}>
              {complianceData.map(d => (
                <div key={d.name} style={styles.legendItem}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: d.color }} />
                  <span style={{ color: 'var(--muted)', fontSize: 11 }}>{d.name}: <strong style={{ color: d.color }}>{d.value}</strong></span>
                </div>
              ))}
            </div>
          </div>

          {/* High risk facilities */}
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>High Risk Facilities</h2>
            <div style={styles.list}>
              {data.high_risk_facilities.length === 0
                ? <p style={{ color: 'var(--muted)', fontSize: 13 }}>No high-risk facilities</p>
                : data.high_risk_facilities.map(f => (
                  <div key={f.id} style={styles.listItem}>
                    <div>
                      <div style={styles.listName}>{f.name}</div>
                      <div style={styles.listSub}>{f.state} · {f.fssai_license}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', color: f.risk_score >= 0.75 ? 'var(--danger)' : 'var(--warn)', fontWeight: 600 }}>
                        {f.risk_score.toFixed(3)}
                      </div>
                      <div style={{ ...styles.badge, color: complianceColor(f.compliance_status), background: complianceBg(f.compliance_status), marginTop: 4, display: 'inline-block' }}>
                        {f.compliance_status.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>

          {/* Alerts panel */}
          <div style={{ ...styles.card, gridColumn: '1 / -1' }}>
            <h2 style={styles.cardTitle}>Open Alerts — Requires Action</h2>
            {alerts.length === 0
              ? <p style={{ color: 'var(--safe)', fontSize: 13 }}>✓ No open alerts across all facilities</p>
              : (
                <div style={styles.alertTable}>
                  <div style={styles.alertHead}>
                    {['Severity', 'Type', 'Facility', 'Message', 'Created', 'Action'].map(h => (
                      <span key={h} style={styles.th}>{h}</span>
                    ))}
                  </div>
                  {alerts.map(a => (
                    <div key={a.id} style={styles.alertRow}>
                      <span style={{ ...styles.badge, color: sevColor(a.severity), background: sevBg(a.severity) }}>{a.severity}</span>
                      <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--muted)' }}>{a.alert_type.replace(/_/g, ' ')}</span>
                      <span style={{ fontSize: 13 }}>{a.facility_name}</span>
                      <span style={{ fontSize: 12, color: 'var(--muted)', flex: 2 }}>{a.message.slice(0, 80)}...</span>
                      <span style={{ fontSize: 11, color: 'var(--muted2)', fontFamily: 'var(--font-mono)' }}>{new Date(a.created_at).toLocaleDateString()}</span>
                      <button
                        style={styles.resolveBtn}
                        onClick={() => resolve(a.id)}
                        disabled={resolving === a.id}
                      >
                        {resolving === a.id ? '...' : 'Resolve'}
                      </button>
                    </div>
                  ))}
                </div>
              )
            }
          </div>
        </div>
      </div>
    </Layout>
  )
}

function complianceColor(s) { return s === 'non_compliant' ? 'var(--danger)' : s === 'warning' ? 'var(--warn)' : 'var(--safe)' }
function complianceBg(s) { return s === 'non_compliant' ? 'rgba(255,77,77,0.1)' : s === 'warning' ? 'rgba(255,184,77,0.1)' : 'rgba(77,255,145,0.1)' }
function sevColor(s) { return s === 'critical' ? 'var(--danger)' : s === 'high' ? 'var(--warn)' : 'var(--blue)' }
function sevBg(s) { return s === 'critical' ? 'rgba(255,77,77,0.1)' : s === 'high' ? 'rgba(255,184,77,0.1)' : 'rgba(77,159,255,0.1)' }

const styles = {
  page: { display: 'flex', flexDirection: 'column', gap: 24, animation: 'fadeUp 0.4s ease' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontFamily: 'var(--font-head)', fontSize: 28, fontWeight: 700 },
  sub: { color: 'var(--muted)', fontSize: 13, marginTop: 4 },
  liveBadge: { display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', border: '1px solid var(--border2)', borderRadius: 999, fontSize: 12, fontFamily: 'var(--font-mono)' },
  liveDot: { width: 6, height: 6, borderRadius: '50%', background: 'var(--safe)', animation: 'pulse 2s infinite' },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 },
  statCard: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 4 },
  statNum: { fontFamily: 'var(--font-head)', fontSize: 32, fontWeight: 800 },
  statLabel: { fontSize: 11, color: 'var(--muted)' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  card: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 },
  cardTitle: { fontFamily: 'var(--font-head)', fontSize: 16, fontWeight: 600 },
  legendRow: { display: 'flex', gap: 20 },
  legendItem: { display: 'flex', alignItems: 'center', gap: 6 },
  list: { display: 'flex', flexDirection: 'column' },
  listItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border)' },
  listName: { fontWeight: 500, fontSize: 14 },
  listSub: { color: 'var(--muted)', fontSize: 12, marginTop: 2, fontFamily: 'var(--font-mono)' },
  badge: { padding: '3px 10px', borderRadius: 999, fontSize: 11, fontFamily: 'var(--font-mono)' },
  alertTable: { display: 'flex', flexDirection: 'column', gap: 0 },
  alertHead: { display: 'grid', gridTemplateColumns: '80px 120px 1fr 2fr 90px 80px', gap: 12, padding: '8px 12px', borderBottom: '1px solid var(--border)' },
  alertRow: { display: 'grid', gridTemplateColumns: '80px 120px 1fr 2fr 90px 80px', gap: 12, padding: '10px 12px', borderBottom: '1px solid var(--border)', alignItems: 'center' },
  th: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase' },
  resolveBtn: { padding: '5px 12px', background: 'none', border: '1px solid var(--border2)', borderRadius: 6, color: 'var(--text)', fontSize: 11 },
}
