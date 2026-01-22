<template>
  <div class="star-rating">
    <Star
      v-for="i in 5"
      :key="i"
      :size="12"
      class="star"
      :class="{ filled: i <= filledStars, half: i === filledStars + 1 && hasHalfStar }"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Star } from 'lucide-vue-next'

const props = defineProps<{
  score: number // 0-100
}>()

const filledStars = computed(() => {
  // 将 0-100 分数转换为 0-5 星
  const stars = (props.score / 100) * 5
  return Math.floor(stars)
})

const hasHalfStar = computed(() => {
  const stars = (props.score / 100) * 5
  return stars - Math.floor(stars) >= 0.5
})
</script>

<style scoped>
.star-rating {
  display: flex;
  gap: 2px;
}

.star {
  color: rgba(255, 255, 255, 0.2);
  transition: color 0.2s ease;
}

.star.filled {
  color: #FFD700;
  fill: #FFD700;
}

.star.half {
  color: #FFD700;
  /* Half star effect using gradient */
  background: linear-gradient(90deg, #FFD700 50%, transparent 50%);
  -webkit-background-clip: text;
  background-clip: text;
}
</style>
