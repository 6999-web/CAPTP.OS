<script setup>
import { computed, ref, watch, nextTick } from 'vue'

import { buildApiUrl, readApiPayload } from '../utils/api'
import { getTacticalScenarioById, tacticalScenarios } from '../data/tacticalScenarios'

const MAX_HISTORY_MESSAGES = 8
const scenario = ref('人质劫持危机处理')
const userInput = ref('')
const isReasoning = ref(false)
const scenarios = tacticalScenarios
const currentScenario = computed(() => getTacticalScenarioById(scenario.value))

const createSystemMessage = (selectedScenario) => ({
  role: 'system',
  content: `你是一名警务教官。现在开始实战决策推演。你将根据场景模拟现场反馈（如嫌疑人、围观群众的行为）。受训警员需要通过对话或行动指令来化解危机。请展示出逻辑严密、具备对抗性的现场反馈。当前场景：${selectedScenario}`
})

const createWelcomeMessage = (selectedScenario) => ({
  role: 'assistant',
  content: getTacticalScenarioById(selectedScenario).openingMessage
})

const chatHistory = ref([])
const displayHistory = ref([])
const chatContainer = ref(null)

const resetConversation = (selectedScenario = scenario.value) => {
  const openingMessage = createWelcomeMessage(selectedScenario)
  chatHistory.value = [
    createSystemMessage(selectedScenario),
    { role: 'assistant', content: openingMessage.content }
  ]
  displayHistory.value = [createWelcomeMessage(selectedScenario)]
}

const buildRequestMessages = () => {
  return chatHistory.value
    .filter((message) => message.role !== 'system')
    .slice(-MAX_HISTORY_MESSAGES)
}

resetConversation()

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

watch(displayHistory, () => scrollToBottom(), { deep: true })
watch(scenario, (nextScenario, previousScenario) => {
  if (nextScenario !== previousScenario) {
    resetConversation(nextScenario)
  }
})

const sendCommand = async () => {
  if (!userInput.value.trim() || isReasoning.value) return
  
  const userText = userInput.value.trim()
  userInput.value = ''
  
  chatHistory.value.push({ role: 'user', content: userText })
  displayHistory.value.push({ role: 'user', content: userText })
  
  isReasoning.value = true
  
  try {
    const res = await fetch(buildApiUrl('/api/tactical-chat'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: scenario.value,
        scenarioContext: currentScenario.value.context,
        messages: buildRequestMessages()
      })
    })
    
    const data = await readApiPayload(res)
    if (res.ok) {
      chatHistory.value.push({ role: 'assistant', content: data.result })
      displayHistory.value.push({ role: 'assistant', content: data.result })
    } else {
      displayHistory.value.push({ role: 'assistant', content: `ERROR: ${data.detail || '链路中继故障。'}` })
    }
  } catch (error) {
    displayHistory.value.push({ role: 'assistant', content: `ERROR: 网络接入失败。${error.message}` })
  } finally {
    isReasoning.value = false
  }
}
</script>

<template>
  <div class="tactical-container">
    <div class="page-header">
       <h1>🧠 执法决策推演终端 / TACTICAL AI</h1>
       <div class="scenario-chips">
          <div 
             v-for="s in scenarios" :key="s.id"
             class="chip" :class="{ active: scenario === s.id }"
             @click="scenario = s.id"
          >
             {{ s.icon }} {{ s.id }}
          </div>
       </div>
       <div class="scenario-brief">
          <div class="brief-label">SCENARIO BRIEF</div>
          <div class="brief-source">{{ currentScenario.sourceNote }}</div>
          <div class="brief-text">{{ currentScenario.context }}</div>
       </div>
    </div>

    <div class="terminal-frame">
       <div class="terminal-header">
          <div class="dots"><span class="red"></span><span class="yellow"></span><span class="green"></span></div>
          <div class="label">SECURE_LINK-GXP-ENCRYPTED (STP: ACTIVE)</div>
          <div class="node">NODE: HQ-VIRTUAL-09</div>
       </div>

       <div class="chat-viewport" ref="chatContainer">
          <div v-for="(msg, idx) in displayHistory" :key="idx" :class="['msg-block', msg.role]">
             <div class="meta">
                <span class="origin">{{ msg.role === 'user' ? '[UNIT_01]' : '[OPFOR/AI]' }}</span>
                <span class="timestamp">{{ new Date().toLocaleTimeString() }}</span>
             </div>
             <div class="bubble">
                <div v-if="msg.role === 'assistant'" class="typing-cursor"></div>
                <div class="text-content">{{ msg.content }}</div>
             </div>
          </div>
          <div v-if="isReasoning" class="msg-block assistant reasoning">
             <div class="bubble">
                <div class="dot-loader"><span></span><span></span><span></span></div>
             </div>
          </div>
       </div>

       <div class="terminal-input-bar">
          <span class="prompt-arrow">➜</span>
          <input 
             v-model="userInput" 
             @keyup.enter="sendCommand"
             type="text" 
             placeholder="输入你的处置口令、站位分工、风险判断或下一步决策..." 
             :disabled="isReasoning"
          />
          <button class="send-btn" @click="sendCommand" :disabled="!userInput.trim() || isReasoning">
             EXECUTE_CMD
          </button>
       </div>
    </div>
  </div>
