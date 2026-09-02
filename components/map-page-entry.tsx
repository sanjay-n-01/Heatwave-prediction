'use client'

import dynamic from 'next/dynamic'

const MapPageContent = dynamic(() => import('./map-page').then((module) => module.MapPageContent), { ssr: false })

export function MapPageEntry() {
  return <MapPageContent />
}
