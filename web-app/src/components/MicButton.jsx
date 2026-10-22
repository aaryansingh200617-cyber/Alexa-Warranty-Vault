import { Mic, Square } from 'lucide-react'

/** The one memorable element: a cyan ring that pulses while the assistant listens. */
export default function MicButton({ listening, disabled, onStart, onStop }) {
  return (
    <span className="relative inline-flex">
      {listening && <span className="absolute inset-0 animate-ring rounded-2xl bg-ai" aria-hidden="true" />}
      <button
        type="button"
        onClick={listening ? onStop : onStart}
        disabled={disabled}
        aria-pressed={listening}
        aria-label={listening ? 'Stop listening' : 'Speak your request'}
        className={`relative flex h-10 w-10 sm:h-11 sm:w-11 items-center justify-center rounded-2xl transition disabled:opacity-50 ${
          listening ? 'bg-ai text-navy' : 'bg-charcoal text-white hover:bg-navy'
        }`}
      >
        {listening ? <Square size={15} fill="currentColor" /> : <Mic size={18} className="sm:hidden" />}
        {!listening && <Mic size={20} className="hidden sm:block" />}
      </button>
    </span>
  )
}
