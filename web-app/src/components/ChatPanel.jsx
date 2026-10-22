import { useEffect, useRef, useState } from 'react'
import { Check, ChevronRight, FileText, SendHorizontal, Volume2, VolumeX, X } from 'lucide-react'
import Logo from './Logo'
import MicButton from './MicButton'
import PurchaseCard from './PurchaseCard'

const SUGGESTIONS = [
  'I bought a dishwasher for $600 with a two-year warranty',
  'Is my dishwasher still under warranty?',
  'Which warranties expire in the next 30 days?',
  'My dishwasher has stopped cleaning properly. Help me prepare a claim',
]

const PHASE_TEXT = {
  listening: 'Listening…',
  processing: 'Understanding your request…',
  tool: 'Checking your vault…',
  responding: 'Speaking…',
}

function ToolChip({ ev }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)} aria-expanded={open}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[13px] font-medium ${
          ev.ok ? 'border-cyan-200 bg-cyan-50 text-cyan-900' : ev.result?.needs ? 'border-line bg-canvas text-slate' : 'border-red-200 bg-red-50 text-bad'
        }`}
      >
        {ev.ok ? <Check size={13} /> : ev.result?.needs ? <ChevronRight size={13} /> : <X size={13} />}
        <code className="font-[inherit]">{ev.name}</code>
        <span className="text-[12px] opacity-75">{ev.ok ? 'completed' : ev.result?.needs ? 'needs more info' : 'failed'}</span>
      </button>
      {open && (
        <pre className="scroll-thin mt-1 max-h-48 overflow-auto rounded-lg bg-navy p-3 text-[12px] leading-snug text-cyan-100">
          {JSON.stringify({ arguments: ev.arguments, result: ev.result }, null, 2)}
        </pre>
      )}
    </div>
  )
}

function Results({ events, onOpenDraft, onDraftClaim }) {
  const out = []
  events.forEach((ev, i) => {
    const r = ev.result
    if (!ev.ok) return
    if (ev.name === 'log_purchase' && r.purchase) out.push(<PurchaseCard key={i} p={r.purchase} onDraftClaim={onDraftClaim} />)
    else if (ev.name === 'check_warranty') (r.multiple ? r.matches : [r.purchase]).forEach((p) => out.push(<PurchaseCard key={`${i}-${p.id}`} p={p} onDraftClaim={onDraftClaim} />))
    else if (ev.name === 'expiring_soon') r.items.forEach((p) => out.push(<PurchaseCard key={`${i}-${p.id}`} p={p} onDraftClaim={onDraftClaim} />))
    else if (ev.name === 'draft_claim' && r.claim)
      out.push(
        <button key={i} onClick={() => onOpenDraft(r)}
          className="flex w-full items-center gap-3 rounded-xl border border-line bg-white p-4 text-left hover:border-brand">
          <FileText className="shrink-0 text-brand" aria-hidden="true" />
          <span className="min-w-0 flex-1">
            <span className="block truncate text-[15px] font-semibold">{r.claim.subject}</span>
            <span className="text-[13px] text-slate">Review, edit or copy the draft</span>
          </span>
          <ChevronRight size={18} className="text-slate" aria-hidden="true" />
        </button>,
      )
  })
  return out.length ? <div className="mt-3 space-y-3">{out}</div> : null
}

export default function ChatPanel({ messages, phase, input, setInput, onSend, speech, onOpenDraft, onDraftClaim, busy, voiceError }) {
  const endRef = useRef(null)
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, phase])

  const submit = (e) => { e.preventDefault(); if (input.trim() && !busy) onSend(input) }
  const status = PHASE_TEXT[phase]

  return (
    <section aria-label="AI assistant" className="flex h-full min-h-0 flex-col">
      <div className="scroll-thin min-h-0 flex-1 space-y-4 overflow-y-auto px-3.5 py-4 sm:space-y-5 sm:px-8 sm:py-6" aria-live="polite">
        {messages.length === 0 && (
          <div className="max-w-xl">
            <h1 className="text-[26px] font-bold leading-tight sm:text-[32px] md:text-[36px]">Your Home, Your Love</h1>
            <p className="mt-2 text-[15px] text-slate sm:mt-3 sm:text-[18px]">Tell me what you bought, ask whether something is covered, or describe a problem and I’ll draft the claim.</p>
            <div className="mt-4 flex flex-col items-start gap-2 sm:mt-6">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => onSend(s)} disabled={busy}
                  className="w-full text-left rounded-xl border border-line bg-white p-2.5 text-[14px] text-charcoal transition hover:border-brand disabled:opacity-50 sm:w-auto sm:px-4 sm:py-2 sm:text-[15px]">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="flex justify-end">
              <p className="max-w-[88%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-charcoal px-3.5 py-2 text-[15px] text-white sm:max-w-[85%] sm:px-4 sm:py-2.5 sm:text-[16px]">{m.text}</p>
            </div>
          ) : (
            <div key={i} className="flex gap-2.5 sm:gap-3">
              <span className="mt-1 shrink-0"><Logo size={24} /></span>
              <div className="min-w-0 max-w-[92%] sm:max-w-[88%]">
                <p className={`whitespace-pre-wrap text-[16px] leading-snug sm:text-[18px] ${m.error ? 'text-bad' : 'text-charcoal'}`}>{m.text}</p>
                {m.events?.map((ev, j) => <ToolChip key={j} ev={ev} />)}
                {m.events && <Results events={m.events} onOpenDraft={onOpenDraft} onDraftClaim={onDraftClaim} />}
              </div>
            </div>
          ),
        )}

        {status && (
          <div className="flex items-center gap-2.5 text-[14px] text-slate sm:gap-3 sm:text-[15px]" role="status">
            <span className="ml-1 flex gap-1" aria-hidden="true">
              {[0, 1, 2].map((d) => <span key={d} className="h-2 w-2 animate-dots rounded-full bg-ai" style={{ animationDelay: `${d * 0.2}s` }} />)}
            </span>
            {status}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-line bg-white px-2.5 py-2.5 sm:px-8 sm:py-3">
        {voiceError && <p role="alert" className="mb-2 text-[13px] text-bad sm:text-[14px]">{voiceError}</p>}
        <form onSubmit={submit} className="flex items-center gap-1.5 sm:gap-2">
          <div className={`flex min-w-0 flex-1 items-center rounded-2xl border bg-canvas px-3 transition-all duration-200 focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/35 focus-within:bg-white sm:px-4 ${speech.listening ? 'border-ai ring-2 ring-ai/30' : 'border-line'}`}>
            <input
              value={input} onChange={(e) => setInput(e.target.value)} maxLength={1000}
              placeholder={speech.listening ? 'Listening…' : 'Ask or describe a purchase…'}
              aria-label="Message" disabled={busy && phase !== 'idle'}
              className="min-w-0 flex-1 bg-transparent py-2.5 text-[15px] outline-none focus:outline-none focus-visible:outline-none border-none placeholder:text-slate sm:py-3 sm:text-[16px]"
            />
          </div>
          {speech.canSpeak && (
            <button type="button"
              onClick={() => { speech.speaking ? speech.stopSpeaking() : speech.setSpeakReplies(!speech.speakReplies) }}
              aria-label={speech.speaking ? 'Stop speaking' : speech.speakReplies ? 'Mute spoken replies' : 'Turn on spoken replies'}
              title={speech.speaking ? 'Stop speaking' : speech.speakReplies ? 'Spoken replies on' : 'Spoken replies off'}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl text-slate hover:bg-canvas transition-colors sm:h-11 sm:w-11">
              {speech.speaking ? <X size={18} /> : speech.speakReplies ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>
          )}
          {speech.canListen && <MicButton listening={speech.listening} disabled={busy} onStart={speech.start} onStop={speech.stop} />}
          <button type="submit" disabled={busy || !input.trim()} aria-label="Send message"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-brand text-navy transition hover:brightness-95 disabled:opacity-40 sm:h-11 sm:w-11">
            <SendHorizontal size={18} />
          </button>
        </form>
      </div>
    </section>
  )
}
