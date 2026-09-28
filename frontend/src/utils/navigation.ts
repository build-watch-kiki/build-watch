import { ref } from 'vue'

/** True while a route navigation (including lazy-chunk loading) is pending. */
export const isNavigating = ref(false)

/** Last failed navigation target for retry. Null when no error. */
export const failedTarget = ref<string | null>(null)

export const navigationError = ref<string | null>(null)

export function dismissNavigationError() {
  navigationError.value = null
  failedTarget.value = null
}
