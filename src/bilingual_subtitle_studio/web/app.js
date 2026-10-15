// Browser side of Bilingual Subtitle Studio. Talks to the local API in api.py.
// Text from the server and from the user is always inserted with textContent, never innerHTML.

const STEP_NAMES = ["Import", "Transcribe", "Translate", "Review", "Export"];
const STEP_SECTIONS = {
  Import: "#step-import",
  Transcribe: "#step-transcribe",
  Translate: "#step-translate",
  Review: "#step-review",
  Export: "#step-export",
};
const SOURCE_NOTES = {
  demo: "Showing demo rows. Transcribe your own audio to replace them.",
  transcription: "Transcribed rows. Translate them next, or edit them directly.",
  gemini_translation: "Translated rows. Check any rows marked for review before exporting.",
};

const state = {
  options: null,
  rows: [],
  source: "demo",
  preparedAudio: "",
  pendingVideo: "",
  exportComplete: false,
  outputMode: "Original + Translation",
  jobRunning: false,
  texts: null,
  activeFormat: "srt",
};

const $ = (selector) => document.querySelector(selector);

// Small DOM builder: el("p", { class: "x", onclick: fn }, "text", childNode)
function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (node.hidden = true), 4500);
}

function errorMessage(detail, fallback) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  return fallback;
}

async function api(path, { method = "GET", body } = {}) {
  const init = { method, headers: {} };
  if (body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const response = await fetch(path, init);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(errorMessage(data.detail, `Request failed (${response.status})`));
  return data;
}

function fillSelect(select, items, selected) {
  select.replaceChildren(
    ...items.map(([value, label]) => {
      const option = el("option", { value }, label);
      option.selected = value === selected;
      return option;
    }),
  );
}

// ---------- Stepper and button states ----------

async function refreshProgress() {
  const data = await api("/api/progress", {
    method: "POST",
    body: {
      rows: state.rows,
      subtitle_source: state.source,
      prepared_audio_path: state.preparedAudio,
      export_complete: state.exportComplete,
      output_mode: state.outputMode,
    },
  });
  renderStepper(data.progress, data.current_step);
}

function renderStepper(progress, currentStep) {
  const items = STEP_NAMES.map((name, index) => {
    const done = progress[name] >= 100;
    const current = name === currentStep;
    const stepClass = done ? "done" : current ? "current" : "";
    return el(
      "button",
      {
        class: `step ${stepClass}`.trim(),
        type: "button",
        "aria-current": current ? "step" : undefined,
        onclick: () => $(STEP_SECTIONS[name]).scrollIntoView({ behavior: "smooth", block: "start" }),
      },
      el("span", { class: "step-dot" }, done ? "✓" : String(index + 1)),
      name,
    );
  });
  $("#stepper").replaceChildren(el("div", { class: "stepper-inner" }, ...items));
}

function renderButtons() {
  $("#transcribe-btn").disabled = !state.preparedAudio || state.jobRunning;
  $("#translate-btn").disabled = !state.rows.length || state.jobRunning;
  $("#mark-reviewed-btn").disabled = !state.rows.length;
  $("#save-btn").disabled = !state.rows.length || state.jobRunning;
}

function renderAll() {
  renderEditor();
  renderButtons();
  refreshProgress().catch((error) => toast(error.message));
}

// ---------- Import ----------

function setImportStatus(message, isError = false) {
  const node = $("#import-status");
  node.textContent = message;
  node.classList.toggle("is-error", isError);
}

async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  setImportStatus(`Uploading ${file.name}…`);
  const response = await fetch("/api/upload", { method: "POST", body: form });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(errorMessage(data.detail, "Upload failed."));

  state.exportComplete = false;
  state.preparedAudio = "";
  state.pendingVideo = "";
  $("#extract-btn").hidden = true;

  if (data.kind === "audio") {
    state.preparedAudio = data.path;
    setImportStatus(`Ready to transcribe: ${data.name}`);
  } else if (data.kind === "video") {
    state.pendingVideo = data.path;
    setImportStatus(`Video uploaded: ${data.name}. Extract its audio to continue.`);
    $("#extract-btn").hidden = false;
  } else {
    setImportStatus(`Unsupported file type: ${data.name}`, true);
  }
  renderAll();
}

