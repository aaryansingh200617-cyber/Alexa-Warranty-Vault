import { useCallback, useEffect, useRef, useState } from 'react'

const Recognition = typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : null

/**
 * Finds the voice closest to Amazon Alexa (warm, natural US English female voice).
 * Priority:
 *  1. Microsoft Natural Online voices (Jenny / Aria / Michelle in Edge on Windows)
 *  2. Google US English female (Chrome)
 *  3. Apple Samantha / Victoria (macOS / iOS)
 *  4. Microsoft Zira (Windows built-in female)
 *  5. Any English female voice
 */
function findAlexaVoice(voices) {
  if (!voices || voices.length === 0) return null

  const candidates = [
    /microsoft jenny/i,
    /microsoft aria/i,
    /microsoft michelle/i,
    /google us english/i,
    /samantha/i,
    /karen/i,
    /victoria/i,
    /microsoft zira/i,
  ]

  // Check top candidate patterns for English voices
  for (const pattern of candidates) {
    const match = voices.find((v) => pattern.test(v.name) && v.lang?.startsWith('en'))
    if (match) return match
  }

  // Look for any English voice with 'female' or 'woman' in name
  const femaleEn = voices.find(
    (v) => v.lang?.startsWith('en') && (/female/i.test(v.name) || /woman/i.test(v.name))
  )
  if (femaleEn) return femaleEn

  // Pick an English (preferably en-US) voice that is NOT an explicit male voice
  const malePattern = /male|david|mark|george|guy|christopher|eric|stefan|james|brian|richard|ryan|ravi/i
  const enUsFemale = voices.find(
    (v) => (v.lang === 'en-US' || v.lang === 'en_US') && !malePattern.test(v.name)
  )
  if (enUsFemale) return enUsFemale

  const anyEn = voices.find((v) => v.lang?.startsWith('en') && !malePattern.test(v.name))
  if (anyEn) return anyEn

  return voices.find((v) => v.default) || voices[0] || null
}

/** Browser speech input + output with Alexa-style female voice synthesis. */
export default function useSpeech({ onFinal, onInterim }) {
  const recRef = useRef(null)
  const voiceRef = useRef(null)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [voiceError, setVoiceError] = useState('')
  const [speakReplies, setSpeakReplies] = useState(true)
  const canListen = Boolean(Recognition)
  const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window

  // Load and cache voices, updating when voiceschanged fires
  useEffect(() => {
    if (!canSpeak) return

    const updateVoice = () => {
      const allVoices = window.speechSynthesis.getVoices()
      voiceRef.current = findAlexaVoice(allVoices)
    }

    updateVoice()
    window.speechSynthesis.addEventListener('voiceschanged', updateVoice)
    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', updateVoice)
    }
  }, [canSpeak])

  const start = useCallback(() => {
    if (!Recognition) return setVoiceError('Voice input isn’t supported in this browser. Type your request instead.')
    setVoiceError('')
    window.speechSynthesis?.cancel()
    const rec = new Recognition()
    rec.lang = navigator.language || 'en-US'
    rec.interimResults = true
    rec.continuous = false
    rec.onstart = () => setListening(true)
    rec.onresult = (e) => {
      const text = Array.from(e.results).map((r) => r[0].transcript).join('')
      if (e.results[e.results.length - 1].isFinal) onFinal?.(text.trim())
      else onInterim?.(text)
    }
    rec.onerror = (e) => {
      const msg = {
        'not-allowed': 'Microphone access was blocked. Allow it in your browser settings, or type instead.',
        'service-not-allowed': 'Microphone access was blocked. Allow it in your browser settings, or type instead.',
        'no-speech': 'I didn’t hear anything. Tap the microphone and try again.',
        'audio-capture': 'No microphone was found. Type your request instead.',
        network: 'Speech recognition needs an internet connection in this browser.',
      }[e.error]
      if (e.error !== 'aborted') setVoiceError(msg || 'Voice input stopped unexpectedly. Try again or type.')
    }
    rec.onend = () => setListening(false)
    recRef.current = rec
    try { rec.start() } catch { setListening(false) }
  }, [onFinal, onInterim])

  const stop = useCallback(() => recRef.current?.stop(), [])

  const stopSpeaking = useCallback(() => { window.speechSynthesis?.cancel(); setSpeaking(false) }, [])

  const speak = useCallback((text) => {
    if (!canSpeak || !speakReplies || !text) return
    window.speechSynthesis.cancel()

    // Strip markdown formatting before speaking for clear Alexa-like pronunciation
    const cleanText = text
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/#+\s+/g, '')

    const u = new SpeechSynthesisUtterance(cleanText)

    // Select the best Alexa-like female voice
    const activeVoice = voiceRef.current || findAlexaVoice(window.speechSynthesis.getVoices())
    if (activeVoice) {
      u.voice = activeVoice
      u.lang = activeVoice.lang || 'en-US'
    }

    // Alexa cadence: natural rate and slightly warm female pitch
    u.rate = 1.0
    u.pitch = 1.05

    u.onstart = () => setSpeaking(true)
    u.onend = () => setSpeaking(false)
    u.onerror = () => setSpeaking(false)
    window.speechSynthesis.speak(u)
  }, [canSpeak, speakReplies])

  useEffect(() => () => { recRef.current?.abort(); window.speechSynthesis?.cancel() }, [])

  return { canListen, canSpeak, listening, speaking, voiceError, setVoiceError, speakReplies, setSpeakReplies, start, stop, speak, stopSpeaking }
}
