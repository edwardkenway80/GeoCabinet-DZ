import { Briefcase } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function ProjetsPage() {
  return (
    <ComingSoon
      title="Gestion des projets"
      description="Organisez les projets du bureau, affectez les membres de l'équipe et suivez les jalons de chaque projet."
      icon={<Briefcase size={28} strokeWidth={2} />}
    />
  )
}