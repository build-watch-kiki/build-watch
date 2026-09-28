import type { PhotoResponse } from '@/types/photos.ts'
import { mockTechniqueById } from './techniques.ts'

export const MOCK_PHOTO_WIDTH = 1600
export const MOCK_PHOTO_HEIGHT = 1000

/** Схематичная площадка как inline-SVG: работает офлайн, оттенок свой у каждого фото. */
export function svgPhotoUrl(hue: number, label: string): string {
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${MOCK_PHOTO_WIDTH}" height="${MOCK_PHOTO_HEIGHT}" viewBox="0 0 ${MOCK_PHOTO_WIDTH} ${MOCK_PHOTO_HEIGHT}">` +
    `<rect width="${MOCK_PHOTO_WIDTH}" height="${MOCK_PHOTO_HEIGHT}" fill="hsl(${hue}, 18%, 88%)"/>` +
    `<rect y="620" width="${MOCK_PHOTO_WIDTH}" height="380" fill="hsl(${hue}, 12%, 72%)"/>` +
    `<polygon points="0,1000 620,620 980,620 1600,1000" fill="hsl(${hue}, 8%, 45%)"/>` +
    `<polygon points="700,620 900,620 1500,1000 100,1000" fill="hsl(${hue}, 6%, 32%)"/>` +
    `<line x1="800" y1="620" x2="800" y2="1000" stroke="hsl(48, 90%, 60%)" stroke-width="10" stroke-dasharray="40 30"/>` +
    `<rect x="120" y="180" width="220" height="150" rx="8" fill="hsl(${hue}, 25%, 55%)"/>` +
    `<rect x="380" y="240" width="160" height="110" rx="8" fill="hsl(${(hue + 40) % 360}, 25%, 60%)"/>` +
    `<rect x="1180" y="200" width="240" height="170" rx="8" fill="hsl(${(hue + 80) % 360}, 22%, 58%)"/>` +
    `<circle cx="1330" cy="120" r="46" fill="hsl(48, 85%, 68%)"/>` +
    `<text x="80" y="80" font-family="sans-serif" font-size="44" font-weight="bold" fill="hsl(${hue}, 20%, 30%)">${label}</text>` +
    `</svg>`
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

interface MockBox {
  techniqueId: number
  confidence: number
  xCenterNorm: number
  yCenterNorm: number
  wNorm: number
  hNorm: number
}

let mockObjectId = 1

function mockDetections(boxes: MockBox[]): PhotoResponse['detections'] {
  return boxes.map((box) => {
    const technique = mockTechniqueById(box.techniqueId)
    return {
      objectId: mockObjectId++,
      classId: technique.id,
      className: technique.nameRu,
      technique: {
        id: technique.id,
        name: technique.name,
        nameRu: technique.nameRu,
        color: technique.color
      },
      color: technique.color,
      confidence: { detection: box.confidence },
      bbox: {
        format: 'xywh_center',
        xCenterNorm: box.xCenterNorm,
        yCenterNorm: box.yCenterNorm,
        wNorm: box.wNorm,
        hNorm: box.hNorm
      }
    }
  })
}

interface MockPhotoRow {
  id: number
  capturedAt: string
  hue: number
  boxes: MockBox[]
}

const MOCK_MODEL = { name: 'mock-road', version: '1.0', weights: 'mock' }

/** Снимки только 20–27.09: по одному на день, детекции генерируются под каждое фото. */
const ROWS: MockPhotoRow[] = [
  {
    id: 101,
    capturedAt: '2026-09-20T09:15:00+03:00',
    hue: 210,
    boxes: [
      {
        techniqueId: 1,
        confidence: 0.9,
        xCenterNorm: 0.28,
        yCenterNorm: 0.64,
        wNorm: 0.24,
        hNorm: 0.3
      },
      {
        techniqueId: 2,
        confidence: 0.82,
        xCenterNorm: 0.66,
        yCenterNorm: 0.68,
        wNorm: 0.26,
        hNorm: 0.26
      }
    ]
  },
  {
    id: 102,
    capturedAt: '2026-09-21T11:40:00+03:00',
    hue: 150,
    boxes: [
      {
        techniqueId: 1,
        confidence: 0.94,
        xCenterNorm: 0.36,
        yCenterNorm: 0.6,
        wNorm: 0.2,
        hNorm: 0.32
      },
      {
        techniqueId: 3,
        confidence: 0.79,
        xCenterNorm: 0.64,
        yCenterNorm: 0.7,
        wNorm: 0.18,
        hNorm: 0.22
      },
      {
        techniqueId: 2,
        confidence: 0.85,
        xCenterNorm: 0.14,
        yCenterNorm: 0.66,
        wNorm: 0.2,
        hNorm: 0.26
      }
    ]
  },
  {
    id: 103,
    capturedAt: '2026-09-22T10:05:00+03:00',
    hue: 30,
    boxes: [
      {
        techniqueId: 4,
        confidence: 0.88,
        xCenterNorm: 0.48,
        yCenterNorm: 0.64,
        wNorm: 0.3,
        hNorm: 0.26
      },
      {
        techniqueId: 1,
        confidence: 0.77,
        xCenterNorm: 0.8,
        yCenterNorm: 0.6,
        wNorm: 0.2,
        hNorm: 0.3
      }
    ]
  },
  {
    id: 104,
    capturedAt: '2026-09-23T10:20:00+03:00',
    hue: 90,
    boxes: [
      {
        techniqueId: 1,
        confidence: 0.93,
        xCenterNorm: 0.3,
        yCenterNorm: 0.62,
        wNorm: 0.22,
        hNorm: 0.3
      },
      {
        techniqueId: 2,
        confidence: 0.87,
        xCenterNorm: 0.68,
        yCenterNorm: 0.66,
        wNorm: 0.26,
        hNorm: 0.28
      }
    ]
  },
  {
    id: 105,
    capturedAt: '2026-09-24T09:10:00+03:00',
    hue: 270,
    boxes: [
      {
        techniqueId: 2,
        confidence: 0.91,
        xCenterNorm: 0.32,
        yCenterNorm: 0.66,
        wNorm: 0.24,
        hNorm: 0.28
      },
      {
        techniqueId: 2,
        confidence: 0.74,
        xCenterNorm: 0.6,
        yCenterNorm: 0.68,
        wNorm: 0.2,
        hNorm: 0.24
      },
      {
        techniqueId: 3,
        confidence: 0.83,
        xCenterNorm: 0.82,
        yCenterNorm: 0.7,
        wNorm: 0.16,
        hNorm: 0.2
      }
    ]
  },
  {
    id: 106,
    capturedAt: '2026-09-25T12:15:00+03:00',
    hue: 180,
    boxes: [
      {
        techniqueId: 1,
        confidence: 0.95,
        xCenterNorm: 0.25,
        yCenterNorm: 0.6,
        wNorm: 0.22,
        hNorm: 0.3
      },
      {
        techniqueId: 5,
        confidence: 0.89,
        xCenterNorm: 0.58,
        yCenterNorm: 0.58,
        wNorm: 0.2,
        hNorm: 0.34
      }
    ]
  },
  {
    id: 107,
    capturedAt: '2026-09-26T14:00:00+03:00',
    hue: 330,
    boxes: [
      {
        techniqueId: 5,
        confidence: 0.92,
        xCenterNorm: 0.4,
        yCenterNorm: 0.58,
        wNorm: 0.2,
        hNorm: 0.34
      },
      {
        techniqueId: 4,
        confidence: 0.86,
        xCenterNorm: 0.68,
        yCenterNorm: 0.64,
        wNorm: 0.26,
        hNorm: 0.26
      }
    ]
  },
  {
    id: 108,
    capturedAt: '2026-09-27T09:45:00+03:00',
    hue: 120,
    boxes: [
      {
        techniqueId: 3,
        confidence: 0.88,
        xCenterNorm: 0.3,
        yCenterNorm: 0.68,
        wNorm: 0.2,
        hNorm: 0.24
      },
      {
        techniqueId: 2,
        confidence: 0.81,
        xCenterNorm: 0.56,
        yCenterNorm: 0.66,
        wNorm: 0.22,
        hNorm: 0.26
      },
      {
        techniqueId: 1,
        confidence: 0.97,
        xCenterNorm: 0.78,
        yCenterNorm: 0.6,
        wNorm: 0.2,
        hNorm: 0.3
      }
    ]
  }
]

export const MOCK_PHOTOS: PhotoResponse[] = ROWS.map((row, index) => ({
  id: row.id,
  name: `mock-road-${String(index + 1).padStart(2, '0')}.svg`,
  url: svgPhotoUrl(row.hue, `Участок ${index + 1}`),
  capturedAt: row.capturedAt,
  createdAt: row.capturedAt,
  isProcessed: true,
  processingStatus: 'succeeded',
  width: MOCK_PHOTO_WIDTH,
  height: MOCK_PHOTO_HEIGHT,
  format: 'image/svg+xml',
  model: { ...MOCK_MODEL },
  detections: mockDetections(row.boxes)
}))
