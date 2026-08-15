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
};

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

// ---------- generic pick grid ----------
function renderPickGrid(containerId, items, selectedItem, onSelect, kind, excludeId) {
  const el = document.getElementById(containerId);
  el.innerHTML = "";
  items.forEach((item) => {
    const isExcluded = excludeId != null && item.id === excludeId;
    const card = document.createElement("div");
    card.className =
      "pick-card" +
      (selectedItem && selectedItem.id === item.id ? " selected" : "") +
      (isExcluded ? " pick-card-disabled" : "");
    let thumb;
    if (kind === "voice") {
      thumb = `<div class="thumb-audio"><button type="button" class="play-btn">▶</button></div>`;
    } else {
      thumb = `<img src="${mediaUrl(item.image_path)}" alt="${item.name}" />`;
    }
    card.innerHTML = `${thumb}<div class="pick-name">${item.name}</div>`;
    if (isExcluded) {
      card.title = "다른 슬롯에서 이미 선택됨";
    } else {
      card.addEventListener("click", () => onSelect(item));
    }
    if (kind === "voice") {
      const playBtn = card.querySelector(".play-btn");
      playBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        new Audio(mediaUrl(item.reference_audio_path)).play();
      });
    }
    el.appendChild(card);
  });
}

// ---------- characters ----------
async function loadCharacters() {
  state.characters = await getJSON("/api/characters");
  renderCharacterGrid();
  renderCharPickers();
}

function renderCharPickers() {
  renderPickGrid("pick-char1", state.characters, state.selChar1, pickChar1, "char", state.selChar2?.id);
  renderPickGrid("pick-char2", state.characters, state.selChar2, pickChar2, "char", state.selChar1?.id);
}

function pickChar1(item) {
  state.selChar1 = item;
  renderCharPickers();
  tryShowComposite();
}
function pickChar2(item) {
  state.selChar2 = item;
  renderCharPickers();
  tryShowComposite();
}
function pickBg(item) {
  state.selBg = item;
  renderPickGrid("pick-bg", state.backgrounds, state.selBg, pickBg, "bg");
  tryShowComposite();
}
function pickVoice1(item) {
  state.selVoice1 = item;
  renderPickGrid("pick-voice1", state.voices, state.selVoice1, pickVoice1, "voice");
}
function pickVoice2(item) {
  state.selVoice2 = item;
  renderPickGrid("pick-voice2", state.voices, state.selVoice2, pickVoice2, "voice");
}

