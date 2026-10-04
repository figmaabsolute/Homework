<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authState, signOut } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const displayName = computed(() => authState.user?.full_name || authState.user?.username || 'Участник')
const initials = computed(() => displayName.value.trim().slice(0, 1).toLocaleUpperCase('ru'))

async function logout() {
  await signOut()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="app-frame">
    <header class="topbar">
      <RouterLink class="brand brand-compact" :to="{ name: 'homework' }">
        <span class="brand-symbol">к</span><span>классный круг</span>
      </RouterLink>

      <nav class="main-nav" aria-label="Главная навигация">
        <RouterLink :class="{ 'router-link-active': route.name === 'homework-detail' }" :to="{ name: 'homework' }">Задания</RouterLink>
        <RouterLink :to="{ name: 'schedule' }">Расписание</RouterLink>
        <RouterLink v-if="authState.user?.is_staff" :to="{ name: 'subjects' }">Предметы</RouterLink>
        <RouterLink v-if="authState.user?.is_staff" :to="{ name: 'invites' }">Участники</RouterLink>
      </nav>

      <div class="account-menu">
        <RouterLink class="user-link" :to="{ name: 'profile' }">
          <span class="avatar">{{ initials }}</span>
          <span class="user-meta"><strong>{{ displayName }}</strong><small>{{ authState.user?.is_staff ? 'Администратор' : 'Участник группы' }}</small></span>
        </RouterLink>
        <button class="logout-button" type="button" @click="logout">Выйти <span aria-hidden="true">↗</span></button>
      </div>
    </header>

    <RouterView v-slot="{ Component }">
      <Transition name="view" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>

    <footer class="app-footer"><span>Закрытое пространство нашей группы</span><span>сделано с заботой <b>✳</b></span></footer>
  </div>
</template>
