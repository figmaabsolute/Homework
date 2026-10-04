<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { createHomework, createSubject, deleteHomework, downloadFile, getFileBlob, getHomeworks, getSubjects, updateHomework, uploadHomeworkFiles } from '@/services/api'
import { authState } from '@/stores/auth'

// Keep the last list in memory while navigating between pages. The fresh API
// response still replaces it in the background, so this never becomes a disk cache.
const homeworkCache = new Map()
const homeworks = ref([])
const subjects = ref([])
const loading = ref(true)
const saving = ref(false)
const subjectsLoading = ref(false)
const creatingSubject = ref(false)
const uploadingFiles = ref(false)
const draggingFiles = ref(false)
const error = ref('')
const subjectError = ref('')
const fileError = ref('')
const search = ref('')
const subjectFilter = ref('all')
const sortMode = ref('deadline')
const editorOpen = ref(false)
const editingId = ref(null)
const newSubjectName = ref('')
const selectedFiles = ref([])
const filePreviews = ref([])
const fileInput = ref(null)
const imagePreviewOpen = ref(false)
const imagePreviewLoading = ref(false)
const imagePreviewError = ref('')
const imagePreviewTitle = ref('')
const imagePreviewUrl = ref('')
const refreshing = ref(false)
const form = reactive({ subject: '', title: '', date: '', description: '', tasks: [''] })
let homeworkRequestId = 0
let hasLoadedHomeworks = false
let imagePreviewRequestId = 0

const isStaff = computed(() => Boolean(authState.user?.is_staff))
const today = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10)
const upcomingCount = computed(() => homeworks.value.filter((item) => item.date >= today()).length)
const currentHomeworkFiles = computed(() => homeworks.value.find((item) => String(item.id) === String(editingId.value))?.files || [])
const filteredHomeworks = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('ru')
  return [...homeworks.value]
    .filter((item) => subjectFilter.value === 'all' || String(item.subject) === subjectFilter.value)
    .filter((item) => {
      const haystack = `${item.title} ${item.description} ${item.subject_detail?.name || ''}`.toLocaleLowerCase('ru')
      return !query || haystack.includes(query)
    })
    .sort((a, b) => {
      if (sortMode.value === 'newest') return (Date.parse(b.created_at || '') || 0) - (Date.parse(a.created_at || '') || 0)
      if (sortMode.value === 'oldest') return (Date.parse(a.created_at || '') || 0) - (Date.parse(b.created_at || '') || 0)
      return a.date.localeCompare(b.date) || a.title.localeCompare(b.title, 'ru')
    })
})

function dateLabel(value) {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' }).format(new Date(`${value}T00:00:00`))
}

function deadlineLabel(value) {
  const date = new Date(`${value}T00:00:00`)
  const base = new Date(`${today()}T00:00:00`)
  const days = Math.round((date - base) / 86400000)
  if (days < 0) return 'Срок прошёл'
  if (days === 0) return 'Сегодня'
  if (days === 1) return 'Завтра'
  return `Через ${days} дн.`
}

async function loadData() {
  const requestId = ++homeworkRequestId
  const cacheKey = authState.user?.username || 'current-user'
  const cachedRows = homeworkCache.get(cacheKey)
  const initialLoad = !hasLoadedHomeworks
  if (initialLoad && cachedRows) {
    homeworks.value = cachedRows
    hasLoadedHomeworks = true
    loading.value = false
  } else if (initialLoad) loading.value = true
  if (!initialLoad || cachedRows) refreshing.value = true
  error.value = ''
  void refreshSubjects()
  try {
    const homeworkRows = normalizeHomeworks(await getHomeworks())
    if (requestId === homeworkRequestId) {
      homeworks.value = homeworkRows
      homeworkCache.set(cacheKey, homeworkRows)
      hasLoadedHomeworks = true
    }
  } catch (err) {
    if (requestId === homeworkRequestId) error.value = err.message
  } finally {
    if (requestId === homeworkRequestId) {
      loading.value = false
      refreshing.value = false
    }
  }
}

