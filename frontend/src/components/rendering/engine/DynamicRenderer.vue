<script setup lang="ts">
/**
 * 动态渲染引擎
 * Dynamic Renderer - MDX-like Component for Vue
 * 
 * 支持在 Markdown 中嵌入 Vue 组件
 * 语法: :::ComponentName{prop1="value1" prop2=value2}
 * 或:   <ComponentName :prop1="value1" />
 */

import { ref, computed, h, resolveComponent, type VNode, watch, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'
import { getComponent, hasComponent } from './ComponentRegistry'
import type { ParsedBlock, RenderContext } from '../types'

// Import common languages for code highlighting
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import json from 'highlight.js/lib/languages/json'
import bash from 'highlight.js/lib/languages/bash'

// Register languages
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('json', json)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('ts', typescript)

// Props
interface Props {
  content: string
  context?: RenderContext
  components?: Record<string, unknown>
}

const props = withDefaults(defineProps<Props>(), {
  context: () => ({}),
  components: () => ({}),
})

// Emits
const emit = defineEmits<{
  (e: 'componentEvent', data: { component: string; event: string; payload: unknown }): void
  (e: 'renderComplete'): void
}>()

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

// Custom renderer for code blocks
const renderer = new marked.Renderer()
renderer.code = function({ text, lang }: { text: string; lang?: string }) {
  const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
  let highlighted: string
  try {
    highlighted = hljs.highlight(text, { language }).value
  } catch {
    highlighted = hljs.highlightAuto(text).value
  }
  return `<pre class="code-block"><code class="hljs language-${language}">${highlighted}</code></pre>`
}
marked.use({ renderer })

/**
 * 组件语法正则表达式
 * 
 * 支持的语法:
 * 1. :::ComponentName{prop1="value" prop2=123}
 *    内容...
 *    :::
 * 
 * 2. <ComponentName :prop1="value" prop2="123" />
 * 
 * 3. {{ComponentName prop1="value"}}
 */
const COMPONENT_PATTERNS = {
  // :::Component{props} content :::
  fenced: /^:::(\w+)(?:\{([^}]*)\})?\s*\n([\s\S]*?)\n:::\s*$/gm,
  
  // <Component :prop="value" /> (self-closing)
  selfClosing: /<(\w+)([^>]*?)\/>/g,
  
  // <Component :prop="value">content</Component>
  withContent: /<(\w+)([^>]*)>([\s\S]*?)<\/\1>/g,
  
  // {{Component prop="value"}}
  mustache: /\{\{(\w+)([^}]*)\}\}/g,
}

/**
 * 解析属性字符串
 */
function parseProps(propsString: string): Record<string, unknown> {
  if (!propsString?.trim()) return {}
  
  const props: Record<string, unknown> = {}
  
  // Match key="value", key='value', key=value, :key="value"
  const propRegex = /:?(\w+)=(?:"([^"]*)"|'([^']*)'|(\S+))/g
  let match
  
  while ((match = propRegex.exec(propsString)) !== null) {
    const [, key, doubleQuoted, singleQuoted, unquoted] = match
    let value: unknown = doubleQuoted ?? singleQuoted ?? unquoted
    
    // Try to parse JSON values
    if (typeof value === 'string') {
      if (value === 'true') value = true
      else if (value === 'false') value = false
      else if (/^-?\d+(\.\d+)?$/.test(value)) value = parseFloat(value)
      else if (value.startsWith('[') || value.startsWith('{')) {
        try {
          value = JSON.parse(value)
        } catch {
          // Keep as string
        }
      }
    }
    
    props[key] = value
  }
  
  return props
}

/**
 * 解析内容为块数组
 */
