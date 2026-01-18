/**
 * Director Language - 用户主导语言系统
 * 
 * TokenDance 的文案规范：用户是导演，AI 是执行者
 * 避免 AI 助手式表达："我帮你...", "让我来..."
 * 使用执行式表达："执行中...", "等待确认..."
 */

export const DirectorLanguage = {
  // ============================================
  // 状态文案
  // ============================================
  status: {
    idle: '就绪',
    thinking: '分析中',
    planning: '规划中',
    executing: '执行中',
    waiting: '等待确认',
    paused: '已暂停',
    completed: '已完成',
    error: '执行失败',
    cancelled: '已取消',
  },
  
  // ============================================
  // 操作按钮
  // ============================================
  actions: {
    start: '开始执行',
    pause: '暂停',
    resume: '继续',
    stop: '停止',
    cancel: '取消',
    retry: '重试',
    confirm: '确认',
    reject: '拒绝',
    modify: '修改',
    approve: '批准',
    skip: '跳过',
    undo: '撤销',
    redo: '重做',
  },
  
  // ============================================
  // 进度提示
  // ============================================
  progress: {
    preparing: '准备中...',
    loading: '加载中...',
    processing: '处理中...',
    analyzing: '分析中...',
    generating: '生成中...',
    saving: '保存中...',
    uploading: '上传中...',
    downloading: '下载中...',
    
    // 带预估时间
    estimatedTime: (seconds: number) => {
      if (seconds < 60) return `预计 ${seconds}s`
      const minutes = Math.floor(seconds / 60)
      return `预计 ${minutes}min`
    },
    
    // 步骤进度
    stepProgress: (current: number, total: number) => 
      `步骤 ${current}/${total}`,
  },
  
  // ============================================
  // 人工介入 (HITL)
  // ============================================
  hitl: {
    title: '需要确认',
    waitingForApproval: '等待确认',
    autoApproveIn: (seconds: number) => `${seconds}s 后自动继续`,
    
    // 操作类型
    operationTypes: {
      file_write: '写入文件',
      file_delete: '删除文件',
      command_execute: '执行命令',
      api_call: '调用 API',
      data_modify: '修改数据',
      system_config: '系统配置',
    },
    
    // 风险等级
    riskLevels: {
      low: '低风险',
      medium: '中风险', 
      high: '高风险',
      critical: '关键操作',
    },
    
    // 提示文案
    prompts: {
      confirmContinue: '确认后继续执行',
      reviewChanges: '请审阅变更',
      approveOperation: '批准此操作',
      modifyAndContinue: '修改后继续',
    },
  },
  
  // ============================================
  // 执行阶段
  // ============================================
  phases: {
    understanding: '理解需求',
    planning: '制定计划',
    researching: '收集信息',
    executing: '执行任务',
    validating: '验证结果',
    completing: '完成收尾',
  },
  
  // ============================================
  // 结果反馈
  // ============================================
  results: {
    success: '执行成功',
    partialSuccess: '部分完成',
    failed: '执行失败',
    
    // 详细反馈
    filesCreated: (count: number) => `创建 ${count} 个文件`,
    filesModified: (count: number) => `修改 ${count} 个文件`,
    tasksCompleted: (count: number) => `完成 ${count} 个任务`,
    errorsOccurred: (count: number) => `发生 ${count} 个错误`,
  },
  
  // ============================================
  // 错误信息
  // ============================================
  errors: {
    networkError: '网络连接失败',
    timeout: '请求超时',
    permissionDenied: '权限不足',
    resourceNotFound: '资源未找到',
    validationFailed: '验证失败',
    unknownError: '未知错误',
    
    // 操作提示
    retryHint: '点击重试',
    contactSupport: '如问题持续，请联系支持',
  },
  
  // ============================================
  // 空状态
  // ============================================
  empty: {
    noTasks: '暂无任务',
    noHistory: '暂无历史记录',
    noFiles: '暂无文件',
    noResults: '暂无结果',
    
    // 引导文案
    getStarted: '开始新任务',
    createFirst: '创建第一个',
  },
  
  // ============================================
  // 工具提示
  // ============================================
  tooltips: {
    pause: '暂停执行 (Space)',
    resume: '继续执行 (Space)',
    stop: '停止执行 (Esc)',
    intervene: '请求介入 (I)',
    expand: '展开详情',
    collapse: '收起',
    copy: '复制',
    share: '分享',
    settings: '设置',
    help: '帮助',
  },
  
  // ============================================
  // 键盘快捷键说明
  // ============================================
  shortcuts: {
    togglePause: 'Space - 暂停/继续',
    requestIntervene: 'I - 请求介入',
    stopExecution: 'Esc - 停止执行',
    switchPanel: 'Tab - 切换面板',
    jumpToStep: '1-9 - 跳转步骤',
  },
} as const

// 类型导出
export type StatusKey = keyof typeof DirectorLanguage.status
export type ActionKey = keyof typeof DirectorLanguage.actions
export type PhaseKey = keyof typeof DirectorLanguage.phases

/**
 * 获取状态文案
 */
export function getStatusText(status: string): string {
  return DirectorLanguage.status[status as StatusKey] || status
}

/**
 * 获取操作文案
 */
export function getActionText(action: string): string {
  return DirectorLanguage.actions[action as ActionKey] || action
}

/**
 * 获取阶段文案
 */
export function getPhaseText(phase: string): string {
  return DirectorLanguage.phases[phase as PhaseKey] || phase
}
