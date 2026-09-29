export const DEFAULT_PROJECT_TYPE_ICON = 'mdi-office-building-outline'

const PROJECT_TYPE_ICONS: Record<number, string> = {
  0: 'mdi-road-variant',
  1: 'mdi-home-city-outline',
  2: 'mdi-school-outline',
  3: 'mdi-hospital-box-outline',
  4: 'mdi-stadium',
  5: 'mdi-palette-outline',
  6: 'mdi-domain',
  7: 'mdi-toy-brick',
  8: 'mdi-briefcase-outline',
  9: 'mdi-road-variant'
}

export function getProjectTypeIcon(typeId: number | null | undefined): string {
  if (typeId === null || typeId === undefined) {
    return DEFAULT_PROJECT_TYPE_ICON
  }
  return PROJECT_TYPE_ICONS[typeId] ?? DEFAULT_PROJECT_TYPE_ICON
}
