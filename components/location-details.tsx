'use client'

import type { cities } from '@/lib/cities'

type City = (typeof cities)[number]

export function LocationDetails({ city }: { city: City }) {
  const meter = Math.min(100, city.score)
  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 text-slate-900 sm:px-10">
      <div className="mx-auto max-w-5xl">
        <a href="/map" onClick={(event) => { event.preventDefault(); window.location.assign('/map') }} className="text-sm font-semibold text-teal-700">← Back to map</a>
        <div className="mt-6 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-10">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div><p className="text-xs font-bold uppercase tracking-[0.2em] text-teal-700">Location heat profile</p><h1 className="mt-2 text-3xl font-bold tracking-tight">{city.name}, {city.state}</h1><p className="mt-2 text-slate-500">Current environmental conditions and heat stress response.</p></div>
            <span className="rounded-full px-4 py-2 text-sm font-bold text-white" style={{ backgroundColor: city.risk === 'Extreme' ? '#991b1b' : city.risk === 'Danger' ? '#ef4444' : city.risk === 'High' ? '#f97316' : '#eab308' }}>{city.risk} risk</span>
          </div>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {[['Temperature', `${city.temperature}°C`, 'bg-orange-50 text-orange-700'], ['Humidity', `${city.humidity}%`, 'bg-sky-50 text-sky-700'], ['WBGT', `${city.wbgt}°C`, 'bg-amber-50 text-amber-700'], ['HTSI', `${city.score}/100`, 'bg-red-50 text-red-700']].map(([label, value, style]) => <div key={label} className={`rounded-2xl p-5 ${style}`}><p className="text-xs font-bold uppercase tracking-wider">{label}</p><p className="mt-3 text-3xl font-bold">{value}</p></div>)}
          </div>
          <div className="mt-10 rounded-2xl border border-slate-200 bg-slate-50 p-6"><div className="flex items-center justify-between"><div><h2 className="font-bold">HTSI meter</h2><p className="mt-1 text-sm text-slate-500">Heat Thermal Stress Index</p></div><strong className="text-2xl text-red-600">{meter}</strong></div><div className="mt-5 h-5 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-gradient-to-r from-yellow-400 via-orange-500 to-red-700" style={{ width: `${meter}%` }} /></div><div className="mt-2 flex justify-between text-xs text-slate-500"><span>Low</span><span>Moderate</span><span>Danger</span><span>Extreme</span></div></div>
        </div>
      </div>
    </main>
  )
}
