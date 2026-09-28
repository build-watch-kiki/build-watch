import App from './App.vue'
import { createApp } from 'vue'
import { registerPlugins } from '@/plugins'
import './style.css'

const app = createApp(App)
registerPlugins(app)
app.mount('#app')
