<script setup>
import { onMounted, ref } from 'vue'
import { createSubject, getSubjects, updateSubject } from '@/services/api'

const subjects = ref([])
const loading = ref(true)
const saving = ref(false)
const editingId = ref(null)
const name = ref('')
const error = ref('')
const notice = ref('')

async function loadSubjects() {
  loading.value = true
  error.value = ''
  try {
    subjects.value = await getSubjects()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function editSubject(subject) {
  editingId.value = subject.id
  name.value = subject.name
  notice.value = ''
  error.value = ''
}

function resetForm() {
  editingId.value = null
  name.value = ''
}

async function saveSubject() {
  const normalizedName = name.value.trim()
  if (!normalizedName) {
    error.value = 'Введи название предмета.'
    return
  }

  saving.value = true
  error.value = ''
  notice.value = ''
  try {
    if (editingId.value) await updateSubject(editingId.value, { name: normalizedName })
    else await createSubject({ name: normalizedName })
    notice.value = editingId.value ? 'Название предмета обновлено.' : 'Предмет добавлен.'
    resetForm()
    await loadSubjects()
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

onMounted(loadSubjects)
</script>

<template>
  <main class="page-wrap">
    <section class="page-heading">
      <div>
        <p class="eyebrow"><span class="eyebrow-dot"></span> УПРАВЛЕНИЕ ГРУППОЙ</p>
        <h1>Предметы<span class="period">.</span></h1>
        <p class="page-subtitle">Настрой список, который используется в заданиях и расписании.</p>
      </div>
      <span class="count-pill">{{ subjects.length }} {{ subjects.length === 1 ? 'предмет' : 'предметов' }}</span>
    </section>

    <p v-if="error" class="notice notice-error" role="alert">{{ error }}</p>
    <p v-if="notice" class="notice notice-success" role="status">{{ notice }}</p>

    <section class="subject-manager">
      <div class="subject-manager-copy">
        <span class="summary-icon icon-lilac">▤</span>
        <div>
          <h2>{{ editingId ? 'Изменить название' : 'Добавить предмет' }}</h2>
          <p>Список синхронизируется с базой Django и сразу доступен при создании задания.</p>
        </div>
      </div>
      <form class="subject-form" @submit.prevent="saveSubject">
        <label for="subject-name">Название предмета</label>
        <div class="subject-form-row">
          <input id="subject-name" v-model="name" maxlength="100" required placeholder="Например, История" />
          <button class="button button-primary" :disabled="saving">{{ saving ? 'Сохраняем…' : editingId ? 'Сохранить' : 'Добавить' }}</button>
          <button v-if="editingId" class="button button-outline" type="button" @click="resetForm">Отмена</button>
        </div>
      </form>
    </section>

    <section class="subject-list-section">
      <div class="section-toolbar">
        <div class="section-title"><h2>Список группы</h2><span>из общей базы данных</span></div>
        <button class="refresh-button" type="button" :disabled="loading" @click="loadSubjects">↻ Обновить</button>
      </div>
      <div v-if="loading" class="loading-state"><span class="spinner"></span> Загружаем предметы…</div>
      <div v-else-if="!subjects.length" class="empty-state subject-empty">
        <span class="empty-mark">✳</span>
        <h2>В этом подключении пока нет предметов</h2>
        <p>Добавь предмет здесь. Он сохранится через API в ту же базу, откуда приложение получает задания.</p>
      </div>
      <div v-else class="subject-list">
        <article v-for="(subject, index) in subjects" :key="subject.id" class="subject-row">
          <span class="subject-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="subject-name">{{ subject.name }}</span>
          <button class="table-action subject-edit" type="button" @click="editSubject(subject)">Изменить</button>
        </article>
      </div>
    </section>
  </main>
</template>