function normalizeHomeworks(payload) {
  const rows = Array.isArray(payload)
    ? payload
    : Array.isArray(payload?.results)
      ? payload.results
      : Array.isArray(payload?.items)
        ? payload.items
        : null
  if (!rows) throw new Error('Сервер вернул список заданий в неожиданном формате. Обнови страницу или проверь API.')
  return rows.map(normalizeHomework)
}

function normalizeHomework(item) {
  return {
    ...item,
    tasks: Array.isArray(item.tasks) ? item.tasks : [],
    files: Array.isArray(item.files) ? item.files : [],
  }
}

function upsertHomework(item) {
  const normalized = normalizeHomework(item)
  const index = homeworks.value.findIndex((row) => String(row.id) === String(normalized.id))
  const rows = [...homeworks.value]
  if (index === -1) rows.unshift(normalized)
  else rows[index] = normalized
  homeworks.value = rows
  homeworkCache.set(authState.user?.username || 'current-user', rows)
}

function isImageFile(file) {
  return file.type.startsWith('image/') || /\.(jpe?g|png|gif|webp)$/i.test(file.name)
}

function updateFilePreviews() {
  filePreviews.value.forEach(({ url }) => {
    if (url) URL.revokeObjectURL(url)
  })
  filePreviews.value = selectedFiles.value.map((file) => ({
    file,
    url: isImageFile(file) ? URL.createObjectURL(file) : '',
  }))
}

function clearSelectedFiles() {
  selectedFiles.value = []
  draggingFiles.value = false
  updateFilePreviews()
  fileError.value = ''
}

function addSelectedFiles(fileList) {
  fileError.value = ''
  const combined = [...selectedFiles.value]
  const seen = new Set(combined.map((file) => `${file.name}:${file.size}:${file.lastModified}`))
  for (const file of Array.from(fileList || [])) {
    const key = `${file.name}:${file.size}:${file.lastModified}`
    if (!seen.has(key)) {
      combined.push(file)
      seen.add(key)
    }
  }

  const tooLarge = combined.find((file) => file.size > 15 * 1024 * 1024)
  const totalSize = combined.reduce((total, file) => total + file.size, 0)
  if (combined.length > 10) fileError.value = 'Можно прикрепить не больше 10 файлов.'
  else if (tooLarge) fileError.value = `Файл «${tooLarge.name}» больше 15 МБ.`
  else if (totalSize > 50 * 1024 * 1024) fileError.value = 'Общий размер файлов больше 50 МБ.'
  else {
    selectedFiles.value = combined
    updateFilePreviews()
  }

  if (fileInput.value) fileInput.value.value = ''
}

function removeSelectedFile(index) {
  fileError.value = ''
  selectedFiles.value.splice(index, 1)
  updateFilePreviews()
}

function closeEditor(force = false) {
  if (!force && (saving.value || uploadingFiles.value)) return
  editorOpen.value = false
  clearSelectedFiles()
}

function normalizeSubjects(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.items)) return payload.items
  return []
}

async function refreshSubjects() {
  subjectsLoading.value = true
  subjectError.value = ''
  try {
    const rows = normalizeSubjects(await getSubjects())
    subjects.value = rows
    if (!rows.some((subject) => String(subject.id) === String(form.subject))) {
      form.subject = rows[0]?.id ?? ''
    }
  } catch (err) {
    subjectError.value = err.message
  } finally {
    subjectsLoading.value = false
  }
}

function resetForm() {
  editingId.value = null
  clearSelectedFiles()
  Object.assign(form, {
    subject: subjects.value[0]?.id ?? '',
    title: '',
    date: today(),
    description: '',
    tasks: [''],
  })
}

function openCreate() {
  resetForm()
  newSubjectName.value = ''
  subjectError.value = ''
  editorOpen.value = true
  void refreshSubjects()
}

function openEdit(item) {
  clearSelectedFiles()
  editingId.value = item.id
  Object.assign(form, {
    subject: item.subject,
    title: item.title,
    date: item.date,
    description: item.description || '',
    tasks: item.tasks.length ? item.tasks.map((task) => task.text) : [''],
  })
  editorOpen.value = true
  void refreshSubjects()
}

