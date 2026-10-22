export const fmtDate = (iso) => {
  if (!iso) return 'Not recorded'
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}
export const fmtShort = (iso) => {
  if (!iso) return 'Unknown'
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
export const fmtMoney = (amount, currency) => {
  if (amount == null) return 'Not recorded'
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(amount) }
  catch { return `${amount} ${currency}` }
}
export const fmtDuration = (months) => {
  if (!months) return 'Unknown'
  const y = Math.floor(months / 12), m = months % 12
  return [y && `${y} year${y > 1 ? 's' : ''}`, m && `${m} month${m > 1 ? 's' : ''}`].filter(Boolean).join(' ')
}
export const STATUS = {
  active: { label: 'Active', cls: 'bg-green-50 text-ok border-green-200', dot: 'bg-ok' },
  expiring_soon: { label: 'Expiring soon', cls: 'bg-amber-50 text-warn border-amber-200', dot: 'bg-warn' },
  expired: { label: 'Expired', cls: 'bg-red-50 text-bad border-red-200', dot: 'bg-bad' },
  unknown: { label: 'Unknown', cls: 'bg-slate-100 text-slate border-line', dot: 'bg-slate' },
}
export const remaining = (p) => {
  if (p.days_remaining == null) return 'No expiry date recorded'
  if (p.days_remaining < 0) return `Expired ${Math.abs(p.days_remaining)} day${Math.abs(p.days_remaining) === 1 ? '' : 's'} ago`
  if (p.days_remaining === 0) return 'Expires today'
  return `${p.days_remaining} day${p.days_remaining === 1 ? '' : 's'} left`
}
