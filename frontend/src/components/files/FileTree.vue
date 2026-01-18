<script setup lang="ts">
/**
 * FileTree Component - 文件树组件
 *
 * 可展开的目录树视图，类似 VS Code 的文件浏览器
 */
import { ref, watch } from 'vue'
import { type DirectoryTreeNode } from '@/api/files'
import {
  FolderIcon,
  FolderOpenIcon,
  DocumentIcon,
  ChevronRightIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'

// Props
const props = defineProps<{
  tree: DirectoryTreeNode | null
  selectedPath?: string
  rootPath?: string
}>()

// Emits
const emit = defineEmits<{
  (e: 'select', node: DirectoryTreeNode, fullPath: string): void
  (e: 'expand', node: DirectoryTreeNode, fullPath: string): void
}>()

// State
const expandedNodes = ref<Set<string>>(new Set())
const selectedNodePath = ref<string>('')

// 语言图标颜色映射
const languageColors: Record<string, string> = {
  python: 'text-yellow-500',
  javascript: 'text-yellow-400',
  typescript: 'text-blue-500',
  vue: 'text-green-500',
  html: 'text-orange-500',
  css: 'text-blue-400',
  scss: 'text-pink-400',
  json: 'text-gray-500',
  markdown: 'text-gray-600',
  go: 'text-cyan-500',
  rust: 'text-orange-600',
  java: 'text-red-500',
}

// Methods
const toggleExpand = (path: string) => {
  if (expandedNodes.value.has(path)) {
    expandedNodes.value.delete(path)
  } else {
    expandedNodes.value.add(path)
  }
}

const isExpanded = (path: string) => expandedNodes.value.has(path)

const handleNodeClick = (node: DirectoryTreeNode, path: string) => {
  selectedNodePath.value = path
  
  if (node.type === 'directory') {
    toggleExpand(path)
    emit('expand', node, path)
  }
  emit('select', node, path)
}

const getLanguageColor = (language: string | null | undefined) => {
  if (!language) return 'text-gray-400'
  return languageColors[language] || 'text-gray-400'
}

const formatSize = (size: number | null | undefined) => {
  if (!size) return ''
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

// 初始展开根节点
watch(
  () => props.tree,
  (tree) => {
    if (tree && tree.type === 'directory') {
      expandedNodes.value.add(tree.name)
    }
  },
  { immediate: true }
)

// 同步外部 selectedPath
watch(
  () => props.selectedPath,
  (path) => {
    if (path) selectedNodePath.value = path
  },
  { immediate: true }
)
</script>

<template>
  <div class="file-tree text-sm select-none">
    <template v-if="tree">
      <!-- Render tree recursively using template -->
      <div class="tree-root">
        <!-- Root node -->
        <div
          class="node-row flex items-center gap-1 py-1 px-2 rounded cursor-pointer transition-colors"
          :class="[
            selectedNodePath === tree.name ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
          ]"
          @click="handleNodeClick(tree, tree.name)"
        >
          <span class="w-4 h-4 flex-shrink-0">
            <component
              :is="isExpanded(tree.name) ? ChevronDownIcon : ChevronRightIcon"
              class="w-4 h-4 text-gray-400"
            />
          </span>
          <component
            :is="isExpanded(tree.name) ? FolderOpenIcon : FolderIcon"
            class="w-4 h-4 flex-shrink-0 text-amber-500"
          />
          <span class="truncate flex-1 font-medium text-gray-700 dark:text-gray-300">
            {{ tree.name }}
          </span>
        </div>
        
        <!-- First level children -->
        <template v-if="isExpanded(tree.name) && tree.children">
          <template
            v-for="child1 in tree.children"
            :key="child1.name"
          >
            <div
              class="node-row flex items-center gap-1 py-1 rounded cursor-pointer transition-colors"
              :class="[
                selectedNodePath === `${tree.name}/${child1.name}` ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
              ]"
              style="padding-left: 20px;"
              @click="handleNodeClick(child1, `${tree.name}/${child1.name}`)"
            >
              <span class="w-4 h-4 flex-shrink-0">
                <component
                  :is="isExpanded(`${tree.name}/${child1.name}`) ? ChevronDownIcon : ChevronRightIcon"
                  v-if="child1.type === 'directory'"
                  class="w-4 h-4 text-gray-400"
                />
              </span>
              <component
                :is="child1.type === 'directory' 
                  ? (isExpanded(`${tree.name}/${child1.name}`) ? FolderOpenIcon : FolderIcon)
                  : DocumentIcon"
                class="w-4 h-4 flex-shrink-0"
                :class="child1.type === 'directory' ? 'text-amber-500' : getLanguageColor(child1.language)"
              />
              <span
                class="truncate flex-1"
                :class="child1.type === 'directory' ? 'font-medium text-gray-700 dark:text-gray-300' : 'text-gray-600 dark:text-gray-400'"
              >
                {{ child1.name }}
              </span>
              <span
                v-if="child1.type === 'file' && child1.size"
                class="text-xs text-gray-400 flex-shrink-0 pr-2"
              >
                {{ formatSize(child1.size) }}
              </span>
            </div>
            
            <!-- Second level children -->
            <template v-if="child1.type === 'directory' && isExpanded(`${tree.name}/${child1.name}`) && child1.children">
              <template
                v-for="child2 in child1.children"
                :key="child2.name"
              >
                <div
                  class="node-row flex items-center gap-1 py-1 rounded cursor-pointer transition-colors"
                  :class="[
                    selectedNodePath === `${tree.name}/${child1.name}/${child2.name}` ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                  ]"
                  style="padding-left: 32px;"
                  @click="handleNodeClick(child2, `${tree.name}/${child1.name}/${child2.name}`)"
                >
                  <span class="w-4 h-4 flex-shrink-0">
                    <component
                      :is="isExpanded(`${tree.name}/${child1.name}/${child2.name}`) ? ChevronDownIcon : ChevronRightIcon"
                      v-if="child2.type === 'directory'"
                      class="w-4 h-4 text-gray-400"
                    />
                  </span>
                  <component
                    :is="child2.type === 'directory'
                      ? (isExpanded(`${tree.name}/${child1.name}/${child2.name}`) ? FolderOpenIcon : FolderIcon)
                      : DocumentIcon"
                    class="w-4 h-4 flex-shrink-0"
                    :class="child2.type === 'directory' ? 'text-amber-500' : getLanguageColor(child2.language)"
                  />
                  <span
                    class="truncate flex-1"
                    :class="child2.type === 'directory' ? 'font-medium text-gray-700 dark:text-gray-300' : 'text-gray-600 dark:text-gray-400'"
                  >
                    {{ child2.name }}
                  </span>
                  <span
                    v-if="child2.type === 'file' && child2.size"
                    class="text-xs text-gray-400 flex-shrink-0 pr-2"
                  >
                    {{ formatSize(child2.size) }}
                  </span>
                  <span
                    v-if="child2.truncated"
                    class="text-xs text-gray-400 pr-2"
                  >...</span>
                </div>
                
                <!-- Third level children -->
                <template v-if="child2.type === 'directory' && isExpanded(`${tree.name}/${child1.name}/${child2.name}`) && child2.children">
                  <template
                    v-for="child3 in child2.children"
                    :key="child3.name"
                  >
                    <div
                      class="node-row flex items-center gap-1 py-1 rounded cursor-pointer transition-colors"
                      :class="[
                        selectedNodePath === `${tree.name}/${child1.name}/${child2.name}/${child3.name}` ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                      ]"
                      style="padding-left: 44px;"
                      @click="handleNodeClick(child3, `${tree.name}/${child1.name}/${child2.name}/${child3.name}`)"
                    >
                      <span class="w-4 h-4 flex-shrink-0">
                        <component
                          :is="ChevronRightIcon"
                          v-if="child3.type === 'directory'"
                          class="w-4 h-4 text-gray-400"
                        />
                      </span>
                      <component
                        :is="child3.type === 'directory' ? FolderIcon : DocumentIcon"
                        class="w-4 h-4 flex-shrink-0"
                        :class="child3.type === 'directory' ? 'text-amber-500' : getLanguageColor(child3.language)"
                      />
                      <span
                        class="truncate flex-1"
                        :class="child3.type === 'directory' ? 'font-medium text-gray-700 dark:text-gray-300' : 'text-gray-600 dark:text-gray-400'"
                      >
                        {{ child3.name }}
                      </span>
                      <span
                        v-if="child3.type === 'file' && child3.size"
                        class="text-xs text-gray-400 flex-shrink-0 pr-2"
                      >
                        {{ formatSize(child3.size) }}
                      </span>
                      <span
                        v-if="child3.truncated"
                        class="text-xs text-gray-400 pr-2"
                      >...</span>
                    </div>
                  </template>
                </template>
              </template>
            </template>
          </template>
        </template>
      </div>
    </template>
    
    <div
      v-else
      class="text-gray-400 text-center py-8"
    >
      暂无文件
    </div>
  </div>
</template>

<style scoped>
.node-row:active {
  @apply scale-[0.99];
}
</style>
