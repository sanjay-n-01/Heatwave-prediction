'use client'

import { Activity, ArrowLeft, ShieldCheck, ThermometerSun } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { IndiaMap } from './india-map'

export function MapPageContent() {
  const router = useRouter()
  return <main className="min-h-screen bg-[#f5f8f7] text-slate-900"><header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-teal-700 text-white"><ThermometerSun className="h-5 w-5" /></div><div><p className="text-base font-bold tracking-tight">HeatShield</p><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">India heat intelligence</p></div></div><div className="hidden items-center gap-2 text-xs font-medium text-slate-500 sm:flex"><ShieldCheck className="h-4 w-4 text-teal-600" /> Your data stays private</div></header><section className="mx-auto max-w-3xl px-5 pb-12 pt-4 sm:px-8"><button type="button" onClick={() => router.push('/')} className="mb-6 flex items-center gap-2 text-sm font-semibold text-teal-700"><ArrowLeft className="h-4 w-4" /> Back to personal details</button><div className="mb-8"><p className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-teal-700"><Activity className="h-4 w-4" /> Step 2 of 2</p><h1 className="text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">Choose your location for a sharper forecast.</h1><p className="mt-4 max-w-xl text-base leading-7 text-slate-500">Tap a city marker or city button to explore the current heat risk.</p></div><IndiaMap /></section></main>
}