async function extractAudio() {
  const data = await api("/api/extract", { method: "POST", body: { path: state.pendingVideo } });
  state.preparedAudio = data.path;
  $("#extract-btn").hidden = true;
  setImportStatus(`Audio ready: ${data.path.split("/").pop()}`);
  renderAll();
}

// ---------- Background jobs ----------

function trackJob(jobId, kind, slot) {
  state.jobRunning = true;
  renderButtons();

  const fill = el("div", { class: "progress-fill" });
  const text = el("div", { class: "progress-text" }, "Starting…");
  const stop = el(
    "button",
    {
      class: "btn btn-small",
      type: "button",
      onclick: () => api(`/api/jobs/${jobId}/cancel`, { method: "POST" }).catch((e) => toast(e.message)),
    },
    "Stop",
  );
  slot.replaceChildren(el("div", { class: "progress-track" }, fill), el("div", { class: "row" }, text, stop));

  const timer = setInterval(async () => {
    try {
      const job = await api(`/api/jobs/${jobId}`);
      if (job.total) fill.style.width = `${Math.min(100, (job.done / job.total) * 100)}%`;
      text.textContent = job.message || "Working…";
      if (job.status === "running") return;

      clearInterval(timer);
      state.jobRunning = false;
      stop.remove();
      if (job.status === "done") {
        applyRows(job.rows, kind);
        slot.replaceChildren();
        toast(kind === "transcribe" ? `Loaded ${job.rows.length} rows.` : `Translated ${job.rows.length} rows.`);
      } else if (job.status === "stopped") {
        text.textContent = job.message || "Stopped.";
      } else {
        text.textContent = job.error || "The job failed.";
        text.classList.add("is-error");
      }
      renderAll();
    } catch (error) {
      clearInterval(timer);
      state.jobRunning = false;
      text.textContent = error.message;
      text.classList.add("is-error");
      renderButtons();
    }
  }, 600);
}

function applyRows(rows, kind) {
  state.rows = rows;
  state.source = kind === "transcribe" ? "transcription" : "gemini_translation";
  state.exportComplete = false;
  scheduleExportPreview();
}

async function startTranscribe() {
  const { job_id } = await api("/api/transcribe", {
    method: "POST",
    body: {
      path: state.preparedAudio,
      model_size: $("#whisper-model").value,
      language: $("#language-hint").value,
      compute_type: $("#compute-type").value,
    },
  });
  trackJob(job_id, "transcribe", $("#transcribe-progress"));
}

async function startTranslate() {
  const { job_id } = await api("/api/translate", {
    method: "POST",
    body: {
      rows: state.rows,
      target_language: $("#target-language").value,
      tone: $("#tone").value,
      model_name: $("#gemini-model").value,
      api_key: $("#api-key").value || null,
    },
  });
  trackJob(job_id, "translate", $("#translate-progress"));
}

async function markAllReviewed() {
  const data = await api("/api/review/mark-all", { method: "POST", body: { rows: state.rows } });
  state.rows = data.rows;
  state.exportComplete = false;
  renderAll();
  scheduleExportPreview();
}

// ---------- Editor ----------

function renderEditor() {
  $("#source-note").textContent = SOURCE_NOTES[state.source] || "";
  const review = state.rows.filter((row) => row.status === "needs_review").length;
  $("#review-note").textContent = !state.rows.length
    ? "No subtitle rows yet."
    : review
      ? `${review} row${review === 1 ? "" : "s"} marked for review.`
      : "No rows marked for review.";
  $("#rows").replaceChildren(...state.rows.map((row, index) => editorRow(row, index)));
}

function editorRow(row, index) {
  const change = (field, value) => {
    state.rows[index][field] = value;
    state.exportComplete = false;
    refreshProgress().catch((error) => toast(error.message));
    scheduleExportPreview();
  };
  const timeInput = (field) =>
    el("input", {
      type: "number",
      step: "0.01",
      min: "0",
      value: String(row[field]),
      "aria-label": field === "start_seconds" ? "Start seconds" : "End seconds",
      onchange: (event) => change(field, Number.parseFloat(event.target.value) || 0),
    });
  const textInput = (field, label) =>
    el("input", {
      type: "text",
      value: row[field] ?? "",
      "aria-label": label,
      onchange: (event) => change(field, event.target.value),
    });

  const statusSelect = el(
    "select",
    {
      "aria-label": "Status",
      onchange: (event) => {
        change("status", event.target.value);
        renderEditor();
      },
    },
    ...["ai_draft", "edited", "needs_review"].map((value) => {
      const option = el("option", { value }, value.replace("_", " "));
      option.selected = row.status === value;
      return option;
    }),
  );
  statusSelect.className = `status-${row.status}`;

  return el(
    "tr",
    {},
    el("td", {}, String(row.index)),
    el("td", {}, timeInput("start_seconds")),
    el("td", {}, timeInput("end_seconds")),
    el("td", {}, textInput("source_text", "Original text")),
    el("td", {}, textInput("translated_text", "Translation")),
    el("td", {}, statusSelect),
  );
}