function renderCharacterGrid() {
  const el = document.getElementById("character-grid");
  el.innerHTML = "";
  state.characters.forEach((c) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${mediaUrl(c.image_path)}" alt="${c.name}" />
      <div class="card-body">
        <div class="card-name">${c.name} <span style="color:#9aa1b0">(${c.gender})</span></div>
        <div class="card-desc">${c.description}</div>
        <button class="card-del" data-id="${c.id}">삭제</button>
      </div>`;
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
  renderPickGrid("pick-bg", state.backgrounds, state.selBg, pickBg, "bg");
}

function renderBackgroundGrid() {
  const el = document.getElementById("background-grid");
  el.innerHTML = "";
  state.backgrounds.forEach((b) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${mediaUrl(b.image_path)}" alt="${b.name}" />
      <div class="card-body">
        <div class="card-name">${b.name}</div>
        <div class="card-desc">${b.description}</div>
        <button class="card-del" data-id="${b.id}">삭제</button>
      </div>`;
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
  renderPickGrid("pick-voice1", state.voices, state.selVoice1, pickVoice1, "voice");
  renderPickGrid("pick-voice2", state.voices, state.selVoice2, pickVoice2, "voice");
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
  const box = document.getElementById("compose-result");
  if (!state.selChar1 || !state.selChar2 || !state.selBg) {
    box.innerHTML = "";
    state.currentComposite = null;
    renderDialogueSummary();
    return;
  }
  const qs = `character1_id=${state.selChar1.id}&character2_id=${state.selChar2.id}&background_id=${state.selBg.id}`;
  try {
    const result = await getJSON(`/api/composites/find?${qs}`);
    state.currentComposite = result;
    box.innerHTML = `<img src="${mediaUrl(result.image_path)}" /><p>저장된 합성 이미지를 불러왔습니다.</p>`;
  } catch (err) {
    state.currentComposite = null;
    box.innerHTML = `<p>이 조합으로 등록된 합성 이미지가 없습니다. 아래 "가져오기"로 등록하세요.</p>`;
  }
  renderDialogueSummary();
}

// ---------- dialogue ----------
function renderDialogueSummary() {
  const el = document.getElementById("dialogue-composite-summary");
  const c = state.currentComposite;
  if (!c) {
    el.innerHTML = "인물1, 인물2, 배경을 선택하세요.";
    return;
  }
  const c1 = state.characters.find((x) => x.id === c.character1_id);
  const c2 = state.characters.find((x) => x.id === c.character2_id);
  el.innerHTML = `
    <div class="summary-row">
      <img src="${mediaUrl(c.image_path)}" />
      <div><b>선택된 합성:</b> ${c1 ? c1.name : "?"} + ${c2 ? c2.name : "?"}</div>
    </div>`;
  document.getElementById("dialogue-char1-label").textContent = `인물1 (${c1 ? c1.name : "?"})`;
  document.getElementById("dialogue-char2-label").textContent = `인물2 (${c2 ? c2.name : "?"})`;
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

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-generate-line1").addEventListener("click", async () => {
    if (!state.currentComposite) {
      alert("먼저 인물1, 인물2, 배경을 선택하세요.");
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
    try {
      const result = await postJSON("/api/dialogues", {
        keyword,
        character1_id: state.currentComposite.character1_id,
        character2_id: state.currentComposite.character2_id,
      });
      state.currentDialogue = result;
      document.getElementById("line1-text").value = result.line1;
      document.getElementById("line2-text").value = result.line2;
    } catch (err) {
      alert("대사 생성 실패: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "인물1 대사 생성";
    }
  });

  document.getElementById("btn-generate-line2").addEventListener("click", async () => {
    if (!state.currentComposite) {
      alert("먼저 인물1, 인물2, 배경을 선택하세요.");
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
    try {
      if (!state.currentDialogue) {
        state.currentDialogue = await postJSON("/api/dialogues/manual", {
          character1_id: state.currentComposite.character1_id,
          character2_id: state.currentComposite.character2_id,
          line1,
          line2: "",
        });
      }
      const result = await postJSON(`/api/dialogues/${state.currentDialogue.id}/reply`, { line1 });
      state.currentDialogue = result;
      document.getElementById("line2-text").value = result.line2;
    } catch (err) {
      alert("답변 생성 실패: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "인물2 대사 생성 (답변)";
    }
  });

  document.getElementById("btn-save-dialogue").addEventListener("click", async () => {
    if (!state.currentComposite) {
      alert("먼저 인물1, 인물2, 배경을 선택하세요.");
      return;
    }
    const line1 = document.getElementById("line1-text").value;
    const line2 = document.getElementById("line2-text").value;
    if (state.currentDialogue) {
      state.currentDialogue = await patchJSON(`/api/dialogues/${state.currentDialogue.id}`, { line1, line2 });
    } else {
      state.currentDialogue = await postJSON("/api/dialogues/manual", {
        character1_id: state.currentComposite.character1_id,
        character2_id: state.currentComposite.character2_id,
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
    try {
      const [vl1, vl2] = await Promise.all([
        postJSON("/api/voice-lines", { text: state.currentDialogue.line1, voice_id: state.selVoice1.id }),
        postJSON("/api/voice-lines", { text: state.currentDialogue.line2, voice_id: state.selVoice2.id }),
      ]);
      state.voiceLine1 = vl1;
      state.voiceLine2 = vl2;
      const box = document.getElementById("voice-result");
      box.innerHTML = `
        <p><b>인물1</b> (${vl1.cached ? "캐시됨" : "새로 생성"}): ${state.currentDialogue.line1}</p>
        <audio controls src="${mediaUrl(vl1.audio_path)}"></audio>
        <p><b>인물2</b> (${vl2.cached ? "캐시됨" : "새로 생성"}): ${state.currentDialogue.line2}</p>
        <audio controls src="${mediaUrl(vl2.audio_path)}"></audio>`;
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
  while (true) {
    const job = await getJSON(`/api/videos/jobs/${jobId}`);
    if (job.status === "done") {
      progressBox.style.display = "none";
      const box = document.getElementById("video-result");
      const videoPath = job.result.video_path;
      const durationSec = job.result.duration_sec;
      const elapsed = job.elapsed_sec;
      box.innerHTML = `
        <video controls src="${mediaUrl(videoPath)}"></video><br/>
        <p><b>영상 길이:</b> ${durationSec}초 · <b>생성 소요 시간:</b> ${elapsed != null ? Math.round(elapsed) + "초" : "-"}</p>
        <a href="${mediaUrl(videoPath)}" target="_blank">다운로드 / 새 탭에서 열기</a>`;
      return;
    }
    if (job.status === "error") {
      progressBox.style.display = "none";
      alert("영상 생성 실패: " + job.error);
      return;
    }
    progressText.textContent = job.status === "running" ? "영상 생성 중... (몇 분 소요될 수 있습니다)" : "대기 중...";
    await new Promise((r) => setTimeout(r, 4000));
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