function handleFilesChange(event) {
  addSelectedFiles(event.target.files)
}

function handleFilesDrop(event) {
  draggingFiles.value = false
  addSelectedFiles(event.dataTransfer?.files)
}

async function addSubjectFromEditor() {
  const subjectName = newSubjectName.value.trim()
  if (!subjectName) {
    subjectError.value = 'Введи название предмета.'
    return
  }

  creatingSubject.value = true
  subjectError.value = ''
  try {
    const subject = await createSubject({ name: subjectName })
    subjects.value = [...subjects.value, subject].sort((a, b) => a.name.localeCompare(b.name, 'ru'))
    form.subject = subject.id
    newSubjectName.value = ''
  } catch (err) {
    subjectError.value = err.message
  } finally {
    creatingSubject.value = false
  }
}

async function saveHomework() {
  if (!form.subject || !form.title.trim() || !form.date) {
    error.value = 'Заполни предмет, название и срок сдачи.'
    return
  }

  saving.value = true
  error.value = ''
  fileError.value = ''
  const creatingHomework = !editingId.value
  const data = {
    subject: Number(form.subject),
    title: form.title.trim(),
    date: form.date,
    description: form.description.trim(),
    tasks: form.tasks.map((text, order) => ({ text: text.trim(), order })).filter((task) => task.text),
  }

  try {
    const savedHomework = editingId.value
      ? await updateHomework(editingId.value, data)
      : await createHomework(data)
    editingId.value = savedHomework.id
    upsertHomework(savedHomework)
    if (creatingHomework) {
      search.value = ''
      subjectFilter.value = 'all'
    }

    if (selectedFiles.value.length) {
      uploadingFiles.value = true
      try {
        const uploaded = await uploadHomeworkFiles(savedHomework.id, selectedFiles.value)
        const current = homeworks.value.find((item) => String(item.id) === String(savedHomework.id))
        const uploadedFiles = Array.isArray(uploaded) ? uploaded : uploaded?.results || []
        if (current) upsertHomework({ ...current, files: [...current.files, ...uploadedFiles] })
        clearSelectedFiles()
      } catch (uploadError) {
        fileError.value = `Задание сохранено, но вложения не загрузились: ${uploadError.message} Отправь форму ещё раз, чтобы повторить загрузку.`
        return
      } finally {
        uploadingFiles.value = false
      }
    }

    closeEditor(true)
    void loadData()
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function removeHomework(item) {
  if (!window.confirm(`Удалить «${item.title}»? Это действие нельзя отменить.`)) return
  error.value = ''
  try {
    await deleteHomework(item.id)
    const rows = homeworks.value.filter((row) => String(row.id) !== String(item.id))
    homeworks.value = rows
    homeworkCache.set(authState.user?.username || 'current-user', rows)
    await loadData()
  } catch (err) {
    error.value = err.message
  }
}

async function download(file) {
  try {
    await downloadFile(file.download_url, file.file_name || `материал-${file.id}`)
  } catch (err) {
    error.value = err.message
  }
}

function getImageMimeType(fileName) {
  const extension = fileName.split('.').pop()?.toLowerCase()
  return ({ jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', gif: 'image/gif', webp: 'image/webp' })[extension] || ''
}

async function openAttachment(file) {
  if (file.file_type !== 'photo' || !getImageMimeType(file.file_name)) {
    await download(file)
    return
  }

  if (imagePreviewUrl.value) URL.revokeObjectURL(imagePreviewUrl.value)
  imagePreviewUrl.value = ''
  imagePreviewTitle.value = file.file_name
  imagePreviewError.value = ''
  imagePreviewOpen.value = true
  imagePreviewLoading.value = true
  const requestId = ++imagePreviewRequestId
  try {
    const blob = await getFileBlob(file.download_url)
    if (requestId !== imagePreviewRequestId) return
    const previewBlob = new Blob([blob], { type: getImageMimeType(file.file_name) })
    imagePreviewUrl.value = URL.createObjectURL(previewBlob)
  } catch (err) {
    if (requestId === imagePreviewRequestId) imagePreviewError.value = err.message
  } finally {
    if (requestId === imagePreviewRequestId) imagePreviewLoading.value = false
  }
}

function closeImagePreview() {
  imagePreviewRequestId += 1
  imagePreviewOpen.value = false
  imagePreviewLoading.value = false
  imagePreviewError.value = ''
  if (imagePreviewUrl.value) URL.revokeObjectURL(imagePreviewUrl.value)
  imagePreviewUrl.value = ''
}

onMounted(loadData)
onBeforeUnmount(() => {
  clearSelectedFiles()
  closeImagePreview()
})
</script>

<template>
  <main class="page-wrap">
    <section class="page-heading">
      <div>
        <p class="eyebrow"><span class="eyebrow-dot"></span> ТВОЁ УЧЕБНОЕ ПРОСТРАНСТВО</p>
        <h1>Домашние задания<span class="period">.</span></h1>
        <p class="page-subtitle">Всё, что нужно успеть — собрано здесь.</p>
      </div>
      <button v-if="isStaff" class="button button-primary" type="button" @click="openCreate">＋ Добавить задание</button>
    </section>

    <section class="summary-row" aria-label="Статистика заданий">
      <div class="summary-card"><span class="summary-icon icon-lilac">▤</span><span><strong>{{ homeworks.length }}</strong><small>всего заданий</small></span></div>
      <div class="summary-card"><span class="summary-icon icon-sun">◷</span><span><strong>{{ upcomingCount }}</strong><small>ещё впереди</small></span></div>
      <div class="summary-note"><span>✳</span><p>Делай понемногу —<br />и всё успеешь.</p></div>
    </section>

    <section class="section-toolbar homework-toolbar">
      <div class="section-title"><h2>{{ sortMode === 'deadline' ? 'Ближайшие' : sortMode === 'newest' ? 'Недавно добавлены' : 'Давно добавлены' }}</h2><span>{{ filteredHomeworks.length }} {{ filteredHomeworks.length === 1 ? 'задание' : 'заданий' }}</span><button class="refresh-button" type="button" :disabled="refreshing" aria-label="Обновить задания" @click="loadData">{{ refreshing ? 'Обновляем…' : '↻ Обновить' }}</button></div>
      <div class="homework-controls">
        <div class="filters">
          <label class="search-box"><span aria-hidden="true">⌕</span><input v-model="search" placeholder="Найти задание" aria-label="Найти задание" /></label>
          <select v-model="subjectFilter" aria-label="Фильтр по предмету"><option value="all">Все предметы</option><option v-for="subject in subjects" :key="subject.id" :value="String(subject.id)">{{ subject.name }}</option></select>
        </div>
        <label class="sort-control"><span>Сортировать</span><select v-model="sortMode" aria-label="Сортировка заданий"><option value="deadline">Ближайший срок</option><option value="newest">Сначала новые</option><option value="oldest">Сначала старые</option></select></label>
      </div>
    </section>

    <p v-if="error" class="notice notice-error" role="alert">{{ error }}</p>
    <div v-if="loading" class="homework-grid" aria-label="Загружаем задания" aria-busy="true"><article v-for="placeholder in 2" :key="placeholder" class="homework-skeleton"><span></span><span></span><span></span></article></div>
    <div v-else-if="!filteredHomeworks.length" class="empty-state">
      <span class="empty-mark">✳</span>
      <h2>{{ homeworks.length ? 'Ничего не нашлось' : 'Пока заданий нет' }}</h2>
      <p>{{ homeworks.length ? 'Измени поиск или фильтр по предмету.' : 'Задания появятся здесь, как только администратор их добавит.' }}</p>
      <button v-if="isStaff && !homeworks.length && subjects.length" class="button button-outline" @click="openCreate">Добавить первое задание</button>
      <RouterLink v-if="isStaff && !homeworks.length && !subjects.length" class="button button-outline" :to="{ name: 'subjects' }">Сначала добавить предмет</RouterLink>
    </div>

    <section v-else class="homework-grid" aria-label="Список заданий">
      <article v-for="(item, index) in filteredHomeworks" :key="item.id" class="homework-card" :class="`tone-${index % 3}`">
        <div class="card-topline"><span class="subject-tag">{{ item.subject_detail?.name }}</span><time class="due-date" :datetime="item.date">{{ dateLabel(item.date) }}</time></div>
        <div class="card-content">
          <RouterLink class="card-title-link" :to="{ name: 'homework-detail', params: { id: item.id } }"><h3>{{ item.title }}</h3></RouterLink>
          <p v-if="item.description" class="card-description">{{ item.description }}</p>
          <ol v-if="item.tasks.length" class="task-list"><li v-for="task in item.tasks" :key="task.id">{{ task.text }}</li></ol>
        </div>
        <div v-if="item.files.length" class="file-row"><button v-for="file in item.files" :key="file.id" class="file-chip" @click="openAttachment(file)"><span>{{ file.file_type === 'photo' ? '▧' : '↧' }}</span>{{ file.file_name }}</button></div>
        <div class="card-bottom"><span class="deadline" :class="{ overdue: item.date < today() }"><i></i>{{ deadlineLabel(item.date) }}</span><div v-if="isStaff" class="card-actions"><button type="button" @click="openEdit(item)">Изменить</button><button type="button" @click="removeHomework(item)">Удалить</button></div></div>
      </article>
    </section>

    <div v-if="editorOpen" class="editor-backdrop" @click.self="closeEditor()" @keydown.esc="closeEditor()">
      <section class="editor-card" role="dialog" aria-modal="true" aria-labelledby="editor-title">
        <header class="editor-heading"><div><p class="eyebrow">{{ editingId ? 'ОБНОВЛЕНИЕ' : 'НОВОЕ ЗАДАНИЕ' }}</p><h2 id="editor-title">{{ editingId ? 'Изменить задание' : 'Добавить задание' }}</h2></div><button class="close-button" type="button" aria-label="Закрыть форму" :disabled="saving || uploadingFiles" @click="closeEditor()">×</button></header>
        <form class="editor-form" @submit.prevent="saveHomework">
          <label class="editor-subject-field"><span class="field-heading"><span>Предмет</span><button type="button" :disabled="subjectsLoading" @click="refreshSubjects">{{ subjectsLoading ? 'Обновляем…' : '↻ Обновить список' }}</button></span><select v-model="form.subject" required :disabled="subjectsLoading || !subjects.length"><option value="" disabled>{{ subjectsLoading ? 'Загружаем предметы…' : subjects.length ? 'Выбери предмет' : 'Предметов пока нет' }}</option><option v-for="subject in subjects" :key="subject.id" :value="subject.id">{{ subject.name }}</option></select></label>
          <label>Название<input v-model="form.title" maxlength="500" required placeholder="Например, упражнения 4–6" /></label>
          <label>Сдать до<input v-model="form.date" type="date" required /></label>
          <label>Описание<textarea v-model="form.description" rows="3" placeholder="Подробности, страницы или комментарий"></textarea></label>
          <div class="task-editor"><div class="field-heading"><span>Пункты задания <small>по желанию</small></span><button type="button" @click="form.tasks.push('')">＋ Добавить пункт</button></div><div v-for="(task, index) in form.tasks" :key="index" class="task-input-row"><input v-model="form.tasks[index]" :aria-label="`Пункт ${index + 1}`" placeholder="Текст задания" /><button type="button" :aria-label="`Удалить пункт ${index + 1}`" @click="form.tasks.splice(index, 1)">×</button></div></div>
          <div class="attachment-field">
            <div class="field-heading"><span>Фото и файлы <small>по желанию · до 10 файлов</small></span></div>
            <div v-if="editingId && currentHomeworkFiles.length" class="current-file-list"><span class="current-file-caption">Уже прикреплены</span><button v-for="file in currentHomeworkFiles" :key="file.id" class="file-chip" type="button" @click="openAttachment(file)"><span>{{ file.file_type === 'photo' ? '▧' : '↧' }}</span>{{ file.file_name }}</button></div>
            <div class="upload-dropzone" :class="{ 'upload-dropzone-active': draggingFiles }" @dragover.prevent="draggingFiles = true" @dragleave.prevent="draggingFiles = false" @drop.prevent="handleFilesDrop">
              <span class="upload-icon" aria-hidden="true">↥</span>
              <div><strong>Перетащи фото или файл сюда</strong><small>JPG, PNG, WEBP, GIF, PDF, TXT, DOCX, XLSX, PPTX · до 15 МБ каждый</small></div>
              <input ref="fileInput" class="file-input-hidden" type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,.pdf,.txt,.docx,.xlsx,.pptx" aria-label="Выбрать фотографии и файлы" @change="handleFilesChange" />
              <button class="button button-outline" type="button" :disabled="saving || uploadingFiles" @click="fileInput?.click()">Выбрать</button>
            </div>
            <div v-if="selectedFiles.length" class="selected-file-list" aria-label="Выбранные вложения">
              <article v-for="(file, index) in selectedFiles" :key="`${file.name}-${file.lastModified}-${index}`" class="selected-file-row">
                <img v-if="filePreviews[index]?.url" class="selected-file-preview" :src="filePreviews[index].url" :alt="`Предпросмотр ${file.name}`" />
                <span v-else class="selected-file-icon" aria-hidden="true">▤</span>
                <span class="selected-file-meta"><strong>{{ file.name }}</strong><small>{{ (file.size / 1024 / 1024).toFixed(2) }} МБ</small></span>
                <button class="remove-file-button" type="button" :disabled="saving || uploadingFiles" :aria-label="`Убрать файл ${file.name}`" @click="removeSelectedFile(index)">×</button>
              </article>
            </div>
            <p v-if="fileError" class="notice notice-error file-error" role="alert">{{ fileError }}</p>
          </div>
          <div v-if="!subjects.length && !subjectsLoading" class="notice notice-warm no-subjects-notice">
            <p>В списке приложения пока нет предметов. Можно добавить его здесь — он сразу появится в задании.</p>
            <div class="quick-subject-row"><input v-model="newSubjectName" maxlength="100" aria-label="Название нового предмета" placeholder="Например, История" @keydown.enter.prevent="addSubjectFromEditor" /><button class="button button-outline" type="button" :disabled="creatingSubject" @click="addSubjectFromEditor">{{ creatingSubject ? 'Добавляем…' : '＋ Добавить предмет' }}</button></div>
            <p v-if="subjectError" class="quick-subject-error" role="alert">{{ subjectError }}</p>
            <RouterLink v-if="isStaff" :to="{ name: 'subjects' }" @click="closeEditor()">Открыть список предметов</RouterLink>
          </div>
          <p v-if="subjectError && (subjects.length || subjectsLoading)" class="notice notice-error" role="alert">{{ subjectError }}</p>
          <div class="editor-actions"><button type="button" class="button button-outline" :disabled="saving || uploadingFiles" @click="closeEditor()">Отмена</button><button class="button button-primary" :disabled="saving || uploadingFiles || subjectsLoading || !subjects.length || !form.subject">{{ uploadingFiles ? 'Загружаем файлы…' : saving ? 'Сохраняем…' : editingId ? 'Сохранить' : 'Опубликовать' }}</button></div>
        </form>
      </section>
    </div>

    <div v-if="imagePreviewOpen" class="image-preview-backdrop" role="dialog" aria-modal="true" aria-label="Просмотр изображения" @click.self="closeImagePreview" @keydown.esc="closeImagePreview" tabindex="-1">
      <section class="image-preview-card">
        <header><strong>{{ imagePreviewTitle }}</strong><button class="close-button" type="button" aria-label="Закрыть просмотр" @click="closeImagePreview">×</button></header>
        <div v-if="imagePreviewLoading" class="loading-state"><span class="spinner"></span> Загружаем фото…</div>
        <p v-else-if="imagePreviewError" class="notice notice-error" role="alert">{{ imagePreviewError }}</p>
        <img v-else-if="imagePreviewUrl" :src="imagePreviewUrl" :alt="imagePreviewTitle" @error="imagePreviewError = 'Не удалось показать это изображение.'" />
      </section>
    </div>
  </main>
</template>
