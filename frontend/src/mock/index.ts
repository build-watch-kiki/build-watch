export const MOCK_PROJECT_ID = 0

/** Показывать ли мок-проект в списке (флаг VITE_SHOW_MOCK_PROJECT). */
export function isMockShown(): boolean {
  return import.meta.env.VITE_SHOW_MOCK_PROJECT === 'true'
}

/** Все запросы для проекта id = 0 обслуживаются из src/mock, бэкенд не вызывается. */
export function isMockProject(projectId: number): boolean {
  return isMockShown() && projectId === MOCK_PROJECT_ID
}

export { MOCK_PROJECT } from './project.ts'
export { MOCK_TECHNIQUES } from './techniques.ts'
export { MOCK_STAGES } from './stages.ts'
export { MOCK_PHOTOS } from './photos.ts'
export {
  createMockProgressDetail,
  createMockProgressHistory
} from './progress.ts'
export {
  addMockPhotoFromFile,
  createMockStage,
  deleteMockStage,
  getMockPhoto,
  listMockPhotos,
  listMockStages,
  updateMockStage,
  updateMockStageTechniques
} from './db.ts'
