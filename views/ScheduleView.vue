<script setup>
import { computed, onMounted, ref } from 'vue'
import { getSchedule } from '@/services/api'

const schedule = ref([])
const loading = ref(true)
const error = ref('')
const weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']

const days = computed(() => weekdays.map((name, weekday) => ({
  name,
  lessons: schedule.value
    .filter((item) => item.weekday === weekday)
    .sort((a, b) => (a.lesson_number ?? 99) - (b.lesson_number ?? 99)),
})))

async function load() {
  loading.value = true
  error.value = ''
  try {
    schedule.value = await getSchedule()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="page-wrap">
    <section class="page-heading"><div><p class="eyebrow"><span class="eyebrow-dot"></span> ПЛАН НА НЕДЕЛЮ</p><h1>Расписание<span class="period">.</span></h1><p class="page-subtitle">Пары и предметы на каждый учебный день.</p></div></section>
    <p v-if="error" class="notice notice-error">{{ error }}</p>
    <div v-if="loading" class="loading-state"><span class="spinner"></span> Загружаем расписание…</div>
    <section v-else class="schedule-grid">
      <article v-for="day in days" :key="day.name" class="day-card" :class="{ 'day-card-empty': !day.lessons.length }">
        <header class="day-card-heading"><h2>{{ day.name }}</h2><span>{{ day.lessons.length ? `${day.lessons.length} ${day.lessons.length === 1 ? 'пара' : 'пары'}` : 'нет занятий' }}</span></header>
        <div v-if="day.lessons.length" class="lesson-list"><div v-for="lesson in day.lessons" :key="lesson.id" class="lesson-row"><span class="lesson-index">{{ lesson.lesson_number ? String(lesson.lesson_number).padStart(2, '0') : '↗' }}</span><div class="lesson-info"><strong>{{ lesson.subject_detail.name }}</strong><small>{{ lesson.is_online ? 'Онлайн-занятие' : lesson.room || 'Аудитория не указана' }}</small></div><span v-if="lesson.is_online" class="online-indicator" title="Онлайн"></span></div></div>
        <p v-else class="empty-day-note">Свободное время —<br />тоже часть плана.</p>
      </article>
    </section>
  </main>
</template>
