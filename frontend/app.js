const state = {
  characters: [],
  backgrounds: [],
  voices: [],
  selChar1: null,
  selChar2: null,
  selBg: null,
  currentComposite: null,
  currentDialogue: null,
  selVoice1: null,
  selVoice2: null,
  voiceLine1: null,
  voiceLine2: null,
  timing: { dialogueSec: 0, voiceSec: 0, videoSec: 0 },
  targetDuration: 20,
};

function fmtSec(sec) {
  if (sec == null) return "-";
  if (sec < 60) return `${sec.toFixed(1)}초`;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}분 ${s}초`;
}

// ---------- api helpers ----------
async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function patchJSON(url, body) {
  const res = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function del(url) {
  const res = await fetch(url, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function mediaUrl(path) {
  return `/media/${path}`;
}

// ---------- navigation ----------
function setupNav() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.target).classList.add("active");
      if (btn.dataset.target === "section-dialogue") renderDialogueSummary();
      if (btn.dataset.target === "section-video") renderVideoSummary();
    });
  });
}

// ---------- voice pick grid ----------
function renderVoicePickGrid(containerId, selectedItem, onSelect) {
  const el = document.getElementById(containerId);
  el.innerHTML = "";
  state.voices.forEach((item) => {
    const card = document.createElement("div");
    card.className = "pick-card" + (selectedItem && selectedItem.id === item.id ? " selected" : "");
    card.innerHTML = `<div class="thumb-audio"><button type="button" class="play-btn">▶</button></div><div class="pick-name">${item.name}</div>`;
    card.addEventListener("click", () => onSelect(item));
    card.querySelector(".play-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      new Audio(mediaUrl(item.reference_audio_path)).play();
    });
    el.appendChild(card);
  });
}

function pickVoice1(item) {
  state.selVoice1 = item;
  renderVoicePickGrid("pick-voice1", state.selVoice1, pickVoice1);
}
function pickVoice2(item) {
  state.selVoice2 = item;
  renderVoicePickGrid("pick-voice2", state.selVoice2, pickVoice2);
}

// ---------- characters ----------
async function loadCharacters() {
  state.characters = await getJSON("/api/characters");
  renderCharacterGrid();
  renderCharSelectionStatus();
}

function pickChar1(item) {
  state.selChar1 = state.selChar1?.id === item.id ? null : item;
  renderCharacterGrid();
  renderCharSelectionStatus();
  tryShowComposite();
}
function pickChar2(item) {
  state.selChar2 = state.selChar2?.id === item.id ? null : item;
  renderCharacterGrid();
  renderCharSelectionStatus();
  tryShowComposite();
}

function renderCharSelectionStatus() {
  const el = document.getElementById("char-selection-status");
  el.innerHTML = `인물1: <b>${state.selChar1 ? state.selChar1.name : "미선택"}</b> · 인물2: <b>${state.selChar2 ? state.selChar2.name : "미선택"}</b>`;
}

function renderCharacterGrid() {
  const el = document.getElementById("character-grid");
  el.innerHTML = "";
  state.characters.forEach((c) => {
    const isChar1 = state.selChar1?.id === c.id;
    const isChar2 = state.selChar2?.id === c.id;
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${mediaUrl(c.image_path)}" alt="${c.name}" />
      <div class="card-body">
        <div class="card-name">${c.name} <span style="color:#9aa1b0">(${c.gender})</span></div>
        <div class="card-desc">${c.description}</div>
        <div class="select-row">
          <button class="select-btn${isChar1 ? " active" : ""}" data-slot="1" ${isChar2 ? "disabled" : ""}>인물1로</button>
          <button class="select-btn${isChar2 ? " active" : ""}" data-slot="2" ${isChar1 ? "disabled" : ""}>인물2로</button>
        </div>
        <button class="card-del" data-id="${c.id}">삭제</button>
      </div>`;
    card.querySelector('[data-slot="1"]').addEventListener("click", () => pickChar1(c));
    card.querySelector('[data-slot="2"]').addEventListener("click", () => pickChar2(c));
    card.querySelector(".card-del").addEventListener("click", async (e) => {
      await del(`/api/characters/${e.target.dataset.id}`);
      await loadCharacters();
    });
    el.appendChild(card);
  });
}

