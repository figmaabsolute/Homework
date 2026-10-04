import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { clearSession } from './stores/auth'

window.addEventListener('auth:expired', () => {
  clearSession()
  if (router.currentRoute.value.name !== 'login') {
    router.replace({ name: 'login', query: { expired: '1' } })
  }
})

createApp(App).use(router).mount('#app')
