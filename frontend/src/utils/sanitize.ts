/**
 * HTML 安全渲染工具
 * 防止 XSS 攻击
 */
import DOMPurify from 'dompurify'
import { marked } from 'marked'

/**
 * 清理 HTML，防止 XSS 攻击
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'code', 'pre', 'a', 'ul', 'ol', 'li',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'hr',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'span', 'div', 'img'
    ],
    ALLOWED_ATTR: ['href', 'class', 'id', 'src', 'alt', 'title', 'target'],
    ALLOW_DATA_ATTR: false,
  })
}

/**
 * 渲染 Markdown 为安全的 HTML
 */
export function renderMarkdown(markdown: string): string {
  if (!markdown) return ''

  try {
    const html = marked(markdown) as string
    return sanitizeHtml(html)
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return sanitizeHtml(markdown)
  }
}

/**
 * 渲染纯文本（转义所有 HTML）
 */
export function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
