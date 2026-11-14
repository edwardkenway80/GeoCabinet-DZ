import { ClipboardList } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function MissionsPage() {
  return (
    <ComingSoon
      title="Gestion des missions"
      description="Définissez les missions d'expertise, leurs objectifs, leurs livrables et leur statut d'avancement."
      icon={<ClipboardList size={28} strokeWidth={2} />}
    />
  )
}