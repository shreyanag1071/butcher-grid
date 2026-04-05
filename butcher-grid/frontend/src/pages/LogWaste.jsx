import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import Layout from '../components/Layout'

export default function LogWaste() {
  const navigate = useNavigate()
  const [facilities, setFacilities] = useState([])
  const [form, setForm] = useState({ facility: '', waste_type: 'solid', quantity_kg: '', disposal_method: 'composting' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { api.getFacilities().then(setFacilities) }, [])
  function set(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await api.logWaste({ ...form, quantity_kg: parseFloat(form.quantity_kg) })
      setResult(res)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  const anomalyColor = result?.is_anomaly ? 'var(--danger)' : 'var(--safe)'

  return (
    <Layout>
      <div style={styles.page}>
        <div style={styles.header}>
          <button style={styles.back} onClick={() => navigate('/farm')}>← Back</button>
          <h1 style={styles.title}>Log Waste Disposal</h1>
          <p style={styles.sub}>AI anomaly detection runs instantly on submission</p>
        </div>

        <div style={styles.cols}>
          <form style={styles.form} onSubmit={handleSubmit}>
            <div style={styles.field}>
              <label style={styles.label}>Facility</label>
              <select style={styles.input} value={form.facility} onChange={e => set('facility', e.target.value)} required>
                <option value="">Select facility...</option>
                {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
            </div>

            <div style={styles.row}>
              <div style={styles.field}>
                <label style={styles.label}>Waste Type</label>
                <select style={styles.input} value={form.waste_type} onChange={e => set('waste_type', e.target.value)}>
                  <option value="solid">Solid Organic</option>
                  <option value="liquid">Liquid Effluent</option>
                  <option value="blood">Blood</option>
                  <option value="chemical">Chemical</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Quantity (kg)</label>
                <input style={styles.input} type="number" value={form.quantity_kg} onChange={e => set('quantity_kg', e.target.value)} placeholder="e.g. 500" required />
              </div>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Disposal Method</label>
              <select style={styles.input} value={form.disposal_method} onChange={e => set('disposal_method', e.target.value)}>
                <option value="composting">Composting</option>
                <option value="biogas">Biogas Plant</option>
                <option value="third_party">Third-Party Handler</option>
                <option value="sewer">Municipal Sewer</option>
                <option value="untreated">Untreated Discharge</option>
              </select>
            </div>

            {error && <p style={styles.error}>{error}</p>}

            <button style={styles.submit} type="submit" disabled={loading}>
              {loading ? 'Analysing...' : 'Submit & Detect Anomalies →'}
            </button>

            <div style={styles.hint}>
              <span style={{ color: 'var(--accent)' }}>💡 Try anomalous combo:</span> Chemical waste + Untreated Discharge + large quantity
            </div>
          </form>

          <div style={styles.resultPanel}>
            <div style={styles.resultHeader}>AI Anomaly Detection</div>
            {!result ? (
              <div style={styles.placeholder}>
                <div style={{ fontSize: 40, opacity: 0.4 }}>🗑️</div>
                <p>Submit a waste log to see anomaly detection results</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20, animation: 'fadeUp 0.4s ease' }}>
                <div style={styles.scoreMeter}>
                  <div style={styles.scoreLabel}>Anomaly Score</div>
                  <div style={{ ...styles.scoreNum, color: anomalyColor }}>{result.anomaly_score.toFixed(3)}</div>
                  <div style={styles.meterBar}>
                    <div style={{ ...styles.meterFill, width: `${result.anomaly_score * 100}%`, background: anomalyColor }} />
                  </div>
                  <div style={{ fontSize: 13, fontFamily: 'var(--font-mono)', color: anomalyColor }}>
                    {result.is_anomaly ? '⚠ ANOMALY — Alert created' : '✓ NORMAL — No anomaly detected'}
                  </div>
                </div>

                {result.ml_result?.reasons?.length > 0 && (
                  <div style={styles.reasons}>
                    <div style={styles.reasonsTitle}>Why this score</div>
                    {result.ml_result.reasons.map((r, i) => (
                      <div key={i} style={{ fontSize: 13, display: 'flex', gap: 8 }}>
                        <span style={{ color: 'var(--accent)' }}>→</span> {r}
                      </div>
                    ))}
                  </div>
                )}

                <div style={styles.details}>
                  {[
                    ['Waste Type', result.waste_type],
                    ['Quantity', `${result.quantity_kg}kg`],
                    ['Disposal', result.disposal_method],
                    ['Severity', result.ml_result?.severity || '—'],
                  ].map(([k, v]) => (
                    <div key={k} style={styles.detailRow}>
                      <span style={styles.detailKey}>{k}</span>
                      <span style={{ fontSize: 13, fontWeight: 500 }}>{v}</span>
                    </div>
                  ))}
                </div>

                <button style={styles.logAnother} onClick={() => { setResult(null); setForm(f => ({ ...f, quantity_kg: '' })) }}>
                  Log another
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}

const styles = {
  page: { display: 'flex', flexDirection: 'column', gap: 24 },
  header: { display: 'flex', flexDirection: 'column', gap: 4 },
  back: { background: 'none', border: 'none', color: 'var(--muted)', fontSize: 13, padding: 0, marginBottom: 4, textAlign: 'left' },
  title: { fontFamily: 'var(--font-head)', fontSize: 28, fontWeight: 700 },
  sub: { color: 'var(--muted)', fontSize: 13 },
  cols: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start' },
  form: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 28, display: 'flex', flexDirection: 'column', gap: 18 },
  field: { display: 'flex', flexDirection: 'column', gap: 6 },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  label: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  input: { padding: '11px 14px', background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 8, color: 'var(--text)', fontSize: 14, outline: 'none' },
  error: { color: 'var(--danger)', fontSize: 13 },
  submit: { padding: '14px', background: 'var(--accent)', border: 'none', borderRadius: 8, color: '#0a0a0a', fontWeight: 700, fontSize: 14, fontFamily: 'var(--font-head)' },
  hint: { fontSize: 12, color: 'var(--muted)', padding: '10px 14px', background: 'rgba(200,240,77,0.05)', borderRadius: 8, border: '1px solid rgba(200,240,77,0.15)' },
  resultPanel: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 28, display: 'flex', flexDirection: 'column', gap: 20, minHeight: 400 },
  resultHeader: { fontFamily: 'var(--font-head)', fontSize: 16, fontWeight: 600, paddingBottom: 16, borderBottom: '1px solid var(--border)' },
  placeholder: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, color: 'var(--muted)', textAlign: 'center', padding: 40 },
  scoreMeter: { display: 'flex', flexDirection: 'column', gap: 8 },
  scoreLabel: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase' },
  scoreNum: { fontFamily: 'var(--font-head)', fontSize: 56, fontWeight: 800, lineHeight: 1 },
  meterBar: { height: 6, background: 'var(--bg3)', borderRadius: 3, overflow: 'hidden' },
  meterFill: { height: '100%', borderRadius: 3, transition: 'width 0.8s ease' },
  reasons: { display: 'flex', flexDirection: 'column', gap: 8 },
  reasonsTitle: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', marginBottom: 4 },
  details: { display: 'flex', flexDirection: 'column', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' },
  detailRow: { display: 'flex', justifyContent: 'space-between', padding: '8px 14px', borderBottom: '1px solid var(--border)' },
  detailKey: { color: 'var(--muted)', fontSize: 12, fontFamily: 'var(--font-mono)' },
  logAnother: { padding: '10px', background: 'none', border: '1px solid var(--border2)', borderRadius: 8, color: 'var(--text)', fontSize: 13 },
}
