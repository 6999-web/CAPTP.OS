<template>
  <div class="overview-container">
    <div class="header-section">
      <h1>📊 终端态势指标 / TERMINAL STATUS</h1>
      <p class="subtitle">AI 赋能警务实战训练数据实时监控中心</p>
    </div>
    
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="label">在线训练终端 / TERMINALS</div>
        <div class="value">42 <span class="trend up">+4.2%</span></div>
        <div class="sub-label">系统负载正常 / STABLE</div>
        <div class="progress-bar"><div class="fill" style="width: 42%;"></div></div>
      </div>
      <div class="metric-card highlight">
        <div class="label">本月累计评分 / TOTAL EVALS</div>
        <div class="value">1,208 <span class="trend up">+12%</span></div>
        <div class="sub-label">累计处理视频 5,290 帧</div>
        <div class="progress-bar"><div class="fill" style="width: 78%;"></div></div>
      </div>
      <div class="metric-card">
        <div class="label">算法评估偏差 / AI DRIFT</div>
        <div class="value">1.5% <span class="trend down">-0.2%</span></div>
        <div class="sub-label">检测精度: 98.2% P/R</div>
        <div class="progress-bar"><div class="fill alert" style="width: 15%;"></div></div>
      </div>
    </div>
    
    <div class="panel main-display">
      <div class="frame-corners"></div>
      <div class="display-header">实时演算流预览 / LIVE INFERENCE STREAM</div>
      <div class="banner-wrapper">
         <div class="scanning-line"></div>
         <img src="https://img.freepik.com/free-photo/police-man-suit-with-gun_23-2148122612.jpg" alt="Police AI" class="banner-img">
         <div class="overlay-text">NODE: GXP-HQ-01 | ENCRYPTED LINK</div>
         <div class="data-overlays">
            <div class="box">POSE: ESTABLISHED</div>
            <div class="box">OBJ: WEAPON_HANDGUN</div>
            <div class="box">LEVEL: ACTIVE</div>
         </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview-container { animation: fadeIn 0.5s ease-in; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.header-section { margin-bottom: 40px; }
.subtitle { color: #5c7f9d; font-size: 14px; font-weight: 500; letter-spacing: 2px; }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.metric-card {
  background: rgba(13, 23, 38, 0.6);
  border: 1px solid rgba(0, 229, 255, 0.1);
  padding: 30px;
  border-radius: 4px;
  position: relative;
  transition: all 0.3s;
}

.metric-card:hover {
  border-color: var(--primary);
  background: rgba(0, 229, 255, 0.05);
  box-shadow: 0 0 20px rgba(0, 229, 255, 0.1);
}

.metric-card.highlight {
  background: linear-gradient(135deg, rgba(0, 102, 204, 0.2) 0%, rgba(13, 23, 38, 0.6) 100%);
  border-color: rgba(0, 102, 204, 0.5);
}

.label { color: #5c7694; font-size: 11px; letter-spacing: 2px; font-weight: 700; }
.value { font-size: 42px; font-weight: 900; color: #fff; margin: 10px 0; display: flex; align-items: baseline; gap: 15px; }
.trend { font-size: 13px; font-weight: 600; padding: 2px 8px; border-radius: 20px; font-family: monospace; }
.sub-label { color: #3d5875; font-size: 12px; margin-bottom: 15px; }

.progress-bar { height: 4px; background: rgba(0,0,0,0.3); border-radius: 2px; overflow: hidden; }
.progress-bar .fill { height: 100%; background: var(--primary); border-radius: 2px; box-shadow: 0 0 10px var(--primary); }
.progress-bar .fill.alert { background: #ff4d4d; box-shadow: 0 0 10px #ff4d4d; }

.main-display { padding: 0; background: #000; border: 1px solid #1a3a5f; }
.display-header { background: #0d1726; padding: 10px 20px; font-size: 11px; color: var(--primary); letter-spacing: 2px; border-bottom: 1px solid #1a3a5f; }

.banner-wrapper { position: relative; height: 450px; overflow: hidden; }
.banner-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; mix-blend-mode: luminosity; }

.scanning-line {
  position: absolute; top:0; left:0; width: 100%; height: 4px;
  background: linear-gradient(180deg, transparent, var(--primary), transparent);
  box-shadow: 0 0 20px var(--primary);
  animation: scan 4s infinite linear;
  z-index: 10;
}

@keyframes scan { 0% { top: -10%; } 100% { top: 110%; } }

.overlay-text { position: absolute; bottom: 20px; left: 20px; font-family: monospace; font-size: 11px; color: var(--primary); text-shadow: 0 0 5px #000; }

.data-overlays { position: absolute; top: 20px; right: 20px; display: flex; flex-direction: column; gap: 10px; }
.data-overlays .box {
  background: rgba(0, 229, 255, 0.1);
  border: 1px solid var(--primary);
  color: var(--primary);
  padding: 5px 12px;
  font-size: 10px;
  font-weight: bold;
  backdrop-filter: blur(5px);
  text-transform: uppercase;
}

.frame-corners::before, .frame-corners::after {
  content: ''; position: absolute; width: 20px; height: 20px; border: 2px solid var(--primary); z-index: 20;
}
.frame-corners::before { top: 10px; left: 10px; border-right: 0; border-bottom: 0; }
.frame-corners::after { bottom: 10px; right: 10px; border-left: 0; border-top: 0; }
</style>