</template>

<style scoped>
.tactical-container { animation: fadeIn 0.4s ease; height: 100%; display: flex; flex-direction: column; }

.page-header { margin-bottom: 30px; }
.scenario-chips { display: flex; gap: 15px; margin-top: 15px; }
.chip { background: #0a111c; border: 1px solid #1a3a5f; padding: 8px 15px; border-radius: 4px; font-size: 13px; color: var(--text-dim); cursor: pointer; transition: 0.3s; }
.chip:hover { border-color: var(--primary); color: #fff; }
.chip.active { background: rgba(0, 229, 255, 0.1); border-color: var(--primary); color: var(--primary); box-shadow: 0 0 10px rgba(0, 229, 255, 0.2); }
.scenario-brief {
  margin-top: 18px;
  padding: 16px 18px;
  border: 1px solid rgba(0, 229, 255, 0.15);
  background: linear-gradient(180deg, rgba(13, 23, 38, 0.85), rgba(9, 15, 24, 0.9));
  border-radius: 6px;
}
.brief-label {
  font-size: 10px;
  letter-spacing: 2px;
  color: #6fa8c6;
  font-family: monospace;
  margin-bottom: 8px;
}
.brief-source {
  font-size: 12px;
  color: #8eb3cf;
  margin-bottom: 10px;
}
.brief-text {
  font-size: 13px;
  line-height: 1.8;
  color: #d5e3f3;
  white-space: pre-wrap;
}

.terminal-frame {
  flex: 1;
  background: #000;
  border: 1px solid #1a3a5f;
  box-shadow: 0 0 40px rgba(0,0,0,0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 4px;
}

.terminal-header {
  background: #0d1726;
  padding: 10px 20px;
  border-bottom: 1px solid #1a3a5f;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dots { display: flex; gap: 6px; }
.dots span { width: 8px; height: 8px; border-radius: 50%; opacity: 0.6; }
.red { background: #ff4d4d; } .yellow { background: #ffc107; } .green { background: #00ff88; }
.terminal-header .label { font-size: 10px; font-family: monospace; color: #5c7f9d; }
.terminal-header .node { font-size: 10px; font-family: monospace; color: var(--primary); }

.chat-viewport {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 25px;
  background-image: linear-gradient(rgba(13, 23, 38, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(13, 23, 38, 0.4) 1px, transparent 1px);
  background-size: 40px 40px;
}

.msg-block { width: 100%; max-width: 85%; }
.msg-block.user { align-self: flex-end; }
.msg-block.assistant { align-self: flex-start; }

.meta { display: flex; gap: 15px; margin-bottom: 6px; font-size: 10px; font-family: monospace; color: #3d5875; }
.user .meta { justify-content: flex-end; }
.user .origin { color: var(--primary); font-weight: bold; }
.assistant .origin { color: #5c7694; font-weight: bold; }

.bubble { padding: 15px 20px; border-radius: 4px; font-size: 15px; line-height: 1.6; border: 1px solid transparent; position: relative; }
.user .bubble { background: rgba(0, 102, 204, 0.2); border-color: rgba(0, 102, 204, 0.6); color: #fff; }
.assistant .bubble { background: rgba(13, 23, 38, 0.8); border-color: #1a3a5f; color: #d0d7de; }

.typing-cursor { position: absolute; width: 6px; height: 18px; background: var(--primary); right: 10px; top: 15px; opacity: 0.6; animation: blink 0.8s infinite; display: none; }
.text-content { white-space: pre-wrap; font-family: inherit; }

.terminal-input-bar {
  background: #0a111c;
  padding: 20px;
  border-top: 1px solid #1a3a5f;
  display: flex;
  align-items: center;
  gap: 15px;
}
.prompt-arrow { color: var(--primary); font-weight: bold; font-family: monospace; }
.terminal-input-bar input {
  flex: 1;
  background: transparent;
  border: none;
  border-bottom: 1px solid #1a3a5f;
  padding: 10px 0;
  color: #fff;
  font-size: 16px;
  outline: none;
  transition: border 0.3s;
}
.terminal-input-bar input:focus { border-color: var(--primary); }

.send-btn {
  background: transparent;
  border: 1px solid var(--primary);
  color: var(--primary);
  padding: 10px 20px;
  font-family: monospace;
  font-weight: bold;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.3s;
}
.send-btn:hover:not(:disabled) { background: var(--primary); color: #000; box-shadow: 0 0 15px var(--primary); }

.dot-loader span { width: 6px; height: 6px; background: var(--primary); border-radius: 50%; display: inline-block; animation: dots 1s infinite alternate; }
.dot-loader span:nth-child(2) { animation-delay: 0.2s; }
.dot-loader span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dots { 0% { opacity: 0.2; transform: scale(0.8); } 100% { opacity: 1; transform: scale(1.2); } }
@keyframes blink { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }
</style>
