import type { DateTimeString } from '@/types/api.ts'
import type { Requirement, Stage } from '@/types/plan.ts'
import { mockTechniqueById } from './techniques.ts'

const CREATED_AT = '2026-09-20T09:00:00.000Z' as DateTimeString

function requirement(techniqueId: number, quantity: number): Requirement {
  const technique = mockTechniqueById(techniqueId)
  return {
    id: technique.id,
    name: technique.name,
    nameRu: technique.nameRu,
    createdAt: CREATED_AT,
    quantity
  }
}

export const MOCK_STAGES: Stage[] = [
  {
    id: 1,
    parentId: 0,
    workTypeId: 101,
    workTypeName: 'Подготовка основания',
    startDate: '2026-09-20',
    endDate: '2026-09-27',
    createdAt: CREATED_AT,
    requiresTechnique: [requirement(1, 2), requirement(2, 3)],
    actual: null
  },
  {
    id: 2,
    parentId: 1,
    workTypeId: 102,
    workTypeName: 'Снятие растительного слоя',
    startDate: '2026-09-20',
    endDate: '2026-09-21',
    createdAt: CREATED_AT,
    requiresTechnique: [requirement(1, 1)],
    actual: {
      startDate: '2026-09-20',
      endDate: '2026-09-21',
      status: 'on_track',
      deviationDays: 0,
      techniqueDeviationCount: 0,
      message: {
        code: 'ahead',
        severity: 'info',
        text: 'Выполняется по плану'
      }
    }
  },
  {
    id: 3,
    parentId: 1,
    workTypeId: 103,
    workTypeName: 'Устройство песчаного основания',
    startDate: '2026-09-22',
    endDate: '2026-09-27',
    createdAt: CREATED_AT,
    requiresTechnique: [requirement(1, 1), requirement(2, 3)],
    actual: {
      startDate: '2026-09-22',
      endDate: '2026-09-26',
      status: 'ahead',
      deviationDays: 0,
      techniqueDeviationCount: 1,
      message: {
        code: 'ahead',
        severity: 'info',
        text: 'Отклонение по технике'
      }
    }
  },
  {
    id: 4,
    parentId: 0,
    workTypeId: 104,
    workTypeName: 'Укладка асфальта',
    startDate: '2026-09-28',
    endDate: '2026-10-04',
    createdAt: CREATED_AT,
    requiresTechnique: [requirement(3, 1), requirement(4, 1)],
    actual: null
  },
  {
    id: 5,
    parentId: 4,
    workTypeId: 105,
    workTypeName: 'Нижний слой асфальта',
    startDate: '2026-09-28',
    endDate: '2026-09-30',
    createdAt: CREATED_AT,
    requiresTechnique: [requirement(3, 1)],
    actual: {
      startDate: '2026-09-27',
      endDate: '2026-09-27',
      status: 'ahead',
      deviationDays: 1,
      techniqueDeviationCount: 1,
      message: {
        code: 'ahead',
        severity: 'info',
        text: 'Отклонение по технике'
      }
    }
  },
  {
    id: 6,
    parentId: 4,
    workTypeId: 106,
    workTypeName: 'Верхний слой асфальта',
    startDate: '2026-10-01',
    endDate: '2026-10-04',
    createdAt: CREATED_AT,
    requiresTechnique: [requirement(3, 1), requirement(4, 1)],
    actual: null
  },
  {
    id: 7,
    parentId: 0,
    workTypeId: 107,
    workTypeName: 'Нанесение разметки',
    startDate: '2026-10-05',
    endDate: '2026-10-06',
    createdAt: CREATED_AT,
    requiresTechnique: [],
    actual: null
  }
]
