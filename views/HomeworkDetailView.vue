<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { downloadFile, getFileBlob, getHomework } from '@/services/api'

const route = useRoute()
const homework = ref(null)
const loading = ref(true)
const error = ref('')
const previewOpen = ref(false)
const previewLoading = ref(false)
const previewError = ref('')
const previewUrl = ref('')
const previewTitle = ref('')
let previewRequestId = 0

async function load() {
  loading.value = true
  error.value = ''
  try {
    homework.value = await getHomework(route.params.id)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(`${value}T00:00:00`))
}

async function download(file) {
  try {
    await downloadFile(file.download_url, file.file_name || `материал-${file.id}`)
  } catch (err) {
    error.value = err.message
  }
}

function imageMimeType(fileName) {
  const extension = fileName.split('.').pop()?.toLowerCase()
  return ({ jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', gif: 'image/gif', webp: 'image/webp' })[extension] || ''
}

async function openAttachment(file) {
  const mimeType = imageMimeType(file.file_name)
  if (file.file_type !== 'photo' || !mimeType) return download(file)

  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  previewTitle.value = file.file_name
  previewError.value = ''
  previewOpen.value = true
  previewLoading.value = true
  const requestId = ++previewRequestId
  try {
    const blob = await getFileBlob(file.download_url)
    if (requestId !== previewRequestId) return
    previewUrl.value = URL.createObjectURL(new Blob([blob], { type: mimeType }))
  } catch (err) {
    if (requestId === previewRequestId) previewError.value = err.message
  } finally {
    if (requestId === previewRequestId) previewLoading.value = false
  }
}

function closePreview() {
  previewRequestId += 1
  previewOpen.value = false
  previewLoading.value = false
  previewError.value = ''
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

onMounted(load)
watch(() => route.params.id, load)
onBeforeUnmount(closePreview)
</script>

<template>
  <main class="page-wrap detail-page">
    <RouterLink class="back-link" :to="{ name: 'homework' }">← Все задания</RouterLink>
    <p v-if="error" class="notice notice-error">{{ error }}</p>
    <div v-if="loading" class="loading-state"><span class="spinner"></span> Загружаем задание…</div>
    <article v-else-if="homework" class="detail-card">
      <div class="detail-topline"><span class="subject-tag">{{ homework.subject_detail.name }}</span><time>{{ formatDate(homework.date) }}</time></div>
      <h1>{{ homework.title }}</h1>
      <p v-if="homework.description" class="detail-description">{{ homework.description }}</p>
      <section v-if="homework.tasks.length" class="detail-section"><h2>Что нужно сделать</h2><ol class="detail-tasks"><li v-for="task in homework.tasks" :key="task.id">{{ task.text }}</li></ol></section>
      <section v-if="homework.files.length" class="detail-section"><h2>Материалы</h2><div class="detail-files"><button v-for="file in homework.files" :key="file.id" class="file-chip" @click="openAttachment(file)"><span>{{ file.file_type === 'photo' ? '▧' : '↧' }}</span>{{ file.file_name }}</button></div></section>
      <p class="detail-updated">Обновлено {{ formatDate(homework.updated_at.slice(0, 10)) }}</p>
    </article>
    <div v-if="previewOpen" class="image-preview-backdrop" role="dialog" aria-modal="true" aria-label="Просмотр изображения" tabindex="-1" @click.self="closePreview" @keydown.esc="closePreview">
      <section class="image-preview-card">
        <header><strong>{{ previewTitle }}</strong><button class="close-button" type="button" aria-label="Закрыть просмотр" @click="closePreview">×</button></header>
        <div v-if="previewLoading" class="loading-state"><span class="spinner"></span> Загружаем фото…</div>
        <p v-else-if="previewError" class="notice notice-error" role="alert">{{ previewError }}</p>
        <img v-else-if="previewUrl" :src="previewUrl" :alt="previewTitle" @error="previewError = 'Не удалось показать это изображение.'" />
      </section>
    </div>
  </main>
</template>
