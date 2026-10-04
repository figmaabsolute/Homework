<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthPageLayout from '@/layouts/AuthPageLayout.vue'
import { signIn, signUp } from '@/stores/auth'

const router = useRouter()
const form = reactive({
  invite_code: '',
  username: '',
  first_name: '',
  last_name: '',
  password: '',
  password_confirm: '',
})
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await signUp({ ...form, username: form.username.trim(), invite_code: form.invite_code.trim() })
    try {
      await signIn({ username: form.username.trim(), password: form.password })
      await router.replace({ name: 'homework' })
    } catch {
      await router.replace({ name: 'login', query: { registered: '1' } })
    }
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AuthPageLayout eyebrow="ТОЛЬКО ПО ПРИГЛАШЕНИЮ" title="Присоединиться" subtitle="Попроси администратора группы создать одноразовый код и введи его здесь.">
    <form class="auth-form register-form" @submit.prevent="submit">
      <label for="invite-code">Код приглашения</label>
      <input id="invite-code" v-model="form.invite_code" autocomplete="off" required placeholder="Вставь свой код" />
      <div class="form-grid-two">
        <label>Имя<input v-model="form.first_name" autocomplete="given-name" placeholder="Имя" /></label>
        <label>Фамилия<input v-model="form.last_name" autocomplete="family-name" placeholder="Фамилия" /></label>
      </div>
      <label for="register-username">Логин</label>
      <input id="register-username" v-model="form.username" autocomplete="username" required maxlength="150" placeholder="Придумай логин" />
      <div class="form-grid-two">
        <label>Пароль<input v-model="form.password" type="password" autocomplete="new-password" required minlength="8" placeholder="Минимум 8 символов" /></label>
        <label>Повтори пароль<input v-model="form.password_confirm" type="password" autocomplete="new-password" required minlength="8" placeholder="Ещё раз" /></label>
      </div>
      <p v-if="error" class="notice notice-error" role="alert">{{ error }}</p>
      <button class="button button-primary button-wide" :disabled="busy">{{ busy ? 'Создаём аккаунт…' : 'Создать аккаунт' }} <span>↗</span></button>
    </form>
    <template #footer>
      <p class="auth-switch">Уже есть аккаунт? <RouterLink :to="{ name: 'login' }">Войти</RouterLink></p>
    </template>
  </AuthPageLayout>
</template>
