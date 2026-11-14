import { FileText } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function DocumentsPage() {
  return (
    <ComingSoon
      title="Gestion des documents"
      description="Stockez, classez et retrouvez les documents liés aux dossiers, projets et clients du bureau."
      icon={<FileText size={28} strokeWidth={2} />}
    />
  )
}