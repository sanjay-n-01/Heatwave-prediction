'use client'

import dynamic from 'next/dynamic'

const Onboarding = dynamic(() => import('./onboarding').then((module) => module.Onboarding), { ssr: false })

export function OnboardingEntry() {
  return <Onboarding />
}
