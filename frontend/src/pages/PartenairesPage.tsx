import { Handshake } from 'lucide-react'
import ComingSoon from '../components/ComingSoon'

export default function PartenairesPage() {
  return (
    <ComingSoon
      title="Gestion des partenaires"
      description="Répertoriez les partenaires du bureau : notaires, avocats, banques, administrations et autres intervenants externes."
      icon={<Handshake size={28} strokeWidth={2} />}
    />
  )
}