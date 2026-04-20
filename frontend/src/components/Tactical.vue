<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { buildApiUrl, readApiPayload } from '../utils/api'

const cases = ref([])
const selectedCaseId = ref('')
const currentQuestionIndex = ref(0)
const currentAnswer = ref('')
const isReasoning = ref(false)
const qaTimeline = ref([])
const canStartTest = ref(false)
const loadError = ref('')

const currentCase = computed(() => {
  return cases.value.find((item) => item.id === selectedCaseId.value) ?? null
})

const currentQuestion = computed(() => {
  if (!currentCase.value) return ''
  return currentCase.value.questions[currentQuestionIndex.value] ?? ''
})

const buildFallbackCases = () => ([
  {
    id: 'fallback-1',
    title: '竹山缉捕特大报复案（题库案例）',
    material: '1993年3月，湖北竹山发生特大报复杀人案件，嫌疑人手持板斧并绑缚爆炸物在铁索桥中央顽抗。捕歼小组采用化装接敌与突然突击方式实施抓捕，最终生擒嫌疑人并实现零附带伤亡。',
    questions: [
      '请先概括该案核心警情与第一处置目标。',
      '如果你是现场第一到场警力，你会如何做首轮口头控制和分工？',
      '在不强攻前提下，你如何创造接敌窗口并控制爆炸风险？',
      '结合本案，总结一条关键成功经验和一条可优化策略。'
    ],
    source: '前端兜底案例'
  }
])

const appendMessage = (role, content, kind = 'normal') => {
  qaTimeline.value.push({ role, content, kind, time: new Date().toLocaleTimeString() })
}

const resetSession = () => {
  qaTimeline.value = []
  currentQuestionIndex.value = 0
  currentAnswer.value = ''
  canStartTest.value = false

  if (!currentCase.value) return

  appendMessage(
    'assistant',
    `案例材料：${currentCase.value.title}\n\n${currentCase.value.material}`,
    'material'
  )

  if (currentCase.value.questions.length > 0) {
    appendMessage('assistant', `第 1 题（基础）：${currentCase.value.questions[0]}`, 'question')
  }
}

const loadCases = async () => {
  loadError.value = ''
  try {
    const response = await fetch(buildApiUrl('/api/tactical-cases'))
    const data = await readApiPayload(response)

    if (!response.ok || !Array.isArray(data.cases) || !data.cases.length) {
      throw new Error(data.detail || '题库接口返回为空')
    }

    cases.value = data.cases
  } catch (error) {
    cases.value = buildFallbackCases()
    loadError.value = `题库读取失败，已切换到前端兜底案例：${error.message}`
  }

  selectedCaseId.value = cases.value[0]?.id || ''
  resetSession()
}

const sendAnswer = async () => {
  const answer = currentAnswer.value.trim()
  if (!answer || isReasoning.value || !currentCase.value || canStartTest.value) return

  appendMessage('user', answer, 'answer')
  currentAnswer.value = ''
  isReasoning.value = true

  try {
    const scenarioContext = `${currentCase.value.material}\n\n当前题目：${currentQuestion.value}`
    const messages = qaTimeline.value.map((item) => ({ role: item.role, content: item.content }))

    const response = await fetch(buildApiUrl('/api/tactical-chat'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: currentCase.value.title,
        scenarioContext,
        messages
      })
    })

    const data = await readApiPayload(response)
    if (!response.ok) {
      throw new Error(data.detail || '推演链路异常')
    }

    appendMessage('assistant', data.result || '已记录你的处置思路。', 'feedback')
  } catch (error) {
    appendMessage('assistant', `点评失败：${error.message}`, 'feedback')
  } finally {
    isReasoning.value = false
  }

  const nextIndex = currentQuestionIndex.value + 1
  if (nextIndex < currentCase.value.questions.length) {
    currentQuestionIndex.value = nextIndex
    const stageName = nextIndex === 1 ? '进阶' : (nextIndex === 2 ? '实战' : '复盘')
    appendMessage('assistant', `第 ${nextIndex + 1} 题（${stageName}）：${currentCase.value.questions[nextIndex]}`, 'question')
  } else {
    canStartTest.value = true
    appendMessage('assistant', '所有问答已完成。你可以点击“开启测试”进入测试模式。', 'done')
  }
}

const startTest = () => {
  appendMessage(
    'assistant',
    `测试已开启：请在 3 分钟内给出《${currentCase.value?.title || '当前案例'}》的完整处置流程（口头控制、站位分工、升级条件、证据固定）。`,
    'test'
  )
}

watch(selectedCaseId, () => {
  if (selectedCaseId.value) {
    resetSession()
  }
})

onMounted(loadCases)
</script>