// ---------- backgrounds ----------
async function loadBackgrounds() {
  state.backgrounds = await getJSON("/api/backgrounds");
  renderBackgroundGrid();
  renderBgSelectionStatus();
}

function pickBg(item) {
  state.selBg = state.selBg?.id === item.id ? null : item;
  renderBackgroundGrid();
  renderBgSelectionStatus();
  tryShowComposite();
}

function renderBgSelectionStatus() {
  document.getElementById("bg-selection-status").innerHTML =
    `배경: <b>${state.selBg ? state.selBg.name : "미선택"}</b>`;
}

function renderBackgroundGrid() {
  const el = document.getElementById("background-grid");
  el.innerHTML = "";
  state.backgrounds.forEach((b) => {
    const isSelected = state.selBg?.id === b.id;
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${mediaUrl(b.image_path)}" alt="${b.name}" />
      <div class="card-body">
        <div class="card-name">${b.name}</div>
        <div class="card-desc">${b.description}</div>
        <div class="select-row">
          <button class="select-btn${isSelected ? " active" : ""}">배경으로 선택</button>
        </div>
        <button class="card-del" data-id="${b.id}">삭제</button>
      </div>`;
    card.querySelector(".select-btn").addEventListener("click", () => pickBg(b));
    card.querySelector(".card-del").addEventListener("click", async (e) => {
      await del(`/api/backgrounds/${e.target.dataset.id}`);
      await loadBackgrounds();
    });
    el.appendChild(card);
  });
}

// ---------- voices ----------
async function loadVoices() {
  state.voices = await getJSON("/api/voices");
  renderVoicePickGrid("pick-voice1", state.selVoice1, pickVoice1);
  renderVoicePickGrid("pick-voice2", state.selVoice2, pickVoice2);
}

// ---------- library import ----------
async function loadImportLists() {
  const data = await getJSON("/api/library-import/scan");

  const charEl = document.getElementById("import-character-list");
  charEl.innerHTML = "";
  data.images.forEach((fname) => {
    const item = document.createElement("div");
    item.className = "import-item";
    item.innerHTML = `<span>${fname}</span><button>인물로</button>`;
    item.querySelector("button").addEventListener("click", async () => {
      const name = prompt("인물 이름", fname.slice(0, 12));
      if (!name) return;
      const description = prompt("설명 (영문 권장, 예: a young man in a dark sweater)", "");
      const gender = prompt("성별 (male/female/robot/other/unspecified)", "unspecified") || "unspecified";
      await postJSON("/api/library-import/character", { filename: fname, name, description, gender });
      await loadCharacters();
    });
    charEl.appendChild(item);
  });

  const bgEl = document.getElementById("import-background-list");
  bgEl.innerHTML = "";
  data.images.forEach((fname) => {
    const item = document.createElement("div");
    item.className = "import-item";
    item.innerHTML = `<span>${fname}</span><button>배경으로</button>`;
    item.querySelector("button").addEventListener("click", async () => {
      const name = prompt("배경 이름", fname.slice(0, 12));
      if (!name) return;
      const description = prompt("설명 (영문 권장, 예: traditional Korean hanok alley)", "");
      await postJSON("/api/library-import/background", { filename: fname, name, description });
      await loadBackgrounds();
    });
    bgEl.appendChild(item);
  });

  const compEl = document.getElementById("import-composite-list");
  compEl.innerHTML = "";
  data.images.forEach((fname) => {
    const item = document.createElement("div");
    item.className = "import-item";
    item.innerHTML = `<span>${fname}</span><button>합성으로 등록</button>`;
    item.querySelector("button").addEventListener("click", async () => {
      if (!state.selChar1 || !state.selChar2 || !state.selBg) {
        alert("먼저 인물1, 인물2, 배경을 선택하세요.");
        return;
      }
      await postJSON("/api/library-import/composite", {
        filename: fname,
        character1_id: state.selChar1.id,
        character2_id: state.selChar2.id,
        background_id: state.selBg.id,
      });
      await tryShowComposite();
    });
    compEl.appendChild(item);
  });

  const voiceEl = document.getElementById("import-voice-list");
  voiceEl.innerHTML = "";
  data.audio.forEach((fname) => {
    const item = document.createElement("div");
    item.className = "import-item";
    item.innerHTML = `<span>${fname}</span><button>목소리로</button>`;
    item.querySelector("button").addEventListener("click", async () => {
      const name = prompt("목소리 이름", fname.slice(0, 12));
      if (!name) return;
      const gender = prompt("성별 (male/female/unspecified)", "unspecified") || "unspecified";
      await postJSON("/api/library-import/voice", { filename: fname, name, gender });
      await loadVoices();
    });
    voiceEl.appendChild(item);
  });
}

// ---------- composites ----------
async function tryShowComposite() {
  if (!state.selChar1 || !state.selChar2 || !state.selBg) {
    state.currentComposite = null;
    renderDialogueSummary();
    return;
  }
  const qs = `character1_id=${state.selChar1.id}&character2_id=${state.selChar2.id}&background_id=${state.selBg.id}`;
  try {
    state.currentComposite = await getJSON(`/api/composites/find?${qs}`);
  } catch (err) {
    state.currentComposite = null;
  }
  renderDialogueSummary();
}

// ---------- dialogue ----------
function renderDialogueSummary() {
  const el = document.getElementById("dialogue-composite-summary");

  document.getElementById("dialogue-char1-label").textContent =
    `인물1 (${state.selChar1 ? state.selChar1.name : "?"})`;
  document.getElementById("dialogue-char2-label").textContent =
    `인물2 (${state.selChar2 ? state.selChar2.name : "?"})`;

  if (!state.selChar1 || !state.selChar2) {
    el.innerHTML = "1단계에서 인물1/인물2를 선택하세요.";
    return;
  }
  if (!state.selBg) {
    el.innerHTML = `<b>${state.selChar1.name} + ${state.selChar2.name}</b> 선택됨. 2단계에서 배경도 선택하면 합성 이미지를 보여줍니다.`;
    return;
  }
  if (!state.currentComposite) {
    el.innerHTML = `이 조합(${state.selChar1.name} + ${state.selChar2.name} + ${state.selBg.name})으로 등록된 합성 이미지가 없습니다. 아래 "가져오기"로 등록하세요.`;
    return;
  }
  el.innerHTML = `
    <div class="summary-row">
      <img src="${mediaUrl(state.currentComposite.image_path)}" />
      <div><b>선택된 합성:</b> ${state.selChar1.name} + ${state.selChar2.name} + ${state.selBg.name}</div>
    </div>`;
}

function renderDialogueTiming() {
  const el = document.getElementById("dialogue-timing");
  el.textContent = state.timing.dialogueSec > 0 ? `대사 생성 누적 소요 시간: ${fmtSec(state.timing.dialogueSec)}` : "";
}

async function loadKeywordPresets() {
  const presets = await getJSON("/api/dialogues/keyword-presets");
  const el = document.getElementById("keyword-presets");
  el.innerHTML = "";
  presets.forEach((kw) => {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = kw;
    chip.addEventListener("click", () => {
      document.getElementById("keyword-input").value = kw;
    });
    el.appendChild(chip);
  });
}

function setupDurationChips() {
  document.querySelectorAll(".duration-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.targetDuration = parseInt(chip.dataset.duration, 10);
      document.querySelectorAll(".duration-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupDurationChips();
  document.getElementById("btn-generate-line1").addEventListener("click", async () => {
    if (!state.selChar1 || !state.selChar2) {
      alert("먼저 1단계에서 인물1, 인물2를 선택하세요.");
      return;
    }
    const keyword = document.getElementById("keyword-input").value.trim();
    if (!keyword) {
      alert("키워드를 입력하세요.");
      return;
    }
    const btn = document.getElementById("btn-generate-line1");
    btn.disabled = true;
    btn.textContent = "생성 중...";
    const t0 = Date.now();
    try {
      const result = await postJSON("/api/dialogues", {
        keyword,
        character1_id: state.selChar1.id,
        character2_id: state.selChar2.id,
        target_duration_sec: state.targetDuration,
      });
      state.currentDialogue = result;
      document.getElementById("line1-text").value = result.line1;
      document.getElementById("line2-text").value = result.line2;
      state.timing.dialogueSec += (Date.now() - t0) / 1000;
      renderDialogueTiming();
    } catch (err) {
      alert("대사 생성 실패: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "인물1 대사 생성";
    }
  });

  document.getElementById("btn-generate-line2").addEventListener("click", async () => {
    if (!state.selChar1 || !state.selChar2) {
      alert("먼저 1단계에서 인물1, 인물2를 선택하세요.");
      return;
    }
    const line1 = document.getElementById("line1-text").value.trim();
    if (!line1) {
      alert("먼저 인물1의 대사를 생성하거나 입력하세요.");
      return;
    }
    const btn = document.getElementById("btn-generate-line2");
    btn.disabled = true;
    btn.textContent = "생성 중...";
    const t0 = Date.now();
    try {
      if (!state.currentDialogue) {
        state.currentDialogue = await postJSON("/api/dialogues/manual", {
          character1_id: state.selChar1.id,
          character2_id: state.selChar2.id,
          line1,
          line2: "",
        });
      }
      const result = await postJSON(`/api/dialogues/${state.currentDialogue.id}/reply`, {
        line1,
        background_id: state.selBg ? state.selBg.id : null,
        target_duration_sec: state.targetDuration,
      });
      state.currentDialogue = result;
      document.getElementById("line2-text").value = result.line2;
      state.timing.dialogueSec += (Date.now() - t0) / 1000;
      renderDialogueTiming();
    } catch (err) {
      alert("답변 생성 실패: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "인물2 대사 생성 (답변)";
    }
  });

  document.getElementById("btn-save-dialogue").addEventListener("click", async () => {
    if (!state.selChar1 || !state.selChar2) {
      alert("먼저 1단계에서 인물1, 인물2를 선택하세요.");
      return;
    }
    const line1 = document.getElementById("line1-text").value;
    const line2 = document.getElementById("line2-text").value;
    if (state.currentDialogue) {
      state.currentDialogue = await patchJSON(`/api/dialogues/${state.currentDialogue.id}`, {
        line1,
        line2,
        background_id: state.selBg ? state.selBg.id : null,
      });
    } else {
      state.currentDialogue = await postJSON("/api/dialogues/manual", {
        character1_id: state.selChar1.id,
        character2_id: state.selChar2.id,
        line1,
        line2,
      });
    }
    alert("저장되었습니다.");
  });
});

// ---------- voice lines ----------
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-generate-voices").addEventListener("click", async () => {
    if (!state.currentDialogue || !state.currentDialogue.line1 || !state.currentDialogue.line2) {
      alert("먼저 3단계에서 인물1, 인물2 대사를 모두 생성/저장하세요.");
      return;
    }
    if (!state.selVoice1 || !state.selVoice2) {
      alert("인물1, 인물2 목소리를 모두 선택하세요.");
      return;
    }
    const btn = document.getElementById("btn-generate-voices");
    btn.disabled = true;
    btn.textContent = "생성 중...";
    const t0 = Date.now();
    try {
      // sequential, not Promise.all: ComfyUI only has one GPU and processes one job at a time
      // anyway, and submitting both at once risked the two TTS calls interleaving in ComfyUI
      const vl1 = await postJSON("/api/voice-lines", { text: state.currentDialogue.line1, voice_id: state.selVoice1.id });
      const vl2 = await postJSON("/api/voice-lines", { text: state.currentDialogue.line2, voice_id: state.selVoice2.id });
      state.voiceLine1 = vl1;
      state.voiceLine2 = vl2;
      state.timing.voiceSec = (Date.now() - t0) / 1000;
      const box = document.getElementById("voice-result");
      box.innerHTML = `
        <p><b>인물1</b> (${vl1.cached ? "캐시됨" : "새로 생성"}): ${state.currentDialogue.line1}</p>
        <audio controls src="${mediaUrl(vl1.audio_path)}"></audio>
        <p><b>인물2</b> (${vl2.cached ? "캐시됨" : "새로 생성"}): ${state.currentDialogue.line2}</p>
        <audio controls src="${mediaUrl(vl2.audio_path)}"></audio>`;
      document.getElementById("voice-timing").textContent = `목소리 생성 소요 시간: ${fmtSec(state.timing.voiceSec)}`;
    } catch (err) {
      alert("목소리 생성 실패: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "목소리 생성";
    }
  });
});

// ---------- video ----------
function renderVideoSummary() {
  const el = document.getElementById("video-summary");
  const parts = [];
  if (state.currentComposite) {
    parts.push(`<img src="${mediaUrl(state.currentComposite.image_path)}" />`);
  }
  if (state.currentDialogue) {
    parts.push(`<div><b>대사:</b><br>${state.currentDialogue.line1}<br>${state.currentDialogue.line2}</div>`);
  }
  if (state.voiceLine1 && state.voiceLine2) {
    parts.push(`<div><b>목소리:</b> ${state.selVoice1.name} / ${state.selVoice2.name}</div>`);
    parts.push(`<div><b>영상 길이:</b> 목소리 길이에 맞춰 자동 결정됩니다</div>`);
  }
  el.innerHTML = parts.length
    ? `<div class="summary-row">${parts.join("")}</div>`
    : "3~4단계를 먼저 완료하세요.";
}

async function pollVideoJob(jobId) {
  const progressBox = document.getElementById("video-progress");
  const progressText = document.getElementById("video-progress-text");
  progressBox.style.display = "flex";

  const startedAt = Date.now();
  let latestStatus = "queued";
  const tick = () => {
    const elapsed = (Date.now() - startedAt) / 1000;
    const label = latestStatus === "running" ? "영상 생성 중" : "대기 중";
    progressText.textContent = `${label}... ${fmtSec(elapsed)} 경과`;
  };
  const timerId = setInterval(tick, 1000);
  tick();

  try {
    while (true) {
      const job = await getJSON(`/api/videos/jobs/${jobId}`);
      latestStatus = job.status;
      if (job.status === "done") {
        const videoPath = job.result.video_path;
        const durationSec = job.result.duration_sec;
        state.timing.videoSec = job.elapsed_sec != null ? job.elapsed_sec : (Date.now() - startedAt) / 1000;
        const total = state.timing.dialogueSec + state.timing.voiceSec + state.timing.videoSec;
        const box = document.getElementById("video-result");
        box.innerHTML = `
          <video controls src="${mediaUrl(videoPath)}"></video><br/>
          <p><b>영상 길이:</b> ${durationSec}초</p>
          <p><b>단계별 소요 시간</b> — 대사: ${fmtSec(state.timing.dialogueSec)} · 목소리: ${fmtSec(state.timing.voiceSec)} · 영상: ${fmtSec(state.timing.videoSec)}</p>
          <p><b>총 소요 시간:</b> ${fmtSec(total)}</p>
          <a href="${mediaUrl(videoPath)}" target="_blank">다운로드 / 새 탭에서 열기</a>`;
        return;
      }
      if (job.status === "error") {
        alert("영상 생성 실패: " + job.error);
        return;
      }
      await new Promise((r) => setTimeout(r, 1500));
    }
  } finally {
    clearInterval(timerId);
    progressBox.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-generate-video").addEventListener("click", async () => {
    if (!state.currentComposite || !state.currentDialogue || !state.voiceLine1 || !state.voiceLine2) {
      alert("3~4단계를 먼저 완료하세요 (대사, 목소리).");
      return;
    }
    const btn = document.getElementById("btn-generate-video");
    btn.disabled = true;
    try {
      const { job_id } = await postJSON("/api/videos", {
        composite_id: state.currentComposite.id,
        dialogue_id: state.currentDialogue.id,
        voice1_id: state.selVoice1.id,
        voice2_id: state.selVoice2.id,
        ltx_prompt: state.currentDialogue.ltx_prompt || null,
      });
      await pollVideoJob(job_id);
    } catch (err) {
      alert("영상 생성 요청 실패: " + err.message);
    } finally {
      btn.disabled = false;
    }
  });
});

// ---------- health ----------
async function checkHealth() {
  try {
    const h = await getJSON("/api/health");
    document.getElementById("status-comfy").className = "dot " + (h.comfyui ? "dot-ok" : "dot-bad");
    document.getElementById("status-ollama").className = "dot " + (h.ollama ? "dot-ok" : "dot-bad");
  } catch {
    document.getElementById("status-comfy").className = "dot dot-bad";
    document.getElementById("status-ollama").className = "dot dot-bad";
  }
}

// ---------- init ----------
async function init() {
  setupNav();
  await Promise.all([loadCharacters(), loadBackgrounds(), loadVoices(), loadKeywordPresets()]);
  await loadImportLists();
  checkHealth();
  setInterval(checkHealth, 15000);
}

document.addEventListener("DOMContentLoaded", init);
