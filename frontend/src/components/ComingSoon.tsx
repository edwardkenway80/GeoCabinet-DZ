import type { ReactNode } from 'react'

interface Props {
  title: string
  description: string
  icon: ReactNode
}

export default function ComingSoon({ title, description, icon }: Props) {
  return (
    <div>
      <h1 style={S.title}>{title}</h1>
      <div style={S.card}>
        <div style={S.iconWrap}>{icon}</div>
        <h2 style={S.h2}>Module en cours de développement</h2>
        <p style={S.p}>{description}</p>
        <div style={S.badge}>API non disponible</div>
      </div>
    </div>
  )
}

const S: Record<string, React.CSSProperties> = {
  title: { fontSize: 22, fontWeight: 700, color: '#1a202c', marginBottom: 24 },
  card: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '60px 40px', textAlign: 'center', maxWidth: 480 },
  iconWrap: { color: '#94a3b8', marginBottom: 16, display: 'flex', justifyContent: 'center' },
  h2: { fontSize: 16, fontWeight: 600, color: '#374151', marginBottom: 8 },
  p: { fontSize: 14, color: '#64748b', lineHeight: 1.6, marginBottom: 20 },
  badge: { display: 'inline-block', background: '#f1f5f9', color: '#64748b', fontSize: 12, fontWeight: 500, padding: '4px 12px', borderRadius: 20 },
}
