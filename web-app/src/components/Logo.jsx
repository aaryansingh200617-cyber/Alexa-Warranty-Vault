export default function Logo({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" role="img" aria-label="Warranty Vault logo">
      <rect width="32" height="32" rx="8" fill="#232F3E" />
      <path d="M16 5l9 3.5v7c0 5.2-3.7 9.3-9 11.5-5.3-2.2-9-6.3-9-11.5v-7z" fill="none" stroke="#FF9900" strokeWidth="2" strokeLinejoin="round" />
      <path d="M11.5 16l3.2 3.2 6-6.4" fill="none" stroke="#00C8E8" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
