import { useCallback, useEffect, useRef, useState } from 'react'
import { LayoutDashboard, MessageSquare } from 'lucide-react'
import { api } from './services/api'
import useSpeech from './hooks/useSpeech'
import ChatPanel from './components/ChatPanel'
import ClaimPanel from './components/ClaimPanel'
import Dashboard from './components/Dashboard'
import Logo from './components/Logo'
import ModeToggle from './components/ModeToggle'

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [phase, setPhase] = useState('idle') // idle | listening | processing | tool | responding | error
  const [dash, setDash] = useState(null)
  const [dashError, setDashError] = useState('')
  const [health, setHealth] = useState({ mcp_connected: null, mode: 'offline' })
  const [draft, setDraft] = useState(null)
  const [tab, setTab] = useState('chat') // mobile tab
  // Online = use LLM AI; Offline = always use the built-in rule agent
  const [onlineMode, setOnlineModeRaw] = useState(() => localStorage.getItem('wv_mode') === 'online')
  const setOnlineMode = (v) => { setOnlineModeRaw(v); localStorage.setItem('wv_mode', v ? 'online' : 'offline') }
  const sessionId = useRef(null)
  const sendRef = useRef(() => {})

  const refreshDash = useCallback(async () => {
    try { setDash(await api.dashboard()); setDashError('') }
    catch (e) { setDashError(e.message) }
  }, [])

  const refreshHealth = useCallback(async () => {
    try { setHealth(await api.health()) } catch { setHealth({ mcp_connected: false, mode: 'offline', unreachable: true }) }
  }, [])

  const speech = useSpeech({
    onInterim: (t) => setInput(t),
    onFinal: (t) => { setInput(t); sendRef.current(t) },
  })

  useEffect(() => {
    refreshDash(); refreshHealth()
    const id = setInterval(refreshHealth, 15000)
    return () => clearInterval(id)
  }, [refreshDash, refreshHealth])

  const busy = phase === 'processing' || phase === 'tool'

  const send = useCallback(async (text) => {
    text = text.trim()
    if (!text || busy) return
    speech.stopSpeaking()
    setInput('')
    setMessages((m) => [...m, { role: 'user', text }])
    setPhase('processing')
    const toolTimer = setTimeout(() => setPhase((p) => (p === 'processing' ? 'tool' : p)), 700)
    try {
      const forceMode = onlineMode ? 'online' : 'offline'
      const res = await api.chat(text, sessionId.current, forceMode)
      sessionId.current = res.session_id
      setMessages((m) => [...m, { role: 'assistant', text: res.reply, events: res.events, error: res.error }])
      setHealth((h) => ({ ...h, mode: res.mode }))
      const done = res.events?.find((e) => e.name === 'draft_claim' && e.ok)
      if (done) setDraft(done.result)
      if (res.events?.length) refreshDash()
      if (res.error) { setPhase('error'); refreshHealth() }
      else if (speech.canSpeak && speech.speakReplies) { setPhase('responding'); speech.speak(res.reply); setTimeout(() => setPhase('idle'), 400) }
      else setPhase('idle')
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', error: true, text: `I couldn’t reach the Warranty Vault service (${e.message}). Check that the agent API is running on port 8000.` }])
      setPhase('error'); refreshHealth()
    } finally {
      clearTimeout(toolTimer)
    }
  }, [busy, onlineMode, speech, refreshDash, refreshHealth])
  sendRef.current = send

  const effectivePhase = speech.listening ? 'listening' : speech.speaking && phase === 'idle' ? 'responding' : phase

  const openSavedClaim = (c) => {
    const purchase = dash.purchases.find((p) => p.id === c.purchase_id)
    setDraft({ claim: { id: c.id, subject: c.draft_subject, body: c.draft_body, issue_description: c.issue_description }, purchase, warnings: [] })
  }
  const handleDraftClaim = async (purchase) => {
    try {
      const existing = dash?.claims?.find((c) => c.purchase_id === purchase.id)
      if (existing) {
        openSavedClaim(existing)
        return
      }
      const res = await api.draftClaim(purchase.id, purchase.product_name)
      if (res.ok && res.claim) {
        setDraft(res)
        refreshDash()
      }
    } catch (e) {
      alert(`Could not draft claim: ${e.message}`)
    }
  }
  const removePurchase = async (p) => {
    if (!window.confirm(`Remove ${p.product_name} and any claim drafts for it?`)) return
    await api.removePurchase(p.id); refreshDash()
  }
  const seed = async () => { await api.seed(); refreshDash() }

  const connected = health.mcp_connected
  const statusText = health.unreachable ? 'API offline' : connected === null ? 'Connecting…' : connected ? 'MCP connected' : 'MCP offline'
  const dot = connected ? 'bg-ok' : connected === null ? 'bg-slate' : 'bg-bad'

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between bg-navy px-3 py-2.5 text-white sm:px-6 sm:py-3">
        <div className="flex min-w-0 items-center gap-2 sm:gap-3.5">
          <img
            src="/alexa-logo.png"
            alt="Amazon Alexa"
            className="h-6 w-auto shrink-0 select-none object-contain sm:h-8"
          />
          <span className="h-5 w-px shrink-0 bg-white/20 sm:h-6" aria-hidden="true" />
          <div className="shrink-0">
            <Logo size={28} />
          </div>
          <div className="min-w-0 leading-tight">
            <p className="truncate text-[15px] font-bold tracking-tight sm:text-[18px]">Warranty Vault</p>
            <p className="hidden text-[13px] text-white/70 sm:block">Your personal AI warranty assistant</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 text-[13px] sm:gap-3">
          {/* Segmented sliding toggle: Offline ↔ AI Online */}
          <ModeToggle online={onlineMode} onToggle={() => setOnlineMode(!onlineMode)} disabled={busy} />

          {onlineMode && health.model && (
            <span
              className="hidden lg:inline-flex items-center rounded-full border border-ai/40 bg-ai/10 px-2.5 py-0.5 text-[12px] font-medium text-ai"
              title={`LLM Model: ${health.model}`}
            >
              {health.model}
            </span>
          )}

          <span className="hidden md:flex items-center gap-1.5 text-[12px] text-white/80" role="status">
            <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
            {statusText}
          </span>
        </div>
      </header>

      <nav className="grid grid-cols-2 border-b border-line bg-white lg:hidden" aria-label="Views">
        {[['chat', 'Assistant', MessageSquare], ['vault', 'Vault', LayoutDashboard]].map(([id, label, Icon]) => (
          <button key={id} onClick={() => setTab(id)} aria-current={tab === id}
            className={`flex items-center justify-center gap-2 py-2.5 text-[14px] font-semibold transition-colors sm:py-3 sm:text-[15px] ${tab === id ? 'border-b-2 border-brand text-charcoal' : 'text-slate hover:text-charcoal'}`}>
            <Icon size={17} aria-hidden="true" />{label}
            {id === 'vault' && dash?.counts?.total > 0 && (
              <span className="rounded-full bg-slate/15 px-1.5 py-0.2 text-[11px] font-bold text-charcoal">
                {dash.counts.total}
              </span>
            )}
          </button>
        ))}
      </nav>

      <main className="grid min-h-0 flex-1 lg:grid-cols-[minmax(0,1fr)_440px]">
        <div className={`min-h-0 ${tab === 'chat' ? 'block' : 'hidden'} lg:block`}>
          <ChatPanel
            messages={messages} phase={effectivePhase} input={input} setInput={setInput} onSend={send}
            speech={speech} onOpenDraft={setDraft} onDraftClaim={handleDraftClaim} busy={busy} voiceError={speech.voiceError}
          />
        </div>
        <aside aria-label="Warranty overview" className={`scroll-thin min-h-0 overflow-y-auto border-l border-line bg-canvas ${tab === 'vault' ? 'block' : 'hidden'} lg:block`}>
          <Dashboard data={dash} error={dashError} onSeed={seed} onDelete={removePurchase} onOpenClaim={openSavedClaim} onDraftClaim={handleDraftClaim} />
        </aside>
      </main>

      {draft && <ClaimPanel draft={draft} onClose={() => setDraft(null)} onSaved={refreshDash} />}
    </div>
  )
}