function parseContent(content: string): ParsedBlock[] {
  const blocks: ParsedBlock[] = []
  let remaining = content
  let lastIndex = 0
  
  // Process fenced components: :::Component{props}\ncontent\n:::
  const fencedRegex = /:::(\w+)(?:\{([^}]*)\})?\s*\n([\s\S]*?)\n:::/g
  let match
  
  const processedRanges: Array<{ start: number; end: number }> = []
  
  while ((match = fencedRegex.exec(content)) !== null) {
    const [fullMatch, componentName, propsStr, innerContent] = match
    const startIndex = match.index
    const endIndex = startIndex + fullMatch.length
    
    // Add text before this component
    if (startIndex > lastIndex) {
      const textBefore = content.slice(lastIndex, startIndex).trim()
      if (textBefore) {
        blocks.push({
          type: 'markdown',
          content: textBefore,
        })
      }
    }
    
    // Add component block
    blocks.push({
      type: 'component',
      content: innerContent || '',
      componentName,
      props: parseProps(propsStr || ''),
      rawText: fullMatch,
    })
    
    processedRanges.push({ start: startIndex, end: endIndex })
    lastIndex = endIndex
  }
  
  // Process self-closing tags: <Component prop="value" />
  const selfClosingRegex = /<(\w+)([^>]*?)\/>/g
  remaining = content
  
  while ((match = selfClosingRegex.exec(content)) !== null) {
    const startIndex = match.index
    const endIndex = startIndex + match[0].length
    
    // Check if already processed
    if (processedRanges.some(r => startIndex >= r.start && endIndex <= r.end)) {
      continue
    }
    
    const [fullMatch, componentName, propsStr] = match
    
    // Only process registered components
    if (hasComponent(componentName) || props.components?.[componentName]) {
      // Add text before
      if (startIndex > lastIndex) {
        const textBefore = content.slice(lastIndex, startIndex).trim()
        if (textBefore) {
          blocks.push({
            type: 'markdown',
            content: textBefore,
          })
        }
      }
      
      blocks.push({
        type: 'component',
        content: '',
        componentName,
        props: parseProps(propsStr || ''),
        rawText: fullMatch,
      })
      
      processedRanges.push({ start: startIndex, end: endIndex })
      lastIndex = endIndex
    }
  }
  
  // Add remaining text
  if (lastIndex < content.length) {
    const remainingText = content.slice(lastIndex).trim()
    if (remainingText) {
      blocks.push({
        type: 'markdown',
        content: remainingText,
      })
    }
  }
  
  // If no blocks were created, treat entire content as markdown
  if (blocks.length === 0) {
    blocks.push({
      type: 'markdown',
      content: content,
    })
  }
  
  return blocks
}

// Parsed blocks
const parsedBlocks = computed(() => parseContent(props.content))

/**
 * 渲染 Markdown 内容
 */
function renderMarkdown(content: string): string {
  try {
    return marked.parse(content) as string
  } catch (err) {
    console.error('[DynamicRenderer] Markdown parse error:', err)
    return `<p>${content}</p>`
  }
}

/**
 * 渲染组件
 */
function renderComponent(block: ParsedBlock): VNode | null {
  if (!block.componentName) return null
  
  // Check props.components first (locally passed)
  const localComponent = props.components?.[block.componentName]
  if (localComponent) {
    return h(localComponent as any, {
      ...block.props,
      ...props.context.data,
      onEvent: (event: string, payload: unknown) => {
        emit('componentEvent', { 
          component: block.componentName!, 
          event, 
          payload 
        })
      },
    })
  }
  
  // Check registry
  const registered = getComponent(block.componentName)
  if (registered) {
    return h(registered.component, {
      ...block.props,
      ...props.context.data,
      onEvent: (event: string, payload: unknown) => {
        emit('componentEvent', { 
          component: block.componentName!, 
          event, 
          payload 
        })
      },
    })
  }
  
  // Try to resolve globally registered component
  try {
    const resolved = resolveComponent(block.componentName)
    if (resolved && typeof resolved !== 'string') {
      return h(resolved, {
        ...block.props,
        ...props.context.data,
      })
    }
  } catch {
    // Component not found
  }
  
  // Return placeholder for unknown component
  console.warn(`[DynamicRenderer] Component "${block.componentName}" not found`)
  return h('div', { 
    class: 'component-placeholder',
    'data-component': block.componentName,
  }, `[Component: ${block.componentName}]`)
}

