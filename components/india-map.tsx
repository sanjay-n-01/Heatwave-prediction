'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { GeoJSON, MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import L, { type GeoJsonObject, type LatLngExpression } from 'leaflet'
import axios from 'axios'
import 'leaflet/dist/leaflet.css'

const riskColors = {
  Moderate: '#eab308',
  High: '#f97316',
  Danger: '#ef4444',
  Extreme: '#991b1b',
} as const

const markerIconFor = (risk: keyof typeof riskColors) => L.divIcon({
  className: 'heat-marker',
  html: `<span style="--marker-color:${riskColors[risk]}"></span>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -12],
})

const cities = [
  { name: 'Delhi', state: 'Delhi NCR', coordinates: [28.6, 77.2] as LatLngExpression, risk: 'Extreme', wbgt: 35.8, score: 86, temperature: 42.1, humidity: 38 },
  { name: 'Jaipur', state: 'Rajasthan', coordinates: [26.91, 75.79] as LatLngExpression, risk: 'High', wbgt: 34.9, score: 78, temperature: 40.4, humidity: 34 },
  { name: 'Mumbai', state: 'Maharashtra', coordinates: [19.08, 72.88] as LatLngExpression, risk: 'High', wbgt: 32.7, score: 69, temperature: 33.8, humidity: 72 },
  { name: 'Chennai', state: 'Tamil Nadu', coordinates: [13.08, 80.27] as LatLngExpression, risk: 'Danger', wbgt: 34.2, score: 72, temperature: 36.2, humidity: 68 },
  { name: 'Kolkata', state: 'West Bengal', coordinates: [22.57, 88.36] as LatLngExpression, risk: 'Moderate', wbgt: 31.8, score: 61, temperature: 34.5, humidity: 64 },
]

function IndiaStates() {
  const [states, setStates] = useState<GeoJsonObject | null>(null)

  useEffect(() => {
    axios.get<GeoJsonObject>('https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson')
      .then(({ data }) => setStates(data))
      .catch(() => setStates(null))
  }, [])

  if (!states) return null
  return <GeoJSON data={states} style={(feature) => {
    const name = String(feature?.properties?.NAME_1 ?? feature?.properties?.st_nm ?? feature?.properties?.name ?? '').toLowerCase()
    const matched = cities.find((city) => name.includes(city.state.split(' ')[0].toLowerCase()))
    const risk = matched?.risk as keyof typeof riskColors | undefined
    return { color: risk ? riskColors[risk] : '#0f766e', weight: risk ? 2 : 1.2, fillColor: risk ? riskColors[risk] : '#14b8a6', fillOpacity: risk ? 0.28 : 0.1 }
  }} />
}

function MapScrollControl() {
  const map = useMapEvents({
    mouseover: () => map.scrollWheelZoom.enable(),
    mouseout: () => map.scrollWheelZoom.disable(),
  })
  useEffect(() => {
    map.scrollWheelZoom.disable()
    return () => map.scrollWheelZoom.disable()
  }, [map])
  return null
}

function CityFocus({ city }: { city: (typeof cities)[number] | undefined }) {
  const map = useMap()
  useEffect(() => {
    if (city) map.flyTo(city.coordinates, 6, { duration: 0.8 })
  }, [city, map])
  return null
}

export function IndiaMap({ onCityChange }: { onCityChange?: (city: (typeof cities)[number]) => void }) {
  const [selectedCity, setSelectedCity] = useState(cities[3])
  const router = useRouter()

  const selectCity = (city: (typeof cities)[number]) => {
    setSelectedCity(city)
    onCityChange?.(city)
    router.push(`/location-details?city=${encodeURIComponent(city.name)}`)
  }

  return (
    <div className="relative overflow-hidden rounded-[1.5rem] border border-slate-200 bg-slate-100 shadow-sm">
      <MapContainer center={[21.2, 79.1]} zoom={4.7} minZoom={4.7} maxZoom={10} maxBounds={[[5.5, 67.5], [37.5, 98.5]]} maxBoundsViscosity={0.9} wheelDebounceTime={80} wheelPxPerZoomLevel={100} scrollWheelZoom={false} dragging={true} doubleClickZoom={true} touchZoom={true} className="h-[27rem] w-full">
        <MapScrollControl />
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <IndiaStates />
        {cities.map((city) => (
          <Marker key={city.name} position={city.coordinates} icon={markerIconFor(city.risk as keyof typeof riskColors)} eventHandlers={{ click: () => selectCity(city) }}>
            
          </Marker>
        ))}
        <CityFocus city={selectedCity} />
      </MapContainer>
      <div className="pointer-events-none absolute left-4 top-4 rounded-xl border border-white/70 bg-white/90 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm backdrop-blur">
        Select a city to view conditions
      </div>
      <div className="absolute right-4 top-4 rounded-xl border border-white/70 bg-white/90 px-3 py-2 shadow-sm backdrop-blur">
        <p className="mb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Risk level</p>
        <div className="flex gap-2 text-[10px] font-semibold text-slate-700">
          {Object.entries(riskColors).map(([risk, color]) => <span key={risk} className="flex items-center gap-1"><i className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />{risk}</span>)}
        </div>
      </div>
      <div className="absolute left-16 right-4 top-14 flex flex-wrap gap-1.5">
        {cities.map((city) => <button key={city.name} type="button" onClick={() => selectCity(city)} aria-label={`Select ${city.name}`} className={`rounded-full border px-2.5 py-1 text-[11px] font-bold shadow-sm backdrop-blur transition ${selectedCity.name === city.name ? 'border-teal-700 bg-teal-700 text-white' : 'border-white/80 bg-white/90 text-slate-700 hover:border-teal-400'}`}>{city.name}</button>)}
      </div>
    </div>
  )
}

export { cities }
