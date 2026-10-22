import { useState } from 'react'
import { ChevronDown, FileText, Trash2 } from 'lucide-react'
import StatusBadge from './StatusBadge'
import { fmtDate, fmtDuration, fmtMoney, fmtShort, remaining } from '../utils'

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-2 py-1 text-[13px] sm:gap-4 sm:text-[14px]">
      <dt className="text-slate">{k}</dt>
      <dd className="text-right font-medium text-charcoal truncate max-w-[60%]">{v}</dd>
    </div>
  )
}

/** compact = dashboard list row; otherwise full card shown inside chat. */
export default function PurchaseCard({ p, compact = false, onDelete, onDraftClaim, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <article className="rounded-xl border border-line bg-white p-3.5 sm:p-4">
      <div className="flex items-start justify-between gap-2.5">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-[15px] sm:text-[17px] font-semibold text-charcoal">{p.product_name}</h3>
          <p className="text-[12px] sm:text-[13px] text-slate mt-0.5">
            {p.warranty_expiry_date ? `Expires ${fmtShort(p.warranty_expiry_date)} · ${remaining(p)}` : remaining(p)}
          </p>
        </div>
        <div className="shrink-0">
          <StatusBadge status={p.status} />
        </div>
      </div>
      {open && (
        <dl className="mt-3 divide-y divide-line border-t border-line pt-2">
          {p.brand && <Row k="Brand" v={p.brand} />}
          <Row k="Purchase date" v={fmtDate(p.purchase_date)} />
          <Row k="Purchase price" v={fmtMoney(p.purchase_price, p.currency)} />
          <Row k="Warranty duration" v={fmtDuration(p.warranty_duration_months)} />
          <Row k="Expiry date" v={fmtDate(p.warranty_expiry_date)} />
          {p.receipt_path && <Row k="Receipt" v={p.receipt_path} />}
        </dl>
      )}
      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          className="inline-flex items-center gap-1 rounded-lg bg-brand px-3 py-1.5 text-[14px] font-semibold text-navy transition hover:brightness-95"
        >
          {open ? 'Hide details' : 'View details'}
          <ChevronDown size={16} className={open ? 'rotate-180' : ''} aria-hidden="true" />
        </button>
        {onDraftClaim && (
          <button
            type="button"
            onClick={() => onDraftClaim(p)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-2.5 py-1.5 text-[13px] sm:text-[14px] font-semibold text-charcoal hover:border-brand hover:text-brand transition"
          >
            <FileText size={15} className="text-brand" />
            <span>Draft claim</span>
          </button>
        )}
        {compact && onDelete && (
          <button
            onClick={() => onDelete(p)}
            aria-label={`Remove ${p.product_name}`}
            className="ml-auto rounded-lg p-2 text-slate hover:bg-red-50 hover:text-bad"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </article>
  )
}
