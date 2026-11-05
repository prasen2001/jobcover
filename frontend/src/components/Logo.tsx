export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="logo" aria-label="JobCover home">
      <span className="logo-mark">J</span>
      {!compact && <span>JobCover</span>}
    </div>
  )
}

