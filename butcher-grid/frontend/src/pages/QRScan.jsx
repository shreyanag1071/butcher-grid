import { useState } from 'react'
import { api } from '../services/api'

export default function QRScan() {
  const [code, setCode] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleScan(e) {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await api.scanQR(code.trim())
      setResult(res)
    } catch {
      setError('Product not found. Check the QR code and try again.')
    } finally { setLoading(false) }
  }

  function tryCode(c) { setCode(c); setResult(null); setError('') }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        {/* Header */}
        <div style={styles.brand}>
          <div style={styles.logo}>BG</div>
          <div>
            <h1 style={styles.title}>Butcher Grid</h1>
            <p style={styles.tagline}>Know what you're eating</p>
          </div>
        </div>

        {!result ? (
          <div style={styles.scanBox}>
            <div style={styles.scanIcon}>📦</div>
            <h2 style={styles.scanTitle}>Scan Product QR Code</h2>
            <p style={styles.scanSub}>Enter the code printed on your meat product packaging to see its full safety report</p>

            <form onSubmit={handleScan} style={styles.form}>
              <input
                style={styles.input}
                value={code}
                onChange={e => setCode(e.target.value)}
                placeholder="e.g. BG-KPF-CHK"
                autoComplete="off"
              />
              <button style={styles.scanBtn} type="submit" disabled={loading || !code}>
                {loading ? 'Checking...' : 'Check Safety →'}
              </button>
            </form>

            {error && <p style={styles.error}>{error}</p>}

            <div style={styles.demos}>
              <p style={styles.demoLabel}>Try a demo code</p>
              <div style={styles.demoRow}>
                {[
                  { label: '✅ Safe batch', code: 'BG-KPF-CHK' },
                  { label: '⚠ Flagged batch', code: 'BG-KLF-CHK' },
                  { label: '🚨 Non-compliant', code: 'BG-MSH-GOT' },
                ].map(d => (
                  <button key={d.code} style={styles.demoBtn} onClick={() => tryCode(d.code)}>
                    <span>{d.label}</span>
                    <span style={styles.demoCode}>{d.code}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ animation: 'fadeUp 0.4s ease' }}>
            {/* Safety verdict */}
            <div style={{ ...styles.verdict, borderColor: result.overall_safe ? 'rgba(77,255,145,0.3)' : 'rgba(255,77,77,0.3)', background: result.overall_safe ? 'rgba(77,255,145,0.05)' : 'rgba(255,77,77,0.05)' }}>
              <div style={{ fontSize: 56 }}>{result.overall_safe ? '✅' : '⚠️'}</div>
              <div>
                <div style={{ ...styles.verdictLabel, color: result.overall_safe ? 'var(--safe)' : 'var(--danger)' }}>
                  {result.safety_label}
                </div>
                <div style={styles.verdictSub}>
                  {result.batch_code} · {result.species} · arrived {result.arrival_date}
                </div>
              </div>
            </div>

            {/* Facility */}
            <div style={styles.section}>
              <div style={styles.sectionTitle}>Facility</div>
              <div style={styles.infoGrid}>
                <InfoRow label="Name" value={result.facility.name} />
                <InfoRow label="State" value={result.facility.state} />
                <InfoRow label="FSSAI License" value={result.facility.fssai_license} mono />
                <InfoRow label="Compliance" value={result.facility.compliance_status.replace('_', ' ')}
                  valueColor={result.facility.compliance_status === 'compliant' ? 'var(--safe)' : result.facility.compliance_status === 'warning' ? 'var(--warn)' : 'var(--danger)'} />
                <InfoRow label="Risk Score" value={result.facility.risk_score.toFixed(2)}
                  valueColor={result.facility.risk_score >= 0.5 ? 'var(--danger)' : 'var(--safe)'} />
              </div>
            </div>

            {/* Medications */}
            <div style={styles.section}>
              <div style={styles.sectionTitle}>Medication History</div>
              <div style={styles.infoGrid}>
                <InfoRow label="Antibiotic administrations" value={result.medications.antibiotic_administrations} />
                <InfoRow label="Hormone administrations" value={result.medications.hormone_administrations} />
                <InfoRow label="Any risk flagged"
                  value={result.medications.any_risk_flagged ? 'Yes — risk detected' : 'No — all clear'}
                  valueColor={result.medications.any_risk_flagged ? 'var(--danger)' : 'var(--safe)'} />
              </div>
            </div>

            <button style={styles.backBtn} onClick={() => { setResult(null); setCode('') }}>
              ← Check another product
            </button>
          </div>
        )}

        <p style={styles.footer}>Powered by Butcher Grid · One Health Monitoring Platform</p>
      </div>
    </div>
  )
}

function InfoRow({ label, value, mono, valueColor }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ fontSize: 13, color: 'var(--muted)' }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 500, fontFamily: mono ? 'var(--font-mono)' : 'inherit', color: valueColor || 'var(--text)' }}>{value}</span>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 },
  container: { width: '100%', maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 28 },
  brand: { display: 'flex', alignItems: 'center', gap: 14 },
  logo: { width: 44, height: 44, background: 'var(--accent)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-head)', fontWeight: 800, fontSize: 16, color: '#0a0a0a', flexShrink: 0 },
  title: { fontFamily: 'var(--font-head)', fontSize: 22, fontWeight: 700 },
  tagline: { color: 'var(--muted)', fontSize: 13, marginTop: 2 },
  scanBox: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 32, display: 'flex', flexDirection: 'column', gap: 20, alignItems: 'center', textAlign: 'center' },
  scanIcon: { fontSize: 48 },
  scanTitle: { fontFamily: 'var(--font-head)', fontSize: 22, fontWeight: 700 },
  scanSub: { color: 'var(--muted)', fontSize: 14, lineHeight: 1.6, maxWidth: 320 },
  form: { display: 'flex', flexDirection: 'column', gap: 10, width: '100%' },
  input: { padding: '14px 16px', background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 10, color: 'var(--text)', fontSize: 16, outline: 'none', textAlign: 'center', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' },
  scanBtn: { padding: '14px', background: 'var(--accent)', border: 'none', borderRadius: 10, color: '#0a0a0a', fontWeight: 700, fontSize: 15, fontFamily: 'var(--font-head)' },
  error: { color: 'var(--danger)', fontSize: 13 },
  demos: { width: '100%', display: 'flex', flexDirection: 'column', gap: 10 },
  demoLabel: { fontSize: 11, color: 'var(--muted2)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  demoRow: { display: 'flex', flexDirection: 'column', gap: 8 },
  demoBtn: { padding: '12px 16px', background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 8, color: 'var(--text)', fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  demoCode: { fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent)' },
  verdict: { padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid', display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20 },
  verdictLabel: { fontFamily: 'var(--font-head)', fontSize: 20, fontWeight: 700 },
  verdictSub: { color: 'var(--muted)', fontSize: 13, marginTop: 4, fontFamily: 'var(--font-mono)' },
  section: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 20, marginBottom: 12 },
  sectionTitle: { fontFamily: 'var(--font-head)', fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--muted)' },
  infoGrid: { display: 'flex', flexDirection: 'column' },
  backBtn: { width: '100%', padding: '12px', background: 'none', border: '1px solid var(--border2)', borderRadius: 10, color: 'var(--text)', fontSize: 13, marginTop: 8 },
  footer: { textAlign: 'center', color: 'var(--muted2)', fontSize: 11, fontFamily: 'var(--font-mono)' },
}
