import { useEffect, useState } from 'react'
import { AlertTriangle, Check, Copy, Download, Save, X } from 'lucide-react'
import { api } from '../services/api'
import { fmtShort } from '../utils'

export default function ClaimPanel({ draft, onClose, onSaved }) {
  const [subject, setSubject] = useState(draft.claim.subject)
  const [body, setBody] = useState(draft.claim.body)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const p = draft.purchase

  useEffect(() => {
    setSubject(draft.claim.subject); setBody(draft.claim.body); setNote('')
  }, [draft])

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const copy = async () => {
    try { await navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`); setNote('Email copied.') }
    catch { setNote('Copy failed. Select the text and copy it manually.') }
  }
  const download = () => {
    const url = URL.createObjectURL(new Blob([`Subject: ${subject}\n\n${body}\n`], { type: 'text/plain' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: `warranty-claim-${p.product_name.toLowerCase().replace(/\W+/g, '-')}.txt` })
    a.click(); URL.revokeObjectURL(url); setNote('Draft downloaded.')
  }
  const save = async () => {
    setBusy(true)
    try { await api.saveClaim(draft.claim.id, subject, body); setNote('Draft saved.'); onSaved?.() }
    catch (e) { setNote(`Couldn’t save the draft: ${e.message}`) }
    finally { setBusy(false) }
  }

  const btn = 'inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-2 text-[14px] font-semibold text-charcoal hover:bg-canvas'

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-navy/50" onClick={onClose}>
      <aside
        role="dialog" aria-modal="true" aria-label="Warranty claim draft"
        className="scroll-thin flex h-full w-full max-w-xl flex-col overflow-y-auto bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between bg-navy px-4 py-3 text-white sm:px-5 sm:py-4">
          <div>
            <h2 className="text-[18px] font-semibold sm:text-[20px]">Claim draft</h2>
            <p className="text-[12px] text-white/70 sm:text-[13px]">Review before sending. Nothing has been sent.</p>
          </div>
          <button onClick={onClose} aria-label="Close draft" className="rounded-lg p-2 hover:bg-white/10"><X size={20} /></button>
        </header>

        <div className="space-y-3.5 p-4 sm:space-y-4 sm:p-5">
          {draft.warnings?.map((w) => (
            <p key={w} className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-[13px] text-warn sm:text-[14px]">
              <AlertTriangle size={18} className="shrink-0" aria-hidden="true" />{w}
            </p>
          ))}

          <section className="rounded-xl border border-line bg-canvas p-3.5 text-[13px] sm:p-4 sm:text-[14px]">
            <h3 className="mb-1 text-[16px] font-semibold sm:text-[17px]">{p.product_name}</h3>
            <p className="text-slate">Purchased {fmtShort(p.purchase_date)} · Warranty expires {fmtShort(p.warranty_expiry_date)}</p>
            <p className="mt-2"><span className="text-slate">Issue: </span>{draft.claim.issue_description}</p>
          </section>

          <label className="block">
            <span className="mb-1 block text-[13px] font-semibold sm:text-[14px]">Email subject</span>
            <input value={subject} onChange={(e) => setSubject(e.target.value)} maxLength={300}
              className="w-full rounded-lg border border-line px-3 py-2 text-[14px] sm:text-[15px]" />
          </label>
          <label className="block">
            <span className="mb-1 block text-[13px] font-semibold sm:text-[14px]">Email body</span>
            <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={10} maxLength={5000}
              className="w-full rounded-lg border border-line px-3 py-2 font-[inherit] text-[14px] leading-relaxed sm:rows-14 sm:text-[15px]" />
          </label>

          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            <button onClick={save} disabled={busy} className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-brand px-4 py-2.5 text-[14px] font-semibold text-navy hover:brightness-95 disabled:opacity-60 sm:py-2 sm:text-[15px]">
              <Save size={16} />Save draft
            </button>
            <button onClick={copy} className={`${btn} justify-center py-2.5 sm:py-2`}><Copy size={16} />Copy email</button>
            <button onClick={download} className={`${btn} justify-center py-2.5 sm:py-2`}><Download size={16} />Download</button>
          </div>
          <p role="status" className="flex min-h-5 items-center gap-1 text-[14px] text-ok">{note && <><Check size={14} />{note}</>}</p>
        </div>
      </aside>
    </div>
  )
}
