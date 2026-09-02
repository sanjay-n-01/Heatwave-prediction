import { LocationDetails } from '@/components/location-details'
import { cities } from '@/lib/cities'

export default async function LocationDetailsPage({ searchParams }: { searchParams: Promise<{ city?: string }> }) {
  const { city: cityName } = await searchParams
  const city = cities.find((item) => item.name === cityName) ?? cities[3]
  return <LocationDetails city={city} />
}
