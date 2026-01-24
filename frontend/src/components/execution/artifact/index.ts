/**
 * Artifact Preview Components
 * 
 * A comprehensive set of components for previewing various artifact types
 * generated during AI agent execution.
 */

// Main components
export { default as PreviewArea } from './PreviewArea.vue'
export { default as ArtifactTabs } from './ArtifactTabs.vue'
export { default as LiveDiff } from './LiveDiff.vue'

// New artifact preview components
export { default as SandboxBrowser } from './SandboxBrowser.vue'
export { default as PdfViewer } from './PdfViewer.vue'
export { default as ChartPreview } from './ChartPreview.vue'
export { default as CodeEditor } from './CodeEditor.vue'
export { default as DataTable } from './DataTable.vue'
export { default as VideoPlayer } from './VideoPlayer.vue'
export { default as AudioPlayer } from './AudioPlayer.vue'
export { default as ExecutionReplay } from './ExecutionReplay.vue'

// Type exports
export type TabType = 
  | 'report' 
  | 'ppt' 
  | 'file-diff' 
  | 'image' 
  | 'sandbox' 
  | 'pdf' 
  | 'chart' 
  | 'code' 
  | 'table' 
  | 'video' 
  | 'audio' 
  | 'replay'
