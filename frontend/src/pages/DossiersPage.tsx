import { FolderOpen } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function DossiersPage() {
  return (
    <ComingSoon
      title="Gestion des dossiers"
      description="Suivez l'avancement des dossiers clients, leurs échéances et les documents associés. Chaque dossier sera lié à un client et à une mission."
      icon={<FolderOpen size={28} strokeWidth={2} />}
    />
  )
}