import type { Stage } from '@/types/plan'

export const GANTT_CELL_WIDTH = 32
export const GANTT_ROW_HEIGHT = 36

export function isRootParent(parentId: unknown): boolean {
  return parentId === null || parentId === undefined || parentId === 0
}

export function isRootStage(stage: Stage): boolean {
  return isRootParent(stage.parentId)
}

export function parseDate(
  value: string | Date | null | undefined
): Date | null {
  if (!value) return null
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : new Date(value)
  }
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

export function getPlanBounds(stages: Stage[]): { start: Date; end: Date } {
  if (!stages.length) {
    const now = new Date()
    const start = new Date(now)
    start.setHours(0, 0, 0, 0)
    const end = new Date(start)
    end.setDate(end.getDate() + 30)
    end.setHours(23, 59, 59, 999)
    return { start, end }
  }

  let min: Date | null = null
  let max: Date | null = null

  for (const stage of stages) {
    const s = parseDate(stage.startDate)
    const e = parseDate(stage.endDate)
    if (s && (!min || s < min)) min = s
    if (e && (!max || e > max)) max = e
  }

  const start = min ? new Date(min) : new Date()
  start.setHours(0, 0, 0, 0)
  const end = max ? new Date(max) : new Date(start)
  end.setHours(23, 59, 59, 999)

  if (max) {
    const day = max.getDate()

    if (day < 15) {
      end.setDate(15)
    } else {
      end.setMonth(end.getMonth() + 1, 0)
    }

    end.setHours(23, 59, 59, 999)
  }

  const minEnd = new Date(start)
  minEnd.setDate(minEnd.getDate() + 30)
  minEnd.setHours(23, 59, 59, 999)

  if (end < minEnd) {
    end.setTime(minEnd.getTime())
  }

  return { start, end }
}

export function generateDays(bounds: { start: Date; end: Date }): Date[] {
  const days: Date[] = []
  const cur = new Date(bounds.start)
  cur.setHours(0, 0, 0, 0)
  const end = new Date(bounds.end)
  end.setHours(0, 0, 0, 0)
  while (cur <= end) {
    days.push(new Date(cur))
    cur.setDate(cur.getDate() + 1)
  }
  return days
}

export interface MonthSpan {
  label: string
  span: number
  key: string
}

function formatMonthYear(date: Date): string {
  const raw = new Intl.DateTimeFormat('ru-RU', {
    month: 'long',
    year: 'numeric'
  }).format(date)
  return raw.charAt(0).toUpperCase() + raw.slice(1)
}

export function generateMonths(days: Date[]): MonthSpan[] {
  const result: MonthSpan[] = []
  let currentKey = ''
  let current: MonthSpan | null = null

  for (const day of days) {
    const key = `${day.getFullYear()}-${day.getMonth()}`
    if (key !== currentKey) {
      currentKey = key
      current = {
        label: formatMonthYear(day),
        span: 0,
        key
      }
      result.push(current)
    }
    if (current) current.span += 1
  }

  return result
}

export function diffDays(a: Date, b: Date): number {
  const aa = new Date(a)
  const bb = new Date(b)
  aa.setHours(0, 0, 0, 0)
  bb.setHours(0, 0, 0, 0)
  return Math.round((bb.getTime() - aa.getTime()) / (1000 * 60 * 60 * 24))
}

export function getDayIndex(date: Date, start: Date): number {
  return diffDays(start, date)
}

export function getBarStyle(
  stage: Stage,
  start: Date,
  cellWidth = GANTT_CELL_WIDTH
): { left: string; width: string } {
  return getPeriodBarStyle(stage.startDate, stage.endDate, start, cellWidth)
}

export function getPeriodBarStyle(
  startDate: string,
  endDate: string,
  start: Date,
  cellWidth = GANTT_CELL_WIDTH
): { left: string; width: string } {
  const s = parseDate(startDate)
  const e = parseDate(endDate)
  if (!s || !e) return { left: '0px', width: `${cellWidth}px` }
  s.setHours(0, 0, 0, 0)
  e.setHours(0, 0, 0, 0)
  const leftDays = Math.max(0, diffDays(start, s))
  const duration = Math.max(1, diffDays(s, e) + 1)
  return {
    left: `${leftDays * cellWidth}px`,
    width: `${duration * cellWidth}px`
  }
}

export function getTodayIndex(start: Date, days: Date[]): number | null {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const idx = diffDays(start, today)
  if (idx < 0 || idx >= days.length) return null
  return idx
}

export function getTotalTechnique(stage: Stage): number {
  if (!stage.requiresTechnique || !Array.isArray(stage.requiresTechnique))
    return 0
  return stage.requiresTechnique.reduce((sum, r) => sum + (r.quantity ?? 0), 0)
}

export function hasChildren(stages: Stage[], id: number): boolean {
  return stages.some((s) => s.parentId === id)
}

export function getChildren(stages: Stage[], parentId: number | null): Stage[] {
  if (isRootParent(parentId)) {
    return stages.filter((s) => isRootParent(s.parentId))
  }
  return stages.filter((s) => s.parentId === parentId)
}

export function getDepth(stage: Stage, stages: Stage[]): number {
  let depth = 0
  let cur: Stage | undefined = stage
  const visited = new Set<number>()
  while (cur && !isRootParent(cur.parentId)) {
    if (visited.has(cur.id)) break
    visited.add(cur.id)
    const parent = stages.find((s) => s.id === cur!.parentId)
    if (!parent) break
    depth += 1
    cur = parent
  }
  return depth
}

export function flattenVisible(
  stages: Stage[],
  expanded: Set<number>
): Stage[] {
  const result: Stage[] = []

  function walk(parentId: number | null) {
    const children = getChildren(stages, parentId)
    for (const child of children) {
      result.push(child)
      if (expanded.has(child.id) && hasChildren(stages, child.id)) {
        walk(child.id)
      }
    }
  }

  walk(null)
  return result
}

export function getInitialExpanded(stages: Stage[]): Set<number> {
  const roots = stages.filter((s) => isRootParent(s.parentId))
  const next = new Set<number>()
  for (const r of roots) {
    if (hasChildren(stages, r.id)) next.add(r.id)
  }
  return next
}

export function findStageById(stages: Stage[], id: number): Stage | undefined {
  return stages.find((s) => s.id === id)
}
