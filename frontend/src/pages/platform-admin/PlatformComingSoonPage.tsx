import { useEffect, useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

interface Props {
  module: string
  description: string
  status: 'operational' | 'pending-api' | 'not-started'
}

export default function PlatformComingSoonPage({ module, description, status }: Props) {
  const { user } = useAuth()
  const [error, setError] = useState('')

  const isPlatformAdmin = user?.is_platform_admin ?? false

  const statusInfo: Record<string, { label: string; color: string; bg: string }> = {
    operational: { label: 'متصل ببيانات حقيقية', color: '#2e7d32', bg: '#e8f5e9' },
    'pending-api': { label: 'واجهة موجودة — بانتظار API', color: '#d97706', bg: '#fef3c7' },
    'not-started': { label: 'لم يبدأ التطوير بعد', color: '#64748b', bg: '#f1f5f9' },
  }

  const info = statusInfo[status]

  useEffect(() => {
    if (!isPlatformAdmin) {
      setError('هذه الصفحة مخصصة لمسيري المنصة فقط.')
    }
  }, [isPlatformAdmin])

  return (
    <div>
      <div style={S.header}>
        <h1 style={S.title}>{module}</h1>
        <p style={S.sub}>{description}</p>
      </div>

      {error && <div style={S.err}>{error}</div>}

      <div style={S.statusBanner}>
        <span style={{ ...S.statusDot, background: info.color }}></span>
        <span style={S.statusLabel}>{info.label}</span>
      </div>

      <div style={S.card}>
        <div style={S.iconWrap}>
          <span style={S.bigIcon}>📄</span>
        </div>
        <h2 style={S.h2}>وحدة {module}</h2>
        <p style={S.p}>
          {status === 'operational'
            ? 'هذه الوحدة متصلة بواجهات برمجية حقيقية وتعرض بيانات من قاعدة البيانات.'
            : status === 'pending-api'
            ? 'تم إنشاء واجهة المستخدم لهذه الوحدة، ولكن واجهات البرمجة (API) المرتبطة بها قيد التطوير في المراحل القادمة.'
            : 'هذه الوحدة مخططة للتطوير في المراحل القادمة من خطة المنصة.'
          }
        </p>
      </div>

      <div style={S.note}>
        <strong>ملاحظة:</strong> لا توجد بيانات تجريبية أو وهمية معروضة. جميع البيانات تأتي من مصادر حقيقية عبر واجهات برمجية (عند توفرها).
      </div>
    </div>
  )
}

const S: Record<string, React.CSSProperties> = {
  header: { marginBottom: 28 },
  title: { fontSize: 22, fontWeight: 700, color: '#1a202c', marginBottom: 4 },
  sub: { fontSize: 14, color: '#64748b' },
  err: {
    background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626',
    padding: '12px 16px', borderRadius: 8, fontSize: 13, marginBottom: 20,
  },
  statusBanner: {
    display: 'flex', alignItems: 'center', gap: 8,
    background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
    padding: '10px 16px', fontSize: 13, color: '#374151', marginBottom: 24,
  },
  statusDot: {
    width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
  },
  statusLabel: { fontSize: 13, fontWeight: 500 },
  card: {
    background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
    padding: '40px 32px', textAlign: 'center', maxWidth: 500, margin: '0 auto',
  },
  iconWrap: {
    width: 64, height: 64, borderRadius: 12,
    background: '#e8f0fb', display: 'flex', alignItems: 'center',
    justifyContent: 'center', margin: '0 auto 20px',
  },
  bigIcon: { fontSize: 32 },
  h2: { fontSize: 18, fontWeight: 600, color: '#1a202c', marginBottom: 8 },
  p: { fontSize: 14, color: '#64748b', lineHeight: 1.6 },
  note: {
    marginTop: 24, fontSize: 12, color: '#94a3b8',
    background: '#f8fafc', borderRadius: 6, padding: '10px 14px',
  },
}