import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          background: '#F4F7FB',
          surface: '#FFFFFF',
          'on-background': '#182536',
          'on-surface': '#182536',
          primary: '#2563EB',
          secondary: '#142033',
          accent: '#0F766E',
          error: '#B42318',
          info: '#2563EB',
          success: '#16704A',
          warning: '#9A5B06'
        }
      }
    }
  },
  defaults: {
    VBtn: {
      rounded: 'lg',
      elevation: 0,
      style: 'text-transform: none; letter-spacing: 0; font-weight: 600;'
    },
    VCard: { rounded: 'xl', elevation: 0 },
    VTextField: { color: 'primary' },
    VSelect: { color: 'primary' },
    VAutocomplete: { color: 'primary' },
    VAlert: { rounded: 'lg' }
  },
  icons: {
    defaultSet: 'mdi'
  }
})
