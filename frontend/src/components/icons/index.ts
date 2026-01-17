/**
 * TokenDance Unified Icon System
 * 
 * This file provides:
 * 1. Re-exports of commonly used Lucide icons
 * 2. Emoji to Lucide icon mapping for migration
 * 3. Category-specific icon sets
 * 
 * Usage:
 *   import { SearchIcon, categoryIcons } from '@/components/icons'
 * 
 * Design System Reference: docs/ux/DESIGN-SYSTEM.md § 6
 */

// Re-export commonly used icons from lucide-vue-next
export {
  // Navigation & Search
  Search as SearchIcon,
  Home as HomeIcon,
  Menu as MenuIcon,
  X as CloseIcon,
  ChevronDown as ChevronDownIcon,
  ChevronRight as ChevronRightIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronUp as ChevronUpIcon,
  ArrowLeft as ArrowLeftIcon,
  ArrowRight as ArrowRightIcon,
  
  // Actions
  Plus as PlusIcon,
  Minus as MinusIcon,
  Check as CheckIcon,
  Copy as CopyIcon,
  Trash2 as TrashIcon,
  Edit3 as EditIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Share2 as ShareIcon,
  RefreshCw as RefreshIcon,
  MoreHorizontal as MoreIcon,
  MoreVertical as MoreVerticalIcon,
  Settings as SettingsIcon,
  
  // Status & Feedback
  AlertCircle as AlertIcon,
  AlertTriangle as WarningIcon,
  CheckCircle as SuccessIcon,
  Info as InfoIcon,
  Loader2 as LoaderIcon,
  Clock as ClockIcon,
  
  // Content Types
  FileText as DocumentIcon,
  File as FileIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Image as ImageIcon,
  Film as VideoIcon,
  Music as AudioIcon,
  
  // Communication
  MessageSquare as ChatIcon,
  Mail as MailIcon,
  Send as SendIcon,
  Bell as NotificationIcon,
  
  // Data & Analytics
  BarChart3 as ChartBarIcon,
  LineChart as ChartLineIcon,
  PieChart as ChartPieIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Database as DatabaseIcon,
  Activity as ActivityIcon,
  
  // Development
  Code as CodeIcon,
  Terminal as TerminalIcon,
  GitBranch as GitBranchIcon,
  Bug as BugIcon,
  Cpu as CpuIcon,
  Layers as LayersIcon,
  
  // Users & Teams
  User as UserIcon,
  Users as UsersIcon,
  UserPlus as UserPlusIcon,
  
  // UI Elements
  Eye as ViewIcon,
  EyeOff as HideIcon,
  Lock as LockIcon,
  Unlock as UnlockIcon,
  Star as StarIcon,
  Heart as HeartIcon,
  Bookmark as BookmarkIcon,
  Pin as PinIcon,
  
  // Media Controls
  Play as PlayIcon,
  Pause as PauseIcon,
  Square as StopIcon,
  SkipForward as SkipIcon,
  
  // Layout
  Maximize2 as MaximizeIcon,
  Minimize2 as MinimizeIcon,
  Columns as ColumnsIcon,
  Grid as GridIcon,
  List as ListIcon,
  
  // Misc
  Sparkles as SparklesIcon,
  Zap as ZapIcon,
  Target as TargetIcon,
  Award as AwardIcon,
  Calendar as CalendarIcon,
  Link as LinkIcon,
  ExternalLink as ExternalLinkIcon,
  Globe as GlobeIcon,
  Map as MapIcon,
  Compass as CompassIcon,
  
  // Financial
  DollarSign as DollarIcon,
  Wallet as WalletIcon,
  CreditCard as CreditCardIcon,
  Banknote as BanknoteIcon,
  
  // Presentation
  Presentation as PresentationIcon,
  LayoutTemplate as TemplateIcon,
  SlidersHorizontal as SlidersIcon,
  
  // Writing
  PenTool as PenIcon,
  Pencil as PencilIcon,
  Type as TypeIcon,
  AlignLeft as AlignLeftIcon,
  
  // Package/Box
  Package as PackageIcon,
  Box as BoxIcon,
  Archive as ArchiveIcon,
} from 'lucide-vue-next'

// Import types
import type { Component } from 'vue'

// ============================================
// Emoji to Lucide Icon Mapping
// ============================================

