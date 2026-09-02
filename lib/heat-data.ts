export type RiskTier = 'Safe' | 'Caution' | 'Extreme Caution' | 'Danger' | 'Extreme Danger'

export interface HeatReading {
  tier: RiskTier
  wbgt: number
  score: number
  temperature: number
  humidity: number
}

export interface HeatStation extends HeatReading {
  id: string
  name: string
  x: number
  y: number
}

export const TIER_CONFIG: Record<RiskTier, { label: string; color: string; badge: string; ring: string; order: number }> = {
  Safe: { label: 'Safe', color: '#16a34a', badge: 'bg-emerald-100 text-emerald-800 border-emerald-300', ring: 'ring-emerald-400', order: 0 },
  Caution: { label: 'Caution', color: '#eab308', badge: 'bg-yellow-100 text-yellow-800 border-yellow-300', ring: 'ring-yellow-400', order: 1 },
  'Extreme Caution': { label: 'Extreme Caution', color: '#f97316', badge: 'bg-orange-100 text-orange-800 border-orange-300', ring: 'ring-orange-400', order: 2 },
  Danger: { label: 'Danger', color: '#dc2626', badge: 'bg-red-100 text-red-800 border-red-300', ring: 'ring-red-500', order: 3 },
  'Extreme Danger': { label: 'Extreme Danger', color: '#7f1d1d', badge: 'bg-red-200 text-red-900 border-red-400', ring: 'ring-red-800', order: 4 },
}

export const RANGES = {
  temperature: { min: 20, max: 50, unit: '°C' },
  humidity: { min: 0, max: 100, unit: '%' },
  score: { min: 0, max: 100, unit: '/100' },
}
