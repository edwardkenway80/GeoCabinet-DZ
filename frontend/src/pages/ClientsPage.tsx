import { Users } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function ClientsPage() {
  return (
    <ComingSoon
      title="Gestion des clients"
      description="Consultez, créez et modifiez la fiche de chaque client du bureau. L'historique des dossiers associés sera accessible depuis cette page."
      icon={<Users size={28} strokeWidth={2} />}
    />
  )
}