<template>
  <div class="tactical-container">
    <div class="header-row">
      <div>
        <h1>决策推演 / Tactical Decision</h1>
        <p class="subtitle">先展示案例材料，再进行由浅入深的一问一答推演。</p>
      </div>
      <div class="case-selector">
        <label for="caseSelect">案例选择</label>
        <select id="caseSelect" v-model="selectedCaseId">
          <option v-for="item in cases" :key="item.id" :value="item.id">{{ item.title }}</option>
        </select>
      </div>
    </div>

    <div v-if="loadError" class="warning-banner">{{ loadError }}</div>

    <div class="terminal-frame">
      <div class="terminal-header">
        <span class="dot red"></span>
        <span class="dot yellow"></span>
        <span class="dot green"></span>
        <span class="terminal-title">TACTICAL LINK / CASE DRIVEN QA</span>
      </div>

      <div class="timeline">
        <div
          v-for="(item, idx) in qaTimeline"
          :key="`${idx}-${item.time}`"
          class="msg"
          :class="[item.role, item.kind]"
        >
          <div class="meta">
            <span>{{ item.role === 'user' ? '学员' : '教官AI' }}</span>
            <span>{{ item.time }}</span>
          </div>
          <div class="content">{{ item.content }}</div>
        </div>

        <div v-if="isReasoning" class="msg assistant feedback">
          <div class="meta"><span>教官AI</span><span>处理中</span></div>
          <div class="content">正在生成点评...</div>
        </div>
      </div>

      <div class="input-row">
        <input
          v-model="currentAnswer"
          :disabled="isReasoning || canStartTest"
          @keyup.enter="sendAnswer"
          placeholder="输入当前题目的处置思路"
        >
        <button class="btn" :disabled="isReasoning || !currentAnswer.trim() || canStartTest" @click="sendAnswer">
          提交回答
        </button>
        <button class="btn test-btn" :disabled="!canStartTest" @click="startTest">
          开启测试
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tactical-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.header-row {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
}

.subtitle {
  margin: 4px 0 0;
  color: #90aac4;
}

.case-selector {
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.case-selector label {
  font-size: 12px;
  color: #8fb3d0;
}

.case-selector select {
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 229, 255, 0.28);
  background: rgba(9, 16, 28, 0.85);
  color: #e0f2ff;
}

.warning-banner {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 151, 112, 0.4);
  background: rgba(255, 112, 67, 0.12);
  color: #ffc7b0;
}

.terminal-frame {
  flex: 1;
  min-height: 0;
  border: 1px solid rgba(0, 229, 255, 0.22);
  border-radius: 10px;
  overflow: hidden;
  background: rgba(6, 11, 20, 0.82);
  display: flex;
  flex-direction: column;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 229, 255, 0.15);
  background: linear-gradient(90deg, rgba(7, 18, 31, 0.95), rgba(11, 26, 46, 0.9));
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.red { background: #ff5f57; }
.yellow { background: #ffbd2f; }
.green { background: #28c840; }

.terminal-title {
  margin-left: 8px;
  font-size: 12px;
  color: #88b8d8;
  letter-spacing: 1px;
}

.timeline {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.msg {
  max-width: min(900px, 95%);
  border-radius: 10px;
  border: 1px solid rgba(0, 229, 255, 0.12);
  background: rgba(9, 16, 27, 0.8);
  padding: 10px 12px;
}

.msg.user {
  align-self: flex-end;
  border-color: rgba(0, 161, 255, 0.35);
  background: rgba(0, 96, 168, 0.24);
}

.msg.material {
  border-color: rgba(0, 229, 255, 0.28);
  background: rgba(0, 114, 201, 0.14);
}

.msg.question {
  border-color: rgba(36, 215, 255, 0.42);
  background: rgba(0, 229, 255, 0.1);
}

.msg.done,
.msg.test {
  border-color: rgba(69, 255, 180, 0.36);
  background: rgba(16, 120, 92, 0.22);
}

.meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #8eb4d2;
  margin-bottom: 6px;
}

.content {
  white-space: pre-wrap;
  line-height: 1.65;
  color: #e3f3ff;
}

.input-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid rgba(0, 229, 255, 0.16);
  background: rgba(9, 16, 27, 0.9);
}

.input-row input {
  width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(0, 229, 255, 0.2);
  background: rgba(5, 12, 22, 0.85);
  color: #e5f5ff;
  padding: 10px 12px;
}

.btn {
  white-space: nowrap;
}

.test-btn {
  border-color: #45ffb4;
  background: rgba(69, 255, 180, 0.1);
  color: #9effdc;
}

@media (max-width: 980px) {
  .header-row {
    flex-direction: column;
    align-items: stretch;
  }

  .case-selector {
    min-width: 0;
  }

  .input-row {
    grid-template-columns: 1fr;
  }
}
</style>
