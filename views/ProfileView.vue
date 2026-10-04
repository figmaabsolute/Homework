<script setup>
import { computed } from 'vue'
import { authState } from '@/stores/auth'

const user = computed(() => authState.user)
const initial = computed(() => (user.value?.full_name || user.value?.username || 'У').slice(0, 1).toLocaleUpperCase('ru'))
</script>

<template>
  <main class="page-wrap profile-page">
    <section class="page-heading"><div><p class="eyebrow"><span class="eyebrow-dot"></span> ЛИЧНЫЙ КАБИНЕТ</p><h1>Мой профиль<span class="period">.</span></h1><p class="page-subtitle">Информация об аккаунте в группе.</p></div></section>
    <section class="profile-card">
      <div class="profile-avatar">{{ initial }}</div>
      <div class="profile-primary"><span class="subject-tag">{{ user?.is_staff ? 'Администратор' : 'Участник группы' }}</span><h2>{{ user?.full_name || user?.username }}</h2><p>@{{ user?.username }}</p></div>
      <div class="profile-details"><div><span>Логин</span><strong>{{ user?.username }}</strong></div><div><span>Имя</span><strong>{{ user?.full_name || 'Не указано' }}</strong></div><div><span>Роль</span><strong>{{ user?.is_staff ? 'Администратор группы' : 'Участник' }}</strong></div></div>
      <p class="profile-security">Вход сохраняется в защищённом браузерном сеансе до 30 дней. Токен доступа обновляется автоматически; кнопка «Выйти» отзывает сеанс.</p>
    </section>
  </main>
</template>
