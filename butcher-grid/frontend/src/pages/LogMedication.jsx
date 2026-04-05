import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import Layout from '../components/Layout'

export default function LogMedication() {
  const navigate = useNavigate()
  const [batches, setBatches] = useState([])
  const [form, setForm] = useState({
    batch: '', medication_name: '', medication_type: 'antibiotic',
    dosage_mg: '', withdrawal_period_days: '', notes: '',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { api.getBatches().then(setBatches) }, [])

  function set(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await api.logMedication({
        ...form,
        dosage_mg: parseFloat(form.dosage_mg),
        withdrawal_period_days: parseInt(form.withdrawal_period_days || 0),
      })
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const riskColor = result?.risk_score >= 0.5 ? 'var(--danger)' : 'var(--safe)'

  return (
    <Layout>
      <div style={styles.page}>
        <div style={styles.header}>
          <button style={styles.back} onClick={() => navigate('/farm')}>← Back</button>
          <h1 style={styles.title}>Log Medication</h1>
          <p style={styles.sub}>AI risk scoring runs instantly on submission</p>
        </div>

        <div style={styles.cols}>
          <form style={styles.form} onSubmit={handleSubmit}>
            <div style={styles.field}>
              <label style={styles.label}>Animal Batch</label>
              <select style={styles.input} value={form.batch} onChange={e => set('batch', e.target.value)} required>
                <option value="">Select batch...</option>
                {batches.map(b => (
                  <option key={b.id} value={b.id}>{b.batch_code} — {b.facility_name} ({b.species})</option>
                ))}
              </select>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Medication Name</label>
              <input style={styles.input} value={form.medication_name} onChange={e => set('medication_name', e.target.value)} placeholder="e.g. Colistin, Estradiol, Newcastle Vaccine" required />
            </div>

            <div style={styles.row}>
              <div style={styles.field}>
                <label style={styles.label}>Type</label>
                <select style={styles.input} value={form.medication_type} onChange={e => set('medication_type', e.target.value)}>
                  <option value="antibiotic">Antibiotic</option>
                  <option value="hormone">Hormone</option>
                  <option value="vaccine">Vaccine</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Dosage (mg)</label>
                <input style={styles.input} type="number" value={form.dosage_mg} onChange={e => set('dosage_mg', e.target.value)} placeholder="e.g. 250" required />
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Withdrawal Days</label>
                <input style={styles.input} type="number" value={form.withdrawal_period_days} onChange={e => set('withdrawal_period_days', e.target.value)} placeholder="e.g. 7" />
              </div>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Notes (optional)</label>
              <textarea style={{ ...styles.input, minHeight: 80, resize: 'vertical' }} value={form.notes} onChange={e => set('notes', e.target.value)} placeholder="Reason for administration..." />
            </div>

            {error && <p style={styles.error}>{error}</p>}

            <button style={styles.submit} type="submit" disabled={loading}>
              {loading ? 'Scoring...' : 'Submit & Score with AI →'}
            </button>

            <div style={styles.hint}>
              <span style={{ color: 'var(--accent)' }}>💡 Try flagged drugs:</span> Colistin, Estradiol, Trenbolone, Ciprofloxacin
            </div>
          </form>

          {/* AI Result panel */}
          <div style={styles.resultPanel}>
            <div style={styles.resultHeader}>AI Risk Assessment</div>
            {!result && (
              <div style={styles.placeholder}>
                <div style={styles.placeholderIcon}>⚡</div>
                <p>Submit a medication log to see instant AI risk scoring</p>
              </div>
            )}
            {result && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20, animation: 'fadeUp 0.4s ease' }}>
                {/* Score meter */}
                <div style={styles.scoreMeter}>
                  <div style={styles.scoreLabel}>Risk Score</div>
                  <div style={{ ...styles.scoreNum, color: riskColor }}>
                    {result.risk_score.toFixed(3)}
                  </div>
                  <div style={styles.meterBar}>
                    <div style={{ ...styles.meterFill, width: `${result.risk_score * 100}%`, background: riskColor }} />
                  </div>
                  <div style={{ ...styles.verdict, color: riskColor }}>
                    {result.risk_flag ? '⚠ FLAGGED — Alert created' : '✓ CLEAR — No alert raised'}
                  </div>
                </div>

                {/* Reasons */}
                {result.ml_result?.reasons?.length > 0 && (
                  <div style={styles.reasons}>
                    <div style={styles.reasonsTitle}>Why this score</div>
                    {result.ml_result.reasons.map((r, i) => (
                      <div key={i} style={styles.reasonItem}>
                        <span style={{ color: 'var(--accent)' }}>→</span> {r}
                      </div>
                    ))}
                  </div>
                )}

                {/* Details */}
                <div style={styles.details}>
                  {[
                    ['Medication', result.medication_name],
                    ['Type', result.medication_type],
                    ['Dosage', `${result.dosage_mg}mg`],
                    ['Withdrawal', `${result.withdrawal_period_days} days`],
                    ['Batch', result.batch_code],
                    ['Severity', result.ml_result?.severity || '—'],
                  ].map(([k, v]) => (
                    <div key={k} style={styles.detailRow}>
                      <span style={styles.detailKey}>{k}</span>
                      <span style={styles.detailVal}>{v}</span>
                    </div>
                  ))}
                </div>

                <button style={styles.logAnother} onClick={() => { setResult(null); setForm(f => ({ ...f, medication_name: '', dosage_mg: '', notes: '' })) }}>
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
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 },
  label: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  input: { padding: '11px 14px', background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: 14, outline: 'none' },
  error: { color: 'var(--danger)', fontSize: 13 },
  submit: { padding: '14px', background: 'var(--accent)', border: 'none', borderRadius: 8, color: '#0a0a0a', fontWeight: 700, fontSize: 14, fontFamily: 'var(--font-head)' },
  hint: { fontSize: 12, color: 'var(--muted)', padding: '10px 14px', background: 'rgba(200,240,77,0.05)', borderRadius: 8, border: '1px solid rgba(200,240,77,0.15)' },
  resultPanel: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 28, display: 'flex', flexDirection: 'column', gap: 20, minHeight: 400 },
  resultHeader: { fontFamily: 'var(--font-head)', fontSize: 16, fontWeight: 600, paddingBottom: 16, borderBottom: '1px solid var(--border)' },
  placeholder: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, color: 'var(--muted)', textAlign: 'center', padding: 40 },
  placeholderIcon: { fontSize: 40, opacity: 0.4 },
  scoreMeter: { display: 'flex', flexDirection: 'column', gap: 8 },
  scoreLabel: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase' },
  scoreNum: { fontFamily: 'var(--font-head)', fontSize: 56, fontWeight: 800, lineHeight: 1 },
  meterBar: { height: 6, background: 'var(--bg3)', borderRadius: 3, overflow: 'hidden' },
  meterFill: { height: '100%', borderRadius: 3, transition: 'width 0.8s ease' },
  verdict: { fontSize: 13, fontFamily: 'var(--font-mono)', fontWeight: 500 },
  reasons: { display: 'flex', flexDirection: 'column', gap: 8 },
  reasonsTitle: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', marginBottom: 4 },
  reasonItem: { fontSize: 13, color: 'var(--text)', lineHeight: 1.5, display: 'flex', gap: 8 },
  details: { display: 'flex', flexDirection: 'column', gap: 0, border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' },
  detailRow: { display: 'flex', justifyContent: 'space-between', padding: '8px 14px', borderBottom: '1px solid var(--border)' },
  detailKey: { color: 'var(--muted)', fontSize: 12, fontFamily: 'var(--font-mono)' },
  detailVal: { fontSize: 13, fontWeight: 500 },
  logAnother: { padding: '10px', background: 'none', border: '1px solid var(--border2)', borderRadius: 8, color: 'var(--text)', fontSize: 13 },
}
