import { Map } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function CartePage() {
  return (
    <ComingSoon
      title="Carte géographique"
      description="Visualisez les dossiers et les biens sur une carte. Ce module sera disponible dans une prochaine version."
      icon={<Map size={28} strokeWidth={2} />}
    />
  )
}