import { useState } from 'react'
import { FileText, Loader2, Sparkles } from 'lucide-react'
import PurchaseCard from './PurchaseCard'
import { fmtShort } from '../utils'

const TILES = [
  ['total', 'Purchases', 'text-charcoal'],
  ['active', 'Active', 'text-ok'],
  ['expiring_soon', 'Expiring soon', 'text-warn'],
  ['expired', 'Expired', 'text-bad'],
]

export default function Dashboard({ data, error, onSeed, onDelete, onOpenClaim, onDraftClaim }) {
  const [seeding, setSeeding] = useState(false)
  if (error) {
    return <p role="alert" className="m-4 rounded-xl border border-red-200 bg-red-50 p-4 text-[14px] text-bad">Couldn’t load your vault: {error}</p>
  }
  if (!data) return <p className="m-4 flex items-center gap-2 text-slate"><Loader2 className="animate-spin" size={16} />Loading your vault…</p>

  const { counts, purchases, expiring, claims } = data
  return (
    <div className="space-y-5 p-3 sm:space-y-6 sm:p-5">
      <section aria-label="Warranty overview" className="grid grid-cols-2 gap-2.5 sm:gap-3">
        {TILES.map(([key, label, color]) => (
          <div key={key} className="rounded-xl border border-line bg-white p-3 sm:p-4">
            <p className={`text-[26px] sm:text-[32px] font-bold leading-none ${color}`}>{counts[key]}</p>
            <p className="mt-1 text-[13px] sm:text-[14px] text-slate">{label}</p>
          </div>
        ))}
      </section>

      {purchases.length === 0 && (
        <section className="rounded-xl border border-dashed border-line bg-white p-5 text-center sm:p-6">
          <p className="text-[16px] sm:text-[17px] font-semibold">Your vault is empty</p>
          <p className="mx-auto mt-1 max-w-xs text-[13px] sm:text-[14px] text-slate">Tell the assistant about something you bought, or load sample purchases to explore.</p>
          <button
            onClick={async () => { setSeeding(true); await onSeed(); setSeeding(false) }}
            disabled={seeding}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-[14px] sm:text-[15px] font-semibold text-navy hover:brightness-95 disabled:opacity-60"
          >
            {seeding ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}Load sample data
          </button>
        </section>
      )}

      {expiring.length > 0 && (
        <section aria-labelledby="exp-h">
          <h2 id="exp-h" className="mb-2 text-[18px] sm:text-[22px] font-semibold">Expiring soon</h2>
          <ul className="space-y-2.5 sm:space-y-3">{expiring.map((p) => <li key={p.id}><PurchaseCard p={p} onDelete={onDelete} onDraftClaim={onDraftClaim} compact /></li>)}</ul>
        </section>
      )}

      {purchases.length > 0 && (
        <section aria-labelledby="rec-h">
          <h2 id="rec-h" className="mb-2 text-[18px] sm:text-[22px] font-semibold">Recent purchases</h2>
          <ul className="space-y-2.5 sm:space-y-3">{purchases.slice(0, 8).map((p) => <li key={p.id}><PurchaseCard p={p} onDelete={onDelete} onDraftClaim={onDraftClaim} compact /></li>)}</ul>
        </section>
      )}

      {claims.length > 0 && (
        <section aria-labelledby="cl-h">
          <h2 id="cl-h" className="mb-2 text-[18px] sm:text-[22px] font-semibold">Claim drafts</h2>
          <ul className="space-y-2">
            {claims.map((c) => (
              <li key={c.id}>
                <button onClick={() => onOpenClaim(c)} className="flex w-full items-center gap-3 rounded-xl border border-line bg-white p-3 text-left hover:border-brand">
                  <FileText size={18} className="shrink-0 text-slate" aria-hidden="true" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[14px] sm:text-[15px] font-semibold">{c.draft_subject}</span>
                    <span className="block text-[12px] sm:text-[13px] text-slate">Saved {fmtShort(c.created_at.slice(0, 10))}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
