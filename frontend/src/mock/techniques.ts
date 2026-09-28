export interface MockTechnique {
  id: number
  name: string
  nameRu: string
  color: string
}

/** Единый справочник техники мок-проекта: фото, стадии и прогресс ссылаются на него. */
export const MOCK_TECHNIQUES: MockTechnique[] = [
  { id: 1, name: 'excavator', nameRu: 'Экскаватор', color: '#C27803' },
  { id: 2, name: 'dump_truck', nameRu: 'Самосвал', color: '#2563EB' },
  { id: 3, name: 'roller', nameRu: 'Каток', color: '#7C3AED' },
  { id: 4, name: 'grader', nameRu: 'Автогрейдер', color: '#0F766E' },
  { id: 5, name: 'truck_crane', nameRu: 'Автокран', color: '#BE185D' }
]

export function mockTechniqueById(id: number): MockTechnique {
  const found = MOCK_TECHNIQUES.find((item) => item.id === id)
  if (!found) throw new Error(`Unknown mock technique id: ${id}`)
  return found
}
