<script setup lang="ts">
import { ref } from 'vue'
import ThinkingBlock from '@/components/execution/ThinkingBlock.vue'
import ToolCallBlock from '@/components/execution/ToolCallBlock.vue'
import ProgressIndicator from '@/components/execution/ProgressIndicator.vue'
import WorkingMemory from '@/components/execution/WorkingMemory.vue'
import type { ToolCall } from '@/components/execution/ToolCallBlock.vue'
import type { ProgressStep } from '@/components/execution/ProgressIndicator.vue'

// Mock data
const thinkingContent = ref(`分析用户需求: "调研AI Agent市场"
关键信息提取:
- 研究主题: AI Agent市场
- 时间范围: 2024年
- 需要的维度: 市场规模、主要玩家、技术趋势

执行计划:
1. 搜索市场规模数据
2. 搜索主要玩家信息
3. 搜索技术趋势报告
4. 聚合和验证信息
5. 生成结构化报告`)

const toolCalls = ref<ToolCall[]>([
  {
    id: '1',
    name: 'web_search',
    params: { query: 'AI Agent市场规模 2024', num_results: 5 },
    status: 'success',
    result: 'Found 5 results:\n1. Gartner: AI Agent市场规模达XXX亿美元\n2. IDC: 2024年增长XX%\n3. TechCrunch: 主要玩家分析\n...',
    duration: 1250,
  },
  {
    id: '2',
    name: 'read_url',
    params: { url: 'https://gartner.com/research/ai-agent-market', mode: 'markdown' },
    status: 'success',
    result: '# AI Agent Market Report 2024\n\n## Executive Summary\n\nThe AI agent market has experienced significant growth...',
    duration: 2340,
  },
  {
    id: '3',
    name: 'web_search',
    params: { query: 'AI Agent主要玩家 Anthropic OpenAI', num_results: 5 },
    status: 'running',
    duration: 850,
  },
  {
    id: '4',
    name: 'shell_command',
    params: { command: 'ls /workspace/data/', workspace_id: 'ws_123' },
    status: 'pending',
  },
])

const progressSteps = ref<ProgressStep[]>([
  { id: '1', label: '分析研究主题', status: 'completed' },
  { id: '2', label: '多源搜索 - 市场规模', status: 'completed' },
  { id: '3', label: '多源搜索 - 主要玩家', status: 'running', elapsed: 3 },
  { id: '4', label: '内容提取与摘要', status: 'pending' },
  { id: '5', label: '信息聚合', status: 'pending' },
  { id: '6', label: '生成结构化报告', status: 'pending' },
])

const taskPlan = `# Task Plan: AI Agent Market Research

## Phase 1: Data Collection
- [x] Search market size data
- [ ] Search major players
- [ ] Search technology trends

## Phase 2: Analysis
- [ ] Cross-validate information
- [ ] Identify patterns

## Phase 3: Report Generation
- [ ] Structure findings
- [ ] Add citations
- [ ] Generate final report`

const findings = `# Research Findings

## Market Size (Updated: 2024-01-13 18:00)
- Gartner报告显示2024年市场规模达XXX亿美元
- IDC预测年增长率XX%
- 来源: gartner.com/research/ai-agent-market

## Key Players
- Anthropic: Claude系列，强调安全性
- OpenAI: ChatGPT，市场领导者
- Google: Gemini，强大的多模态能力

## Technical Trends
1. Function Calling成为标配
2. 长上下文窗口竞赛
3. RAG技术普及`

const progress = `# Execution Progress

## 2024-01-13 17:55:00 - Task Started
User query: "调研AI Agent市场"

## 2024-01-13 17:55:12 - Step 1: Planning
Created research plan with 3 phases

## 2024-01-13 17:55:30 - Step 2: web_search
Query: "AI Agent市场规模 2024"
Status: SUCCESS
Duration: 1250ms
Result: Found 5 relevant sources

## 2024-01-13 17:56:00 - Step 3: read_url
URL: gartner.com/research/ai-agent-market
Status: SUCCESS
Duration: 2340ms
Extracted: 2500 words

## 2024-01-13 17:56:15 - Step 4: web_search
Query: "AI Agent主要玩家"
Status: RUNNING
Elapsed: 3s`
</script>

