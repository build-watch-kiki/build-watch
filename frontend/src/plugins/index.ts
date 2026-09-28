import vuetify from '@/plugins/vuetify'
import pinia from '@/store'
import router from '@/router'

import type { App } from 'vue'

export function registerPlugins(app: App) {
  app.use(pinia).use(vuetify).use(router)
}
