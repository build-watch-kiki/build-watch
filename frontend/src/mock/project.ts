import type { Project } from '@/types/projects.ts'

export const MOCK_PROJECT: Project = {
  id: 0,
  name: 'Плановое дорожное развитие',
  startDate: '2026-09-20',
  endDate: '2026-10-06',
  createdAt: '2026-09-20T09:00:00.000Z',
  projectType: {
    id: 0,
    name: 'Дорожное строительство',
    createdAt: '2026-09-20T09:00:00.000Z'
  }
}