// ---------- Export ----------

let previewTimer = null;

function scheduleExportPreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(refreshPreview, 300);
}

function exportRequest(save) {
  return api("/api/export", {
    method: "POST",
    body: {
      rows: state.rows,
      output_mode: state.outputMode,
      target_language: $("#target-language").value,
      save,
    },
  });
}

async function refreshPreview() {
  const preview = $("#preview");
  if (!state.rows.length) {
    state.texts = null;
    preview.classList.remove("is-error");
    preview.textContent = "Nothing to preview yet. Transcribe or translate first.";
    return;
  }
  try {
    const data = await exportRequest(false);
    state.texts = data.texts;
    preview.classList.remove("is-error");
    showPreview();
  } catch (error) {
    state.texts = null;
    preview.classList.add("is-error");
    preview.textContent = error.message;
  }
}

function showPreview() {
  const preview = $("#preview");
  const link = $("#download-link");
  if (!state.texts) return;
  const format = state.activeFormat;
  preview.textContent = state.texts[format];
  if (link.href.startsWith("blob:")) URL.revokeObjectURL(link.href);
  link.href = URL.createObjectURL(new Blob([state.texts[format]], { type: "text/plain;charset=utf-8" }));
  link.download = `subtitles.${format}`;
  link.textContent = `Download ${format.toUpperCase()}`;
}

async function saveAll() {
  const data = await exportRequest(true);
  state.exportComplete = true;
  $("#save-note").textContent = `Saved to ${data.folder}`;
  renderAll();
}

// ---------- Wiring ----------

function wire() {
  const dropzone = $("#dropzone");
  const fileInput = $("#file-input");
  const run = (action) => (...args) => action(...args).catch((error) => toast(error.message));

  fileInput.addEventListener("change", () => fileInput.files[0] && run(uploadFile)(fileInput.files[0]));
  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("is-over");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-over"));
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-over");
    if (event.dataTransfer.files[0]) run(uploadFile)(event.dataTransfer.files[0]);
  });

  $("#extract-btn").addEventListener("click", run(extractAudio));
  $("#transcribe-btn").addEventListener("click", run(startTranscribe));
  $("#translate-btn").addEventListener("click", run(startTranslate));
  $("#mark-reviewed-btn").addEventListener("click", run(markAllReviewed));
  $("#save-btn").addEventListener("click", run(saveAll));

  $("#output-mode").addEventListener("change", (event) => {
    state.outputMode = event.target.value;
    state.exportComplete = false;
    renderAll();
    scheduleExportPreview();
  });
  $("#target-language").addEventListener("change", scheduleExportPreview);

  for (const tab of document.querySelectorAll(".tab")) {
    tab.addEventListener("click", () => {
      state.activeFormat = tab.dataset.format;
      for (const other of document.querySelectorAll(".tab")) other.classList.toggle("is-active", other === tab);
      showPreview();
    });
  }
}

async function init() {
  state.options = await api("/api/options");
  const options = state.options;
  fillSelect($("#whisper-model"), options.whisper_models.map((v) => [v, v]), "base");
  fillSelect(
    $("#language-hint"),
    options.language_hints.map((v) => [v, v === "auto" ? "Auto-detect" : v]),
    "auto",
  );
  fillSelect($("#compute-type"), options.compute_types.map((v) => [v, v]), "int8");
  fillSelect($("#target-language"), options.languages.map((l) => [l.code, l.label]), "en");
  fillSelect($("#tone"), options.tones.map((v) => [v, v]), "Natural");
  fillSelect($("#output-mode"), options.output_modes.map((v) => [v, v]), state.outputMode);

  const demo = await api("/api/demo");
  state.rows = demo.rows;
  state.source = "demo";
  wire();
  renderAll();
  refreshPreview();
}

init().catch((error) => toast(`Could not start: ${error.message}`));