// Trigger render complete
onMounted(() => {
  emit('renderComplete')
})

watch(() => props.content, () => {
  emit('renderComplete')
})
</script>

<template>
  <div class="dynamic-renderer" :class="{ 'theme-dark': context?.theme === 'dark' }">
    <template v-for="(block, index) in parsedBlocks" :key="index">
      <!-- Markdown Block -->
      <div 
        v-if="block.type === 'markdown'"
        class="markdown-block"
        v-html="renderMarkdown(block.content)"
      />
      
      <!-- Component Block -->
      <div 
        v-else-if="block.type === 'component'"
        class="component-block"
        :data-component="block.componentName"
      >
        <component :is="() => renderComponent(block)" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.dynamic-renderer {
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.6;
  color: #374151;
}

.dynamic-renderer.theme-dark {
  color: #d1d5db;
}

.markdown-block {
  margin-bottom: 1.5rem;
}

.component-block {
  margin: 1.5rem 0;
}

/* Markdown styles */
.markdown-block :deep(h1),
.markdown-block :deep(h2),
.markdown-block :deep(h3),
.markdown-block :deep(h4) {
  font-weight: 600;
  color: #111827;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.theme-dark .markdown-block :deep(h1),
.theme-dark .markdown-block :deep(h2),
.theme-dark .markdown-block :deep(h3),
.theme-dark .markdown-block :deep(h4) {
  color: #f9fafb;
}

.markdown-block :deep(h1) { font-size: 1.875rem; }
.markdown-block :deep(h2) { font-size: 1.5rem; }
.markdown-block :deep(h3) { font-size: 1.25rem; }
.markdown-block :deep(h4) { font-size: 1.125rem; }

.markdown-block :deep(p) {
  margin-bottom: 1em;
}

.markdown-block :deep(ul),
.markdown-block :deep(ol) {
  margin-left: 1.5em;
  margin-bottom: 1em;
}

.markdown-block :deep(li) {
  margin-bottom: 0.5em;
}

.markdown-block :deep(blockquote) {
  border-left: 4px solid #e5e7eb;
  padding-left: 1em;
  margin: 1em 0;
  color: #6b7280;
  font-style: italic;
}

.theme-dark .markdown-block :deep(blockquote) {
  border-left-color: #374151;
  color: #9ca3af;
}

.markdown-block :deep(a) {
  color: #4f46e5;
  text-decoration: underline;
}

.markdown-block :deep(a:hover) {
  color: #4338ca;
}

.markdown-block :deep(code) {
  background: #f3f4f6;
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.theme-dark .markdown-block :deep(code) {
  background: #374151;
}

.markdown-block :deep(.code-block) {
  background: #1f2937;
  border-radius: 8px;
  padding: 1em;
  margin: 1em 0;
  overflow-x: auto;
}

.markdown-block :deep(.code-block code) {
  background: transparent;
  padding: 0;
  color: #f9fafb;
}

.markdown-block :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.markdown-block :deep(th),
.markdown-block :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5em 1em;
  text-align: left;
}

.theme-dark .markdown-block :deep(th),
.theme-dark .markdown-block :deep(td) {
  border-color: #374151;
}

.markdown-block :deep(th) {
  background: #f9fafb;
  font-weight: 600;
}

.theme-dark .markdown-block :deep(th) {
  background: #374151;
}

.markdown-block :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.markdown-block :deep(hr) {
  border: 0;
  border-top: 1px solid #e5e7eb;
  margin: 2em 0;
}

.theme-dark .markdown-block :deep(hr) {
  border-top-color: #374151;
}

/* Component placeholder */
.component-block :deep(.component-placeholder) {
  background: #fef3c7;
  border: 1px dashed #f59e0b;
  border-radius: 8px;
  padding: 1em;
  text-align: center;
  color: #92400e;
  font-size: 0.875rem;
}

.theme-dark .component-block :deep(.component-placeholder) {
  background: #451a03;
  border-color: #78350f;
  color: #fcd34d;
}
</style>
