<template>
  <div class="preview-area">
    <div class="preview-content">
      <div v-if="currentTab === 'report'" class="preview-placeholder">
        <div class="icon">📄</div>
        <h3>研究报告预览</h3>
        <p>AI Deep Research 生成的研究报告将在这里显示</p>
      </div>

      <div v-else-if="currentTab === 'ppt'" class="preview-placeholder">
        <div class="icon">📊</div>
        <h3>PPT 预览</h3>
        <p>AI PPT Generation 生成的演示文稿将在这里显示</p>
      </div>

      <div v-else-if="currentTab === 'file-diff'" class="preview-placeholder">
        <div class="icon">📝</div>
        <h3>文件变更预览</h3>
        <p>Coworker 修改的文件 Diff 将在这里显示</p>
        <div class="mock-diff">
          <div class="diff-line removed">- const oldValue = 'old'</div>
          <div class="diff-line added">+ const newValue = 'new'</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  sessionId: string
  currentTab: 'report' | 'ppt' | 'file-diff'
}

defineProps<Props>()
</script>

<style scoped>
.preview-area {
  flex: 1;
  overflow-y: auto;
  background: rgba(18, 18, 18, 0.9);
}

.preview-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.preview-placeholder {
  text-align: center;
  max-width: 500px;
}

.icon {
  font-size: 64px;
  margin-bottom: 24px;
}

h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--text-primary, #ffffff);
}

p {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  margin: 0 0 24px 0;
}

.mock-diff {
  margin-top: 24px;
  text-align: left;
  background: rgba(0, 0, 0, 0.4);
  padding: 16px;
  border-radius: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.diff-line {
  padding: 4px 8px;
  border-radius: 4px;
}

.diff-line.removed {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

.diff-line.added {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

/* 滚动条样式 */
.preview-area::-webkit-scrollbar {
  width: 8px;
}

.preview-area::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

.preview-area::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.preview-area::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
