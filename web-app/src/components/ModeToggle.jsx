import { Sparkles, WifiOff } from 'lucide-react'

/**
 * ModeToggle - Responsive segmented sliding toggle: Offline <-> AI Online
 *
 * Smooth sliding pill indicator with fluid easing and glow effect.
 * Responsive sizing for small mobile screens through desktop.
 */
export default function ModeToggle({ online, onToggle, disabled }) {
  return (
    <div
      role="radiogroup"
      aria-label="Assistant mode selection"
      className="relative inline-flex items-center rounded-full bg-charcoal/80 p-0.5 sm:p-1 border border-white/15 shadow-inner backdrop-blur-sm select-none"
    >
      {/* Smooth sliding pill indicator */}
      <span
        aria-hidden="true"
        className={`absolute top-0.5 sm:top-1 bottom-0.5 sm:bottom-1 w-[calc(50%-2px)] sm:w-[calc(50%-4px)] rounded-full transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] shadow-sm pointer-events-none ${
          online
            ? 'left-[calc(50%+1px)] sm:left-[calc(50%+2px)] bg-gradient-to-r from-ai to-[#38bdf8] shadow-[0_0_12px_rgba(0,200,232,0.45)]'
            : 'left-0.5 sm:left-1 bg-white/20 border border-white/10'
        }`}
      />

      {/* Offline Option */}
      <button
        id="mode-toggle-offline"
        type="button"
        role="radio"
        aria-checked={!online}
        onClick={() => online && onToggle()}
        disabled={disabled}
        title="Switch to Offline mode (built-in rule agent)"
        className={`relative z-10 flex items-center justify-center gap-1 sm:gap-1.5 rounded-full px-2.5 sm:px-3.5 py-0.5 sm:py-1 text-[11px] sm:text-xs font-semibold transition-colors duration-200 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ai disabled:cursor-not-allowed disabled:opacity-50 ${
          !online
            ? 'text-white'
            : 'text-white/50 hover:text-white/80'
        }`}
      >
        <WifiOff size={12} aria-hidden="true" className={`shrink-0 ${!online ? 'text-white' : 'text-white/50'}`} />
        <span>Offline</span>
      </button>

      {/* AI Online Option */}
      <button
        id="mode-toggle-online"
        type="button"
        role="radio"
        aria-checked={online}
        onClick={() => !online && onToggle()}
        disabled={disabled}
        title="Switch to Online mode (LLM AI agent)"
        className={`relative z-10 flex items-center justify-center gap-1 sm:gap-1.5 rounded-full px-2.5 sm:px-3.5 py-0.5 sm:py-1 text-[11px] sm:text-xs font-semibold transition-colors duration-200 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ai disabled:cursor-not-allowed disabled:opacity-50 ${
          online
            ? 'text-navy font-bold'
            : 'text-white/50 hover:text-white/80'
        }`}
      >
        <Sparkles size={12} aria-hidden="true" className={`shrink-0 ${online ? 'text-navy' : 'text-white/50'}`} />
        <span>AI Online</span>
      </button>
    </div>
  )
}
