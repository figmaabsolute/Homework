<script setup>
defineProps({
  eyebrow: { type: String, required: true },
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
})
</script>

<template>
  <main class="auth-layout">
    <section class="auth-panel">
      <RouterLink class="brand" :to="{ name: 'login' }"><span class="brand-symbol">к</span><span>классный круг</span></RouterLink>
      <div class="auth-content">
        <p class="eyebrow">{{ eyebrow }}</p>
        <h1>{{ title }}</h1>
        <p class="auth-subtitle">{{ subtitle }}</p>
        <slot />
        <slot name="footer" />
      </div>
      <p class="auth-bottom">Закрытое пространство нашей группы <span>✳</span></p>
    </section>
    <aside class="auth-visual" aria-hidden="true">
      <div class="visual-orbit orbit-a"></div>
      <div class="visual-orbit orbit-b"></div>
      <span class="visual-spark spark-a">✳</span>
      <span class="visual-spark spark-b">✳</span>
      <div class="visual-card card-top"><span class="tiny-label">НАША ГРУППА</span><strong>Учимся<br />вместе.</strong><span class="card-stamp">✳</span></div>
      <div class="visual-card card-bottom"><span class="tiny-label">ОДИН ШАГ ЗА РАЗ</span><strong>Большие дела<br />начинаются<br />с малого.</strong><span class="visual-line"></span></div>
      <p class="visual-caption">Задания, расписание<br />и полезные материалы — рядом.</p>
    </aside>
  </main>
</template>
