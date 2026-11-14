import { Settings } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function ParametresPage() {
  return (
    <ComingSoon
      title="Paramètres"
      description="Configurez les préférences du bureau, la langue, les notifications et les options d'affichage."
      icon={<Settings size={28} strokeWidth={2} />}
    />
  )
}