<template>
  <div class="min-h-screen bg-bg-primary">
    <!-- Header -->
    <header class="border-b border-border-default bg-bg-secondary">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <h1 class="text-2xl font-bold text-text-primary">TokenDance UI Components Demo</h1>
        <p class="text-sm text-text-secondary mt-1">
          Chain-of-Thought Visualization & Working Memory Pattern
        </p>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 py-8">
      <!-- Section 1: ThinkingBlock -->
      <section class="mb-12">
        <div class="mb-4">
          <h2 class="text-xl font-semibold text-text-primary mb-1">1. ThinkingBlock</h2>
          <p class="text-sm text-text-secondary">
            可折叠的思考过程块，支持流式输出和打字机效果
          </p>
        </div>
        <div class="bg-bg-secondary rounded-lg p-6">
          <ThinkingBlock :content="thinkingContent" :isStreaming="false" :defaultExpanded="true" />
        </div>
      </section>

      <!-- Section 2: ToolCallBlock -->
      <section class="mb-12">
        <div class="mb-4">
          <h2 class="text-xl font-semibold text-text-primary mb-1">2. ToolCallBlock</h2>
          <p class="text-sm text-text-secondary">
            工具调用可视化，展示不同状态（pending/running/success/error）
          </p>
        </div>
        <div class="bg-bg-secondary rounded-lg p-6 space-y-4">
          <ToolCallBlock
            v-for="toolCall in toolCalls"
            :key="toolCall.id"
            :toolCall="toolCall"
            :defaultExpanded="toolCall.status === 'success'"
          />
        </div>
      </section>

      <!-- Section 3: ProgressIndicator -->
      <section class="mb-12">
        <div class="mb-4">
          <h2 class="text-xl font-semibold text-text-primary mb-1">3. ProgressIndicator</h2>
          <p class="text-sm text-text-secondary">
            长任务进度指示器，适用于Deep Research和PPT生成
          </p>
        </div>
        <div class="bg-bg-secondary rounded-lg p-6">
          <ProgressIndicator title="深度研究：AI Agent市场" :steps="progressSteps" />
        </div>
      </section>

      <!-- Section 4: WorkingMemory -->
      <section class="mb-12">
        <div class="mb-4">
          <h2 class="text-xl font-semibold text-text-primary mb-1">4. WorkingMemory</h2>
          <p class="text-sm text-text-secondary">
            三文件工作法可视化（Manus核心架构）- Task Plan / Findings / Progress
          </p>
        </div>
        <div class="bg-bg-secondary rounded-lg p-6">
          <WorkingMemory :taskPlan="taskPlan" :findings="findings" :progress="progress" />
        </div>
      </section>

      <!-- Section 5: Complete Chat Example -->
      <section class="mb-12">
        <div class="mb-4">
          <h2 class="text-xl font-semibold text-text-primary mb-1">5. Complete Agent Response</h2>
          <p class="text-sm text-text-secondary">完整的Agent消息示例（含思考过程 + 工具调用）</p>
        </div>
        <div class="bg-bg-secondary rounded-lg p-6">
          <!-- Agent Avatar & Name -->
          <div class="flex items-center gap-3 mb-4">
            <div
              class="w-10 h-10 rounded-full bg-accent-gradient flex items-center justify-center flex-shrink-0"
            >
              <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <div class="font-semibold text-text-primary">TokenDance Agent</div>
              <div class="text-xs text-text-tertiary">Deep Research Mode</div>
            </div>
          </div>

          <!-- Thinking Block -->
          <ThinkingBlock :content="thinkingContent" :isStreaming="false" />

          <!-- Tool Calls -->
          <div class="space-y-3 mt-3">
            <ToolCallBlock
              v-for="toolCall in toolCalls.slice(0, 2)"
              :key="toolCall.id"
              :toolCall="toolCall"
            />
          </div>

          <!-- Final Response -->
          <div class="mt-4 p-4 rounded-lg bg-bg-tertiary/30 border border-border-default">
            <div class="prose prose-invert max-w-none">
              <p class="text-text-primary leading-relaxed">
                基于多源搜索和信息聚合，我已完成AI Agent市场的初步调研。主要发现如下：
              </p>
              <h3 class="text-text-primary">市场规模</h3>
              <p class="text-text-secondary">
                2024年全球AI Agent市场规模预计达到XXX亿美元，较去年增长XX%。
              </p>
              <h3 class="text-text-primary">主要玩家</h3>
              <ul class="text-text-secondary">
                <li>Anthropic - Claude系列，强调Constitutional AI</li>
                <li>OpenAI - ChatGPT，市场领导者</li>
                <li>Google - Gemini，多模态能力突出</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- Color Palette Reference -->
      <section class="mb-12">
        <div class="mb-4">
          <h2 class="text-xl font-semibold text-text-primary mb-1">Color Palette</h2>
          <p class="text-sm text-text-secondary">深色主题色彩系统（蓝紫渐变）</p>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <!-- Backgrounds -->
          <div class="space-y-2">
            <div class="text-xs font-medium text-text-secondary mb-2">Backgrounds</div>
            <div class="h-16 rounded-lg bg-bg-primary border border-border-default flex items-center justify-center">
              <span class="text-xs text-text-tertiary">Primary</span>
            </div>
            <div class="h-16 rounded-lg bg-bg-secondary border border-border-default flex items-center justify-center">
              <span class="text-xs text-text-tertiary">Secondary</span>
            </div>
            <div class="h-16 rounded-lg bg-bg-tertiary border border-border-default flex items-center justify-center">
              <span class="text-xs text-text-tertiary">Tertiary</span>
            </div>
          </div>

          <!-- Accent Colors -->
          <div class="space-y-2">
            <div class="text-xs font-medium text-text-secondary mb-2">Accent</div>
            <div
              class="h-16 rounded-lg bg-accent-primary flex items-center justify-center text-white font-medium"
            >
              Primary
            </div>
            <div
              class="h-16 rounded-lg bg-accent-hover flex items-center justify-center text-white font-medium"
            >
              Hover
            </div>
            <div
              class="h-16 rounded-lg bg-accent-gradient flex items-center justify-center text-white font-medium"
            >
              Gradient
            </div>
          </div>

          <!-- Text Colors -->
          <div class="space-y-2">
            <div class="text-xs font-medium text-text-secondary mb-2">Text</div>
            <div
              class="h-16 rounded-lg bg-bg-secondary border border-border-default flex items-center justify-center"
            >
              <span class="text-sm text-text-primary font-medium">Primary</span>
            </div>
            <div
              class="h-16 rounded-lg bg-bg-secondary border border-border-default flex items-center justify-center"
            >
              <span class="text-sm text-text-secondary">Secondary</span>
            </div>
            <div
              class="h-16 rounded-lg bg-bg-secondary border border-border-default flex items-center justify-center"
            >
              <span class="text-sm text-text-tertiary">Tertiary</span>
            </div>
          </div>

          <!-- Status Colors -->
          <div class="space-y-2">
            <div class="text-xs font-medium text-text-secondary mb-2">Status</div>
            <div class="h-16 rounded-lg bg-green-500/20 border border-green-500/30 flex items-center justify-center">
              <span class="text-sm text-green-400 font-medium">Success</span>
            </div>
            <div class="h-16 rounded-lg bg-red-500/20 border border-red-500/30 flex items-center justify-center">
              <span class="text-sm text-red-400 font-medium">Error</span>
            </div>
            <div class="h-16 rounded-lg bg-yellow-500/20 border border-yellow-500/30 flex items-center justify-center">
              <span class="text-sm text-yellow-400 font-medium">Warning</span>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="border-t border-border-default bg-bg-secondary py-6">
      <div class="max-w-7xl mx-auto px-6 text-center text-sm text-text-tertiary">
        TokenDance v0.1.0-MVP · Chain-of-Thought UI · Manus Working Memory Pattern
      </div>
    </footer>
  </div>
</template>
