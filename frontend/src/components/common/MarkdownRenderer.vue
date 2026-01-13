<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'

// Import commonly used languages
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import sql from 'highlight.js/lib/languages/sql'
import yaml from 'highlight.js/lib/languages/yaml'

// Register languages
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('yaml', yaml)

// Aliases
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('py', python)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('yml', yaml)

export interface MarkdownRendererProps {
  content: string
  sanitize?: boolean
}

const props = withDefaults(defineProps<MarkdownRendererProps>(), {
  sanitize: true,
})

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

// Custom renderer for code blocks with highlighting
const renderer = new marked.Renderer()
renderer.code = function({ text, lang }: { text: string; lang?: string; escaped?: boolean }) {
  const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
  let highlighted: string
  try {
    highlighted = hljs.highlight(text, { language }).value
  } catch {
    highlighted = hljs.highlightAuto(text).value
  }
  return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`
}
marked.use({ renderer })

const renderedContent = computed(() => {
  try {
    return marked.parse(props.content) as string
  } catch (err) {
    console.error('Markdown parse error:', err)
    return `<p>${props.content}</p>`
  }
})

// Re-apply highlight when content changes
watch(() => props.content, () => {
  highlightCodeBlocks()
})

onMounted(() => {
  highlightCodeBlocks()
})

function highlightCodeBlocks() {
  // This ensures code blocks are highlighted after DOM updates
  setTimeout(() => {
    document.querySelectorAll('pre code').forEach((block) => {
      if (!block.classList.contains('hljs')) {
        hljs.highlightElement(block as HTMLElement)
      }
    })
  }, 10)
}
</script>

<template>
  <div 
    class="markdown-content prose prose-invert max-w-none"
    v-html="renderedContent"
  />
</template>

<style>
/* Import highlight.js theme */
@import 'highlight.js/styles/atom-one-dark.css';

/* Override highlight.js styles for dark theme */
.markdown-content {
  color: #ffffff;
}

.markdown-content pre {
  background: #1c1c1e !important;
  padding: 1em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-content code {
  background: #1c1c1e;
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
  color: #a1a1aa;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.markdown-content pre code {
  background: transparent;
  padding: 0;
  color: #ffffff;
  font-size: 0.875rem;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  color: #ffffff;
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.markdown-content h1 {
  font-size: 1.75rem;
  border-bottom: 1px solid #27272a;
  padding-bottom: 0.3em;
}

.markdown-content h2 {
  font-size: 1.5rem;
  border-bottom: 1px solid #27272a;
  padding-bottom: 0.3em;
}

.markdown-content h3 {
  font-size: 1.25rem;
}

.markdown-content p {
  margin-bottom: 1em;
  line-height: 1.6;
  color: #a1a1aa;
}

.markdown-content a {
  color: hsl(262 83% 58%);
  text-decoration: underline;
}

.markdown-content a:hover {
  color: hsl(262 90% 65%);
}

.markdown-content ul,
.markdown-content ol {
  margin-left: 1.5em;
  margin-bottom: 1em;
  color: #a1a1aa;
}

.markdown-content li {
  margin-bottom: 0.5em;
}

.markdown-content blockquote {
  border-left: 4px solid #27272a;
  padding-left: 1em;
  margin: 1em 0;
  color: #71717a;
  font-style: italic;
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.markdown-content table th,
.markdown-content table td {
  border: 1px solid #27272a;
  padding: 0.5em;
  text-align: left;
}

.markdown-content table th {
  background: #1c1c1e;
  color: #ffffff;
  font-weight: 600;
}

.markdown-content table td {
  color: #a1a1aa;
}

.markdown-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 1em 0;
}

.markdown-content hr {
  border: 0;
  border-top: 1px solid #27272a;
  margin: 2em 0;
}

/* Code highlighting adjustments */
.markdown-content .hljs {
  background: transparent;
}

.markdown-content .hljs-comment,
.markdown-content .hljs-quote {
  color: #5c6370;
  font-style: italic;
}

.markdown-content .hljs-keyword,
.markdown-content .hljs-selector-tag,
.markdown-content .hljs-subst {
  color: #c678dd;
}

.markdown-content .hljs-number,
.markdown-content .hljs-literal,
.markdown-content .hljs-variable,
.markdown-content .hljs-template-variable,
.markdown-content .hljs-tag .hljs-attr {
  color: #d19a66;
}

.markdown-content .hljs-string,
.markdown-content .hljs-doctag {
  color: #98c379;
}

.markdown-content .hljs-title,
.markdown-content .hljs-section,
.markdown-content .hljs-selector-id {
  color: #61afef;
}

.markdown-content .hljs-subst {
  color: #abb2bf;
}

.markdown-content .hljs-type,
.markdown-content .hljs-class .hljs-title {
  color: #e5c07b;
}

.markdown-content .hljs-attribute,
.markdown-content .hljs-name,
.markdown-content .hljs-tag {
  color: #e06c75;
}

.markdown-content .hljs-regexp,
.markdown-content .hljs-link {
  color: #56b6c2;
}

.markdown-content .hljs-symbol,
.markdown-content .hljs-bullet {
  color: #61aeee;
}

.markdown-content .hljs-built_in,
.markdown-content .hljs-builtin-name {
  color: #e6c07b;
}

.markdown-content .hljs-meta {
  color: #61aeee;
}

.markdown-content .hljs-deletion {
  color: #e06c75;
}

.markdown-content .hljs-addition {
  color: #98c379;
}

.markdown-content .hljs-emphasis {
  font-style: italic;
}

.markdown-content .hljs-strong {
  font-weight: bold;
}
</style>