import {
  Search,
  PenTool,
  Database,
  BarChart3,
  Code,
  FileText,
  Package,
  Presentation,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Sparkles,
  MessageSquare,
  Target,
  Lightbulb,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Cpu,
  FolderOpen,
} from 'lucide-vue-next'

/**
 * Mapping from Emoji characters to Lucide icon components.
 * Use this to migrate Emoji icons to Lucide.
 * 
 * Usage:
 *   const IconComponent = emojiToLucide['🔍']
 *   <component :is="IconComponent" class="w-5 h-5" />
 */
export const emojiToLucide: Record<string, Component> = {
  // Search & Research
  '🔍': Search,
  '🔎': Search,
  
  // Writing & Documents
  '✍️': PenTool,
  '✍': PenTool,
  '📝': PenTool,
  '📄': FileText,
  '📃': FileText,
  '📑': FileText,
  
  // Data & Charts
  '📊': BarChart3,
  '📈': TrendingUp,
  '📉': TrendingDown,
  '🗃️': Database,
  '🗃': Database,
  
  // Development
  '💻': Code,
  '🖥️': Code,
  '🖥': Code,
  '⌨️': Code,
  '⌨': Code,
  
  // Package & Box
  '📦': Package,
  
  // Presentation
  '🎤': Presentation,
  '📽️': Presentation,
  '📽': Presentation,
  
  // Status
  '✅': CheckCircle,
  '⚠️': AlertTriangle,
  '⚠': AlertTriangle,
  '❌': AlertTriangle,
  '⏰': Clock,
  '⏱️': Clock,
  '⏱': Clock,
  
  // Activity & Process
  '⚡': Activity,
  '🔄': Activity,
  '♻️': Activity,
  
  // AI & Magic
  '✨': Sparkles,
  '🪄': Sparkles,
  '🔮': Sparkles,
  
  // Communication
  '💬': MessageSquare,
  '🗨️': MessageSquare,
  '🗨': MessageSquare,
  
  // Targets & Goals
  '🎯': Target,
  
  // Ideas
  '💡': Lightbulb,
  
  // Trends
  '🚀': ArrowUpRight,
  '📤': ArrowUpRight,
  '📥': ArrowDownRight,
  
  // Neutral
  '➖': Minus,
  
  // Tech
  '🧠': Cpu,
  '🤖': Cpu,
  
  // Files
  '📁': FolderOpen,
  '🗂️': FolderOpen,
  '🗂': FolderOpen,
}

// ============================================
// Category-specific Icon Sets
// ============================================

/**
 * Category icons for skill discovery and templates.
 * Replaces emoji-based categoryIcons.
 */
export const categoryIcons = {
  research: Search,
  writing: PenTool,
  data: Database,
  visualization: BarChart3,
  coding: Code,
  document: FileText,
  other: Package,
  presentation: Presentation,
  analysis: Activity,
} as const

/**
 * Get category icon component by category ID.
 */
export function getCategoryIcon(categoryId: string): Component {
  return categoryIcons[categoryId as keyof typeof categoryIcons] || Package
}

/**
 * Financial indicator icons.
 */
export const financialIcons = {
  up: TrendingUp,
  down: TrendingDown,
  neutral: Minus,
  bullish: ArrowUpRight,
  bearish: ArrowDownRight,
  warning: AlertTriangle,
  success: CheckCircle,
  pending: Clock,
} as const

/**
 * Status icons for workflow and execution.
 */
export const statusIcons = {
  active: Activity,
  success: CheckCircle,
  pending: Clock,
  error: AlertTriangle,
  inactive: Minus,
} as const

/**
 * Template type icons.
 */
export const templateIcons = {
  research: Search,
  writing: PenTool,
  data: Database,
  visualization: BarChart3,
  coding: Code,
  document: FileText,
  presentation: Presentation,
  default: Package,
} as const

// ============================================
// Helper Functions
// ============================================

/**
 * Convert an emoji to its Lucide icon equivalent.
 * Returns Package icon as fallback.
 */
export function getIconForEmoji(emoji: string): Component {
  return emojiToLucide[emoji] || Package
}

/**
 * Check if an emoji has a Lucide icon mapping.
 */
export function hasIconMapping(emoji: string): boolean {
  return emoji in emojiToLucide
}
