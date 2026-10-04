<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthPageLayout from '@/layouts/AuthPageLayout.vue'
import { signIn } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await signIn({ username: username.value.trim(), password: password.value })
    const next = route.query.next
    const safeNext = typeof next === 'string' && next.startsWith('/') && !next.startsWith('//')
      ? next
      : { name: 'homework' }
    await router.replace(safeNext)
  } catch (err) {
    error.value = err.message.includes('No active account') ? 'Неверный логин или пароль.' : err.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AuthPageLayout eyebrow="СНОВА РАДЫ ТЕБЯ ВИДЕТЬ" title="Войти в кабинет" subtitle="Введи данные аккаунта, чтобы открыть задания и расписание.">
    <p v-if="route.query.expired" class="notice notice-warm">Сеанс завершился. Войди ещё раз.</p>
    <p v-if="route.query.registered" class="notice notice-warm">Аккаунт создан. Теперь можно войти.</p>
    <form class="auth-form" @submit.prevent="submit">
      <label for="login-username">Логин</label>
      <input id="login-username" v-model="username" autocomplete="username" required placeholder="Твой логин" />
      <div class="label-row"><label for="login-password">Пароль</label><span>Только для участников</span></div>
      <input id="login-password" v-model="password" type="password" autocomplete="current-password" required placeholder="Твой пароль" />
      <p v-if="error" class="notice notice-error" role="alert">{{ error }}</p>
      <button class="button button-primary button-wide" :disabled="busy">{{ busy ? 'Входим…' : 'Войти' }} <span>↗</span></button>
    </form>
    <template #footer>
      <p class="auth-switch">Есть приглашение? <RouterLink :to="{ name: 'register' }">Создать аккаунт</RouterLink></p>
    </template>
  </AuthPageLayout>
</template>
