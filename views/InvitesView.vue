<script setup>
import { onMounted, reactive, ref } from 'vue'
import { createInvite, getInvites, revokeInvite } from '@/services/api'

const invites = ref([])
const loading = ref(true)
const creating = ref(false)
const copied = ref(false)
const error = ref('')
const issued = ref(null)
const form = reactive({ label: '', expires_in_hours: 72 })

function statusLabel(status) {
  return { active: 'Действует', used: 'Использовано', expired: 'Истекло' }[status] || status
}

function formatDate(value) {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

async function load() {
  loading.value = true
  try {
    invites.value = await getInvites()
    error.value = ''
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function issue() {
  creating.value = true
  error.value = ''
  issued.value = null
  try {
    issued.value = await createInvite({ ...form, label: form.label.trim() })
    form.label = ''
    copied.value = false
    await load()
  } catch (err) {
    error.value = err.message
  } finally {
    creating.value = false
  }
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(issued.value.code)
    copied.value = true
  } catch {
    error.value = 'Не удалось скопировать автоматически. Выдели код и скопируй его вручную.'
  }
}

async function revoke(invite) {
  if (!window.confirm('Отозвать это приглашение?')) return
  try {
    await revokeInvite(invite.id)
    await load()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(load)
</script>

<template>
  <main class="page-wrap">
    <section class="page-heading"><div><p class="eyebrow"><span class="eyebrow-dot"></span> УПРАВЛЕНИЕ ДОСТУПОМ</p><h1>Участники<span class="period">.</span></h1><p class="page-subtitle">Создавай одноразовые приглашения для своей группы.</p></div></section>
    <p v-if="error" class="notice notice-error">{{ error }}</p>

    <section class="invite-create-card">
      <div class="invite-create-copy"><span class="invite-create-icon">＋</span><div><h2>Новое приглашение</h2><p>Код можно использовать один раз. Срок действия — до 30 дней.</p></div></div>
      <form class="invite-form" @submit.prevent="issue"><label>Для кого <span>по желанию</span><input v-model="form.label" maxlength="100" placeholder="Например, Алина" /></label><label>Действует<select v-model.number="form.expires_in_hours"><option :value="24">1 день</option><option :value="72">3 дня</option><option :value="168">7 дней</option><option :value="720">30 дней</option></select></label><button class="button button-primary" :disabled="creating">{{ creating ? 'Создаём…' : 'Создать код' }}</button></form>
      <div v-if="issued" class="issued-code"><div><span class="tiny-label">ПРИГЛАШЕНИЕ СОЗДАНО · ИСТЕКАЕТ {{ formatDate(issued.expires_at) }}</span><code>{{ issued.code }}</code><small>Код показывается только сейчас. Скопируй и отправь его участнику.</small></div><button class="button button-outline" @click="copyCode">{{ copied ? 'Скопировано ✓' : 'Скопировать' }}</button></div>
    </section>

    <section class="invite-list-section"><header class="section-toolbar"><div class="section-title"><h2>История приглашений</h2><span>{{ invites.length }}</span></div><button class="text-button" @click="load">Обновить список ↻</button></header>
      <div v-if="loading" class="loading-state"><span class="spinner"></span> Загружаем…</div>
      <div v-else-if="!invites.length" class="empty-state compact-empty"><span class="empty-mark">✳</span><h2>Пока приглашений нет</h2><p>Создай первый код, чтобы пригласить участника.</p></div>
      <div v-else class="invite-table-wrap"><table class="invite-table"><thead><tr><th>Для кого</th><th>Создано</th><th>Истекает</th><th>Статус</th><th></th></tr></thead><tbody><tr v-for="invite in invites" :key="invite.id"><td><strong>{{ invite.label || 'Без пометки' }}</strong><small v-if="invite.used_by">Аккаунт: {{ invite.used_by }}</small></td><td>{{ formatDate(invite.created_at) }}</td><td>{{ formatDate(invite.expires_at) }}</td><td><span class="status-pill" :class="`status-${invite.status}`">{{ statusLabel(invite.status) }}</span></td><td><button v-if="invite.status === 'active'" class="table-action" @click="revoke(invite)">Отозвать</button></td></tr></tbody></table></div>
    </section>
  </main>
</template>
