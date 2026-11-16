"use strict";

const $ = id => document.getElementById(id);

// Access and provider credentials stay out of browser storage.
const appearanceKey = "mr-robot.appearance";
const appearances = new Set(["system", "light", "dark"]);
const systemAppearance = typeof window.matchMedia === "function" ?
  window.matchMedia("(prefers-color-scheme: dark)") : null;
let appearance = "light";
try {
  const savedAppearance = window.localStorage.getItem(appearanceKey);
  if (appearances.has(savedAppearance)) appearance = savedAppearance;
} catch (_) {
  // Blocked/private storage must not prevent the controls from loading.
}

function applyAppearance() {
  const dark = appearance === "dark" || (appearance === "system" && systemAppearance?.matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  $("themeSelect").value = appearance;
  $("themeDescription").textContent = appearance === "system" ?
    "Follows your system" : appearance === "dark" ? "Dark appearance" : "Light appearance";
}

$("themeSelect").addEventListener("change", () => {
  appearance = appearances.has($("themeSelect").value) ? $("themeSelect").value : "dark";
  applyAppearance();
  try { window.localStorage.setItem(appearanceKey, appearance); }
  catch (_) { $("themeDescription").textContent += " · this window only"; }
});
systemAppearance?.addEventListener("change", () => {
  if (appearance === "system") applyAppearance();
});
applyAppearance();

let access = "";
let connected = false;
let deviceKnown = false;
let deviceState = null;
let firmware = null;
let museOnline = false;
let hostReady = false;
let selectedFace = "pixel";
let settings = null;
let settingsDirty = false;
let voicePaused = false;
let localButtonSupported = false;
let armError = null;
let storedGeminiConfirmed = false;
let latestImage = null;
let imageRequest = null;
const ollamaModelHints = {
  "gemma4:12b": "Chat on this Mac or press the green button for a spoken question and a text reply.",
  "gemma4:e4b": "Chat on this Mac. Replies can also appear on the round display.",
  "qwen3.6:latest": "Chat on this Mac or press the green button. Gemma transcribes the question and Qwen answers.",
  "x/z-image-turbo:latest": "Generate an image from text or voice. It appears in Conversation and on the board’s Gallery."
};
function ollamaChoice(model) {
  const tagged = model.includes(":") ? model : model + ":latest";
  return Object.hasOwn(ollamaModelHints, tagged) ? tagged : "custom";
}
const geminiModels = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"];
const imageMode = () => settings?.provider === "ollama" && /^x\/z-image-turbo(?::latest)?$/.test(settings.model);
let voice = {active: false, stage: "off", turns: 0};
let textPending = false;
let textReaction = null;
let reactionTimer = null;
let savePending = false;
let voicePending = false;
let usbPending = false;
let commandPending = false;
let statusPoll = null;
let devicePoll = null;
let pollPending = false;
let portCount = 0;
let connectionErrorNotice = "";

const urls = {
  gemini: "https://generativelanguage.googleapis.com/v1beta",
  openrouter: "https://openrouter.ai/api/v1",
  ollama: "http://127.0.0.1:11434"
};
const defaults = {muse: "Muse", ollama: "gemma4:12b", gemini: "gemini-3.8-flash", openrouter: "", compatible: "", mock: "fixture"};
const providerNames = {muse: "Meta Muse", ollama: "Ollama", gemini: "Google Gemini", openrouter: "OpenRouter", compatible: "Compatible API", mock: "Local mock"};
const friendly = {
  unauthorized: "Open Control Room with tools/manager.py --open to connect this window.",
  network_unavailable: "The local manager is unavailable. Keep it running, then wait for the connection to recover.",
  status_timeout: "The local manager did not answer its status check. Keep it running; controls will recover when it responds.",
  request_failed: "The local manager could not complete this request. Try again when its connection is ready.",
  connect_one_waveshare_usb: "Connect one Waveshare with a USB data cable, then try again.",
  usb_connection_failed: "USB could not connect. Check the cable and close any other serial monitor.",
  usb_disconnected: "The board disconnected. Check its USB cable, then reconnect in Device.",
  usb_not_connected: "Connect the board in Device before using hardware controls.",
  gemini_quota_exceeded: "Google’s quota was reached. No retry or paid-model fallback was made.",
  gemini_key_rejected: "Google rejected this key. Check the project and API restrictions in AI Studio.",
  confirm_gemini_free_tier_project_first: "Confirm the key’s Free tier in Connection first.",
  gemini_live_requires_voice_transport: "Live models use the voice connection. Choose a Flash text model here.",
  gemini_model_not_found: "This model is unavailable for your key. Choose a supported model in AI Studio.",
  ollama_timeout: "The local model took too long to answer. Try again once it has loaded.",
  ollama_empty_at_limit: "The model reached its output limit before returning an answer.",
  image_runtime_missing: "The local Z-Image runtime is missing.",
  image_runtime_unavailable: "Control Room could not reach the local Z-Image runtime.",
  image_generation_failed: "Z-Image did not return a valid image.",
  image_generation_timeout: "Z-Image took too long to generate the image.",
  local_prompt_unclear: "I couldn’t make out the spoken request. Please try again.",
  daily_request_limit: "Today’s local attempt limit was reached. It resets at midnight UTC.",
  minute_request_limit: "The local per-minute limit was reached. Wait before sending again.",
  request_in_progress: "A request is already in progress. Wait for it to finish.",
  configure_gemini_first: "Save your Gemini connection first.",
  voice_firmware_required: "Connect the board running Face Lab 0.8 or newer.",
  voice_stream_firmware_required: "Update the board to Face Lab 0.9 to use the wake phrase.",
  wake_model_setup_required: "Install the local wake model using the project voice guide.",
  voice_stream_checksum: "An audio block failed its USB check. Enable voice mode to try again.",
  voice_stream_sequence: "An audio block arrived out of order. Enable voice mode to try again.",
  local_voice_firmware_required: "Update Face Lab to use the green button with Ollama.",
  local_voice_model_required: "Select an audio-capable Gemma 4 model in Connection.",
  voice_usb_timeout: "The board stopped responding. Check its USB cable.",
  voice_device_rejected: "The board ended the voice turn. Enable voice mode to try again.",
  voice_too_quiet: "The question was too quiet. Speak closer to the board.",
  voice_mode_owns_usb: "Pause voice before changing hardware controls.",
  device_firmware_unknown: "Control Room could not identify the board firmware. Check the USB cable.",
  device_switch_rejected: "The device could not switch. Let the current turn finish, then save again.",
  device_switch_unverified: "The board did not report the requested firmware after restarting.",
  provider_changed: "The saved provider changed in another window. Reload it before applying.",
  muse_board_unavailable: "Connect the paired Muse board over USB and apply the Muse provider.",
  muse_link_offline: "Muse is reconnecting to Wi-Fi. Wait for it to come online before sending.",
  muse_request_failed: "Muse could not complete this text request.",
  muse_reply_timeout: "Muse did not return a text reply in time.",
  stop_voice_mode_first: "Pause voice before disconnecting USB.",
  voice_connection_failed: "The Gemini voice connection failed. No automatic retry was sent.",
  voice_device_or_input_error: "Voice stopped. Check USB and speak only when the display says LISTENING, then enable voice again.",
  voice_cancelled: "Voice was cancelled.",
  voice_audio_limit: "The reply exceeded the twenty-second audio limit. Voice mode stopped.",
  voice_failed: "Voice stopped. Check the connection and enable voice to try again."
};

function consumeAccess() {
  const supplied = new URLSearchParams(location.hash.slice(1)).get("access");
  if (!supplied) return false;
  access = supplied;
  // The launcher credential stays in memory, never in storage, logs, or the page URL.
  history.replaceState(null, "", location.pathname);
  return true;
}

function notice(message, bad = false) {
  $("notice").textContent = message;
  $("notice").classList.toggle("error", bad);
}

function errorMessage(err) {
  return friendly[err.message] || err.message.replaceAll("_", " ");
}

function error(err) {
  notice(errorMessage(err), true);
}

async function api(path, body) {
  if (!access) throw Error("unauthorized");
  // Status reads must expire so a stalled local service cannot leave a stale
  // microphone/connection claim on screen. Never abort or retry action POSTs.
  const controller = body === undefined ? new AbortController() : null;
  const deadline = controller ? setTimeout(() => controller.abort(), 10000) : null;
  try {
    let response;
    try {
      response = await fetch(path, {
        method: body === undefined ? "GET" : "POST",
        cache: "no-store",
        credentials: "omit",
        headers: {
          "Authorization": "Bearer " + access,
          ...(body === undefined ? {} : {"Content-Type": "application/json"})
        },
        ...(controller ? {signal: controller.signal} : {}),
        ...(body === undefined ? {} : {body: JSON.stringify(body)})
      });
    } catch (_) {
      throw Error(controller?.signal.aborted ? "status_timeout" : "network_unavailable");
    }
    let result;
    try { result = await response.json(); }
    catch (_) { throw Error(controller?.signal.aborted ? "status_timeout" : "request_failed"); }
    if (!response.ok) throw Error(result.error || "request_failed");
    return result;
  } finally {
    if (deadline !== null) clearTimeout(deadline);
  }
}

// Tabs change only the visible controls, never the hardware or voice mode.
const tabs = Array.from(document.querySelectorAll("[data-panel]"));
function selectPanel(name, focus = false) {
  tabs.forEach(tab => {
    const selected = tab.dataset.panel === name;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    $("panel-" + tab.dataset.panel).hidden = !selected;
    if (selected && focus) tab.focus();
  });
}
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectPanel(tab.dataset.panel));
  tab.addEventListener("keydown", event => {
    let next;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    selectPanel(tabs[next].dataset.panel, true);
  });
});

function preview(face = selectedFace) {
  selectedFace = ["classic", "pixel", "orbit"].includes(face) ? face : "pixel";
  $("facePreview").className = "face " + selectedFace + " " + $("expression").value;
  document.querySelectorAll("[data-face]").forEach(button => {
    const selected = button.dataset.face === selectedFace;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  const expected = settings?.provider === "muse" ? "muse" : "face-lab";
  $("providerDeviceState").textContent = savePending ? "Applying provider and checking the board…" :
    firmware === "muse" || firmware === "face-lab" ?
      "ESP32 is running " + (firmware === "muse" ? "Muse." : "Face Lab.") +
      (settings && firmware !== expected ? " Save & apply to switch to the saved provider." : "") :
      "Connect the ESP32 by USB to apply a provider to the board.";
  renderStage();
}

// This is a state illustration, not a screen mirror or a measured audio waveform.
function renderStage() {
  let state = "idle", mode = "FACE LAB", title = "Ready when you are";
  let hint = "Enable a voice mode to begin.", faceHint = "Mic off", mic = "Microphone off";
  if (!access) {
    mode = "PREVIEW"; title = "Control Room is locked";
    hint = "Open the local launcher to connect."; faceHint = "Interface preview"; mic = "Microphone status unavailable";
  } else if (!hostReady || !deviceKnown) {
    mode = "STATUS UNAVAILABLE"; title = "Connection unavailable";
    hint = "Waiting for the local manager to respond."; faceHint = "Check Control Room"; mic = "Microphone status unavailable";
  } else if (firmware === "muse") {
    mode = "MUSE"; title = "Muse on the ESP32";
    hint = museOnline ? "Tap the green button for a live call." : "Waiting for the Muse link."; mic = "See the board for microphone status";
  } else if (armError && !voice.active && !voicePaused) {
    state = "error"; mode = "VOICE UNAVAILABLE"; title = "Voice unavailable";
    hint = friendly[armError] || "Check the provider settings."; mic = "Microphone off";
  } else if (!connected) {
    mode = "PREVIEW"; title = "Connect your companion";
    hint = portCount && firmware === "face-lab" ? "Open Device and select Connect to enable controls." : "Connect the ESP32 to this Mac by USB."; faceHint = "Interface preview"; mic = "Microphone status unavailable";
  } else if (!voice.active && deviceState && deviceState.microphone_active) {
    state = "listening"; mode = "MIC TEST"; title = "Microphone test";
    hint = "The board is measuring microphone levels."; faceHint = "Level test"; mic = "Microphone on · diagnostic";
  } else if (!voice.active && deviceState && deviceState.microphone_armed) {
    mode = "MIC TEST ARMED"; title = "Microphone test armed";
    hint = "Tap the board to start its level test."; faceHint = "Tap to begin";
  } else if (voice.error) {
    state = "error"; mode = "VOICE STOPPED"; title = "Voice stopped";
    hint = friendly[voice.error] || "Check the connection and enable voice to try again.";
    faceHint = "Check Control Room"; mic = "Voice mode stopped";
  } else if (voice.active) {
    const stages = {
      starting: ["thinking", "CONNECTING", "Connecting voice", "Preparing the voice connection.", "Please wait", "Microphone status pending"],
      waiting_for_tap: ["ready", "TAP TO BEGIN", "Ready to listen", "Tap the screen or press the talk button.", "Mic off", "Microphone off"],
      waiting_for_wake: ["wake", "LOCAL WAKE DETECTOR", "Listening for the wake phrase", "Say “Hey Mr. Robot” or press and release the green button.", "Mic on · local wake", "Microphone on · local wake"],
      waiting_for_followup: ["listening", "FOLLOW-UP", "Ready for your follow-up", "Speak again within 15 seconds, or press the button to end the conversation.", "Mic on · local follow-up", "Microphone on · local follow-up"],
      listening: ["listening", "LISTENING", "Listening", "Speak now. A screen tap or button press cancels.", "Tap to cancel", "Microphone on · question"],
      thinking: ["thinking", "THINKING", "Thinking", voice.mode === "image" ? "Preparing your image prompt." : voice.mode === "local" ? "Ollama is preparing your reply." : "Gemini is preparing your reply.", "Tap to cancel", "Microphone off"],
      generating_image: ["creating", "GENERATING IMAGE", "Generating an image", "The PNG will appear in Conversation and can also go to the ESP32.", "", "Microphone off"],
      sending_reply: ["receiving", "GETTING REPLY", "Getting your reply", "The reply is being sent to the board.", "Tap to cancel", "Microphone off"],
      speaking: ["speaking", "SPEAKING", "Speaking", "A screen tap or button press stops this turn.", "Tap to cancel", "Microphone off"]
    };
    [state, mode, title, hint, faceHint, mic] = stages[voice.stage] ||
      ["idle", "VOICE ACTIVE", "Voice active", "Check the board for its current state.", "Status pending", "Microphone status pending"];
  }
  if (hostReady && textReaction && !textPending && state === "idle") {
    state = textReaction;
    title = state === "done" ? "Reply ready" : "Request stopped";
    mode = "TEXT REQUEST";
    hint = state === "done" ? "Open Conversation to see the reply." : "Check the status message.";
  }
  if (hostReady && textPending && !["listening", "speaking", "receiving"].includes(state)) {
    state = imageMode() ? "creating" : "thinking";
    title = imageMode() ? "Drawing your image" : "Thinking";
    mode = imageMode() ? "Z-IMAGE TURBO" : "TEXT REQUEST";
    hint = "Waiting for the selected model.";
  }
  $("facePreview").dataset.reaction = state === "speaking" ? voice.reaction || "neutral" : "neutral";
  $("facePreview").dataset.state = state;
  $("stateMarker").dataset.state = state;
  $("faceMode").textContent = mode;
  $("faceHint").textContent = faceHint;
  $("companionState").textContent = title;
  $("companionHint").textContent = hint;
  $("micState").textContent = mic;
  $("facePreview").setAttribute("aria-label", selectedFace + " state illustration. " + title + ". " + mic + ".");
  $("previewLabel").textContent = hostReady && deviceKnown && (connected || firmware === "muse") ? "Device state" : "Preview";
  $("connectionDot").dataset.connected = String(connected && hostReady && deviceKnown);
}

function renderControls() {
  const live = hostReady && deviceKnown;
  $("screenLabel").hidden = deviceState?.screens_supported !== true;
  $("boardScreen").disabled = !live || !connected || voice.active || usbPending || commandPending;
  const busyVoice = voice.active || voicePending;
  const voiceReady = live && connected && !settingsDirty && (localButtonSupported ||
    (settings?.provider === "gemini" && settings.key_configured && settings.gemini_free_tier_confirmed));
  const waitingForWake = voice.stage === "waiting_for_wake";
  $("send").disabled = (settings?.provider === "muse" && (firmware !== "muse" || !deviceKnown || !museOnline)) || !hostReady || !settings || textPending || (busyVoice && !waitingForWake) || savePending || settingsDirty;
  $("send").setAttribute("aria-busy", String(textPending));
  $("save").disabled = !hostReady || savePending || voicePending || textPending || usbPending;
  $("providerFields").disabled = savePending || voicePending || textPending || usbPending;
  // Retain Stop after a failed status read: the last known active mode may still be running.
  $("voiceStop").hidden = !voice.active && (!voiceReady || voicePaused);
  $("voiceStop").disabled = !access || voicePending;
  $("voiceResume").hidden = !voicePaused || !(localButtonSupported || settings?.provider === "gemini");
  $("voiceResume").disabled = !voiceReady || busyVoice || textPending || savePending;
  $("connect").hidden = connected;
  $("disconnect").hidden = !connected;
  $("connect").disabled = !live || !portCount || usbPending || busyVoice;
  $("disconnect").disabled = !hostReady || usbPending || busyVoice || textPending || commandPending;
  $("ports").disabled = connected || usbPending || busyVoice;
  $("appearanceControls").disabled = firmware === "muse" || busyVoice || commandPending || usbPending;
  document.querySelectorAll("[data-new-expression]").forEach(option => {
    option.disabled = connected && deviceState?.screens_supported !== true;
  });
  document.querySelectorAll("[data-command]").forEach(button => {
    button.disabled = !live || !connected || busyVoice || commandPending || usbPending;
  });
  $("messages").setAttribute("aria-busy", String(textPending));
  $("settingsBadge").textContent = settingsDirty ? "UNSAVED CHANGES" : settings ? "SAVED ON THIS MAC" : "NOT LOADED";
  $("settingsBadge").dataset.dirty = String(settingsDirty);
  const voiceHelp = !hostReady ? "Open the local manager to use voice." : !deviceKnown ?
    "Device status is unavailable. Check the local manager." : !connected ? "Connect the board in Device to enable voice." :
    !voiceReady && !voice.active ? settingsDirty ? "Save the changes in Connection before enabling voice." :
      settings?.provider === "ollama" ? "Choose Gemma 4 12B, Qwen 3.6 or Z-Image to use the green button." : "Configure Gemini and confirm the Free tier in Connection to use voice." : voice.active ?
      "Pause voice to change device settings or switch providers." : voicePaused ?
      "Voice is paused. Resume voice to use the button and wake phrase." : localButtonSupported ? "Press and release the green button for a local text reply." : "Voice arms automatically when Gemini and USB are ready.";
  $("voiceHelp").textContent = firmware === "muse" ? "Tap again to end the call." : armError && !voice.active && !voicePaused ?
    friendly[armError] || "Check the provider settings." : imageMode() ?
    "Say “Hey Mr. Robot” or tap the green button, then describe your image." : voiceHelp;
  $("usbHelp").textContent = busyVoice ? "Pause voice before disconnecting or changing hardware." :
    connected ? "Connected. Appearance changes apply to the board." : "Use the board’s USB data connection to your Mac.";
  renderStage();
}

function renderVoice() {
  const titles = {
    starting: "Connecting voice…", waiting_for_tap: "Tap to begin.", waiting_for_wake: "Say “Hey Mr. Robot” or press the button.",
    listening: "Listening to you.", waiting_for_followup: "Ask a follow-up.",
    thinking: "Preparing a reply.", generating_image: "Generating an image.", sending_reply: "Getting your reply.", speaking: "Mr. Robot is speaking."
  };
  const stateUnavailable = !hostReady || !deviceKnown || (voice.active && !connected);
  $("voiceHeading").textContent = stateUnavailable ? "Voice status unavailable." : voice.error && !voicePaused ? "Voice stopped." :
    voice.active ? titles[voice.stage] || "Voice active." : "Voice controls";
  $("voiceStatus").textContent = stateUnavailable ? voice.active ?
    "The connection was lost. The last voice mode may still be running; use Stop voice mode or the board’s cancel control." :
    "Reconnect the local manager or board to confirm its state." :
    voice.error && !voicePaused ? friendly[voice.error] || "Voice stopped. Check the connection." :
    voice.active && voice.mode === "image" ? "Spoken prompts are transcribed locally. Images appear in Conversation." : voice.active && voice.mode === "local" ? "Ollama runs on this Mac and sends its text reply to the round display." : voice.active ?
      voice.stage === "waiting_for_wake" ? "The microphone is on for local wake detection. The green button also starts listening." :
      voice.stage === "waiting_for_tap" ? "Tap the screen or press the talk button, then speak when LISTENING appears." :
      voice.stage === "waiting_for_followup" ? "Speak again when the reply ends. The microphone is listening locally for up to 15 seconds." :
      voice.stage === "listening" ? "Your question ends after a pause. Tap the board or press its button to cancel." :
      "You can stop the voice session at any time." : voicePaused ? "The microphone is paused." : localButtonSupported ?
      "Press the green button. The microphone stays off between questions." : settings?.provider === "ollama" ?
      "Type a message in the text terminal." : "Gemini voice arms automatically when the board connects.";
  if (firmware === "muse") {
    $("voiceHeading").textContent = "Muse on the ESP32";
    $("voiceStatus").textContent = "Tap the green button for a spoken conversation. Hold it for a voice note with a text reply.";
  }
  const count = Number(voice.turns) || 0;
  $("voiceInstructions").textContent = firmware === "muse" ?
    "Tap for a live call or hold for a voice note. Muse connects over the ESP32’s Wi-Fi." : imageMode() ?
    "Wake detection and speech transcription run on this Mac. The image appears in Conversation." :
    settings?.provider === "ollama" ? "Tap the green button and speak when LISTENING appears. The answer appears on the ESP32." :
    "Say “Hey Mr. Robot” or tap the green button. Once activated, your question goes to Gemini. Speak again when LISTENING returns.";
  $("voiceCount").hidden = !count;
  $("voiceCount").textContent = count + (count === 1 ? " reply" : " replies");
  $("send").firstChild && ($("send").firstChild.textContent = imageMode() ? "Generate " : "Send ");
  $("send").setAttribute("aria-label", imageMode() ? "Generate image" : "Send message");
  $("prompt").placeholder = imageMode() ? "Describe an image…" : "Message Mr. Robot…";
  $("chatMode").textContent = textPending ? "WAITING FOR REPLY" : settings ?
    settings.provider === "mock" ? "LOCAL MOCK" : providerNames[settings.provider] || settings.provider : "LAPTOP";
  $("textHelp").textContent = imageMode() ? "Images stay in this browser. Generation runs on this Mac." : voice.active ? (voice.stage === "waiting_for_wake" ?
    "Wake listening pauses while your message is sent." : "Finish or pause the voice turn to send a message.") : settings && settings.provider === "mock" ?
    "Mock returns a local fixture. No AI service is contacted." : "The provider receives your current message.";
}

async function command(operation, value) {
  if (commandPending) return;
  if (!connected) { notice("Preview only. Connect USB in Device to apply this to the board."); return; }
  commandPending = true;
  renderControls();
  try {
    deviceState = await api("/api/device/command", {operation, ...(value === undefined ? {} : {value})});
    $("diagnostics").textContent = JSON.stringify(deviceState, null, 2);
    notice(operation === "mic-arm" ? "The microphone test is armed. Tap the board to measure levels." : "Device control applied.");
  } catch (err) { error(err); }
  finally { commandPending = false; renderControls(); }
}

document.querySelectorAll("[data-face]").forEach(button => button.addEventListener("click", () => {
  preview(button.dataset.face);
  command("face", selectedFace);
}));
$("boardScreen").addEventListener("change", () => command("screen", $("boardScreen").value));
$("expression").addEventListener("change", () => { preview(); command("expression", $("expression").value); });
$("brightness").addEventListener("input", () => { $("brightnessValue").textContent = $("brightness").value; });
$("brightness").addEventListener("change", () => command("brightness", Number($("brightness").value)));
document.querySelectorAll("[data-command]").forEach(button => button.addEventListener("click", () => command(button.dataset.command)));

function renderModelField() {
  const isOllama = $("provider").value === "ollama";
  const choice = $("ollamaModel").value;
  const custom = isOllama && choice === "custom";
  $("ollamaModelLabel").hidden = !isOllama;
  $("ollamaModel").disabled = !isOllama;
  $("textModelLabel").hidden = isOllama && !custom;
  $("model").disabled = isOllama && !custom;
  $("customModelLabel").textContent = custom ? "Ollama model name" : "Model";
  $("ollamaModelHint").textContent = ollamaModelHints[choice] ||
    "Enter a model name from ollama list, including its tag when required.";
}

function renderSettings() {
  const provider = $("provider").value;
  $("textModels").replaceChildren(...(provider === "gemini" ? geminiModels : []).map(model => {
    const option = document.createElement("option");
    option.value = model;
    return option;
  }));
  $("keyLabel").hidden = ["mock", "ollama", "muse"].includes(provider);
  $("ollamaGuide").hidden = provider !== "ollama";
  $("baseLabel").hidden = provider !== "compatible";
  $("geminiGuide").hidden = provider !== "gemini";
  $("mockGuide").hidden = provider !== "mock";
  $("remoteGuide").hidden = !["openrouter", "compatible"].includes(provider);
  $("model").readOnly = ["mock", "muse"].includes(provider);
  $("museGuide").hidden = provider !== "muse";
  if (provider === "ollama") {
    const choice = ollamaChoice($("model").value);
    $("ollamaModel").value = choice;
    if (choice !== "custom") $("model").value = choice;
  }
  renderModelField();
}

$("ollamaModel").addEventListener("change", () => {
  const choice = $("ollamaModel").value;
  $("model").value = choice === "custom" ? "" : choice;
  renderModelField();
  if (choice === "custom") $("model").focus();
  dirtySettings();
});

let geminiConfirmationEdited = false;
$("geminiFree").addEventListener("change", () => { geminiConfirmationEdited = true; });
$("provider").addEventListener("change", () => {
  geminiConfirmationEdited = false;
  const provider = $("provider").value;
  $("model").value = settings?.provider === provider ? settings.model : defaults[provider];
  $("apiKey").value = "";
  $("baseUrl").value = urls[provider] || "";
  $("keyState").textContent = "";
  $("geminiFree").checked = provider === "gemini" && (settings?.provider === "gemini" ? settings.gemini_free_tier_confirmed : storedGeminiConfirmed);
  $("budgetConfirmed").checked = false;
  renderSettings();
});
$("apiKey").addEventListener("input", () => { $("geminiFree").checked = false; $("budgetConfirmed").checked = false; });
function dirtySettings() {
  settingsDirty = true;
  $("settingsState").textContent = "Unsaved changes. Save this connection before sending a message or enabling voice.";
  renderControls();
}
$("settingsForm").addEventListener("input", dirtySettings);
$("settingsForm").addEventListener("change", dirtySettings);

const conversation = Promise.resolve().then(openConversation);
const emptyChat = $("emptyChat");
const imageIds = new Set();
let lastSeenImage = null;

function storageUnavailable() {
  $("historyStatus").textContent = "Local storage unavailable · this window only";
}

function renderMessage(message) {
  emptyChat.remove();
  const item = document.createElement("article");
  item.className = message.kind === "user" ? "user" : "assistant";
  const small = document.createElement("small");
  small.textContent = message.label;
  const paragraph = document.createElement("p");
  paragraph.textContent = message.text;
  item.append(small, paragraph);
  if (message.png) {
    const image = document.createElement("img");
    image.className = "generated-image";
    image.alt = "Generated image";
    image.width = 512;
    image.height = 512;
    image.loading = "lazy";
    image.src = "data:image/png;base64," + message.png;
    item.append(image);
  }
  $("messages").append(item);
  $("clearHistory").hidden = false;
  $("messages").scrollTop = $("messages").scrollHeight;
}

const historyReady = Promise.all([
  conversationStorage(conversation, "readonly", messages => messages.getAll()),
  conversationStorage(conversation, "readonly", (_, preferences) => preferences.get("lastImage"))
]).then(([messages, lastImage]) => {
  lastSeenImage = lastImage;
  for (const message of messages) {
    if (message.imageId) imageIds.add(message.imageId);
    renderMessage(message);
  }
}).catch(storageUnavailable);

async function addMessage(text, label, kind, image = null) {
  await historyReady;
  const message = {text, label, kind};
  if (image) {
    if (imageIds.has(image.id) || image.id === lastSeenImage) return;
    imageIds.add(image.id);
    lastSeenImage = image.id;
    Object.assign(message, {imageId: image.id, png: image.png});
  }
  renderMessage(message);
  try {
    await conversationStorage(conversation, "readwrite", (messages, preferences) => {
      if (image) preferences.put(image.id, "lastImage");
      const request = messages.add(message);
      request.onerror = event => {
        if (request.error.name === "ConstraintError") event.preventDefault();
      };
      return request;
    });
  } catch (_) {
    storageUnavailable();
  }
}

$("clearHistory").addEventListener("click", async () => {
  if (!window.confirm("Clear the conversation saved in this browser?")) return;
  $("clearHistory").disabled = true;
  try {
    await conversationStorage(conversation, "readwrite", messages => messages.clear());
  } catch (_) {
    storageUnavailable();
    return;
  } finally {
    $("clearHistory").disabled = false;
  }
  $("messages").replaceChildren(emptyChat);
  $("clearHistory").hidden = true;
});

async function retrieveImage() {
  if (imageRequest) return imageRequest;
  imageRequest = (async () => {
    const image = await api("/api/image");
    if (!image.id || image.id === latestImage || typeof image.png !== "string") return;
    await addMessage("Image ready", "Z-IMAGE TURBO", "assistant", image);
    latestImage = image.id;
  })();
  try { await imageRequest; }
  finally { imageRequest = null; }
}
$("prompt").addEventListener("keydown", event => {
  if (event.key !== "Enter" || !(event.metaKey || event.ctrlKey) || event.isComposing) return;
  event.preventDefault();
  if (!$("send").disabled) $("chatForm").requestSubmit($("send"));
});

$("chatForm").addEventListener("submit", async event => {
  event.preventDefault();
  const pauseWake = voice.active && voice.stage === "waiting_for_wake";
  if (textPending || (voice.active && !pauseWake) || voicePending || savePending) return;
  if (settings?.provider === "muse" && (firmware !== "muse" || !deviceKnown || !museOnline)) {
    error(Error("muse_link_offline")); return;
  }
  if (settingsDirty) { notice("Save the connection changes before sending a message.", true); return; }
  if (!hostReady) { error(Error(access ? "network_unavailable" : "unauthorized")); return; }
  const text = $("prompt").value.trim();
  if (!text) { $("prompt").focus(); return; }
  if (new TextEncoder().encode(text).length > 4096) { notice("Message must fit within 4,096 UTF-8 bytes.", true); return; }
  textPending = true;
  textReaction = null;
  clearTimeout(reactionTimer);
  await addMessage(text, "YOU", "user");
  $("prompt").value = "";
  renderControls();
  renderVoice();
  notice(imageMode() ? "Generating an image locally…" : "Waiting for the selected provider…");
  try {
    if (pauseWake) {
      voice = await api("/api/voice/stop", {});
      renderVoice();
      renderControls();
    }
    const reply = await api("/v1/chat", {text});
    if (reply.image_id) await retrieveImage();
    else await addMessage(reply.text, reply.is_mock ? "LOCAL MOCK" : reply.provider.toUpperCase() + " · " + reply.model, "assistant");
    textReaction = "done";
    notice(reply.image_id ? (reply.device_delivery === "image_sent" ? "Image ready in Conversation and on the round display." : "Image ready in Conversation.") : reply.provider === "muse" ? "Muse replied through the paired ESP32." : reply.is_mock ? "Local mock check complete. No AI service was contacted." : reply.device_delivery === "sent" ?
      "Reply received and sent to the round display." : "Reply received on the laptop.");
  } catch (err) {
    textReaction = "error";
    error(err);
    await addMessage(errorMessage(err), "REQUEST STOPPED", "assistant");
    if (!$("prompt").value) $("prompt").value = text;
  } finally {
    if (pauseWake) await api("/api/voice/resume", {}).catch(error);
    textPending = false;
    reactionTimer = setTimeout(() => { textReaction = null; renderStage(); }, 3500);
    renderControls();
    renderVoice();
    await refreshStatus();
  }
});

$("settingsForm").addEventListener("submit", async event => {
  event.preventDefault();
  if (savePending || voicePending || textPending || usbPending) return;
  savePending = true;
  renderControls();
  const provider = $("provider").value;
  let saved = false;
  const alreadyOnFaceLab = provider === "ollama" && settings?.provider === "ollama" && connected && firmware === "face-lab";
  const resumeWake = alreadyOnFaceLab && !voicePaused;
  let pausedForSave = false;
  try {
    if (voice.active || resumeWake) {
      voice = await api("/api/voice/stop", {});
      pausedForSave = true;
      if (voice.active) throw Error("stop_voice_mode_first");
    }
    await api("/api/settings", {
      provider, model: $("model").value, base_url: urls[provider] || $("baseUrl").value,
      api_key: $("apiKey").value, max_output_tokens: Number($("tokens").value),
      daily_requests: Number($("daily").value), requests_per_minute: Number($("minute").value),
      max_key_budget_usd: Number($("budget").value), remote_budget_confirmed: $("budgetConfirmed").checked,
      ...(provider === "gemini" && (geminiConfirmationEdited || $("apiKey").value) ? {gemini_free_tier_confirmed: $("geminiFree").checked} : {})
    });
    saved = true;
    geminiConfirmationEdited = false;
    $("apiKey").value = "";
    settingsDirty = false;
    if (alreadyOnFaceLab) {
      $("settingsState").textContent = "Saved. Ollama will use the selected model.";
    } else if (portCount && ["gemini", "ollama", "muse"].includes(provider)) {
      notice("Applying provider to the ESP32…");
      await api("/api/device/apply-provider", {provider});
      $("settingsState").textContent = "Saved and applied to the ESP32.";
    } else {
      $("settingsState").textContent = "Saved on this Mac. Connect USB and save again to apply to the board.";
    }
    notice($("settingsState").textContent);
    await refreshStatus(true);
    await refreshDevice();
  } catch (err) {
    if (saved) {
      await refreshStatus(true);
      await refreshDevice();
      $("settingsState").textContent = "Saved on this Mac. " + errorMessage(err);
    }
    error(err);
  }
  finally {
    if (resumeWake && pausedForSave) {
      try {
        await api("/api/voice/resume", {});
        await refreshStatus();
      } catch (err) { error(err); }
    }
    savePending = false;
    renderControls();
  }
});

async function refreshStatus(initial = false) {
  if (statusPoll) return statusPoll;
  statusPoll = (async () => {
    try {
      const status = await api("/api/status");
      const loadForm = (initial || !settings) && !settingsDirty;
      settings = status.settings;
      voicePaused = status.voice_paused === true;
      localButtonSupported = status.local_button_supported === true;
      storedGeminiConfirmed = status.gemini_profile_confirmed === true;
      armError = status.voice_arm_error || null;
      if (status.image_id && status.image_id !== latestImage) retrieveImage().catch(error);
      voice = status.voice || {active: false, stage: "off", turns: 0};
      hostReady = true;
      $("providerStatus").textContent = settings.provider === "mock" ? "Local mock · no AI service" :
        settings.provider === "muse" ? "Meta Muse" :
        settings.provider === "ollama" ? "Ollama · " + settings.model :
        (providerNames[settings.provider] || settings.provider) + (settings.key_configured ? " · configured" : " · key needed");
      $("usageStatus").textContent = status.requests_today + " / " + settings.daily_requests;
      if (loadForm) {
        for (const [id, name] of Object.entries({provider: "provider", model: "model", baseUrl: "base_url", tokens: "max_output_tokens", daily: "daily_requests", minute: "requests_per_minute", budget: "max_key_budget_usd"})) {
          $(id).value = settings[name];
        }
        $("geminiFree").checked = settings.gemini_free_tier_confirmed;
        $("budgetConfirmed").checked = settings.remote_budget_confirmed;
        renderSettings();
      }
      if (!settingsDirty) $("keyState").textContent = settings.key_configured ? "Saved · leave blank to keep" : "Not configured";
      return true;
    } catch (err) {
      hostReady = false;
      $("providerStatus").textContent = err.message === "unauthorized" ? "Locked" : "Status unavailable";
      $("deviceStatus").textContent = "Status unavailable";
      $("usageStatus").textContent = "—";
      connectionErrorNotice = errorMessage(err);
      error(err);
      return false;
    } finally { renderVoice(); renderControls(); }
  })();
  try { return await statusPoll; }
  finally { statusPoll = null; }
}

async function refreshDevice() {
  if (devicePoll) return devicePoll;
  if (!access) return false;
  devicePoll = (async () => {
    try {
      const device = await api("/api/device");
      connected = device.connected;
      deviceKnown = true;
      deviceState = connected ? device.state : null;
      firmware = device.runtime?.firmware || (connected ? "face-lab" : null);
      museOnline = device.runtime?.online === true;
      $("deviceStatus").textContent = firmware === "muse" ? (museOnline ? "Muse · online" : "Muse · connecting") : connected ? "USB · " + (deviceState.firmware || "Face Lab") : firmware === "face-lab" ? "Face Lab · USB" : "Not connected";
      const selected = $("ports").value;
      $("ports").replaceChildren();
      portCount = device.ports.length;
      const paths = portCount ? device.ports : [""];
      paths.forEach(path => {
        const option = document.createElement("option");
        option.value = path;
        option.textContent = path || "No USB device found";
        $("ports").append(option);
      });
      if (device.ports.includes(selected)) $("ports").value = selected;
      if (connected) {
        $("diagnostics").textContent = JSON.stringify(deviceState, null, 2);
        if (!commandPending && !["brightness", "expression"].includes(document.activeElement.id)) {
          $("expression").value = deviceState.expression;
          if (deviceState.screen && document.activeElement.id !== "boardScreen") $("boardScreen").value = deviceState.screen;
          $("brightness").value = deviceState.brightness;
          $("brightnessValue").textContent = deviceState.brightness;
          preview(deviceState.face);
        }
      } else {
        $("diagnostics").textContent = "Connect USB to read firmware and hardware state.";
      }
      if (device.error) error(Error(device.error));
      return true;
    } catch (err) {
      deviceKnown = false;
      $("deviceStatus").textContent = "Status unavailable";
      connectionErrorNotice = errorMessage(err);
      error(err);
      return false;
    } finally { renderVoice(); renderControls(); }
  })();
  try { return await devicePoll; }
  finally { devicePoll = null; }
}

async function changeUsb(connect) {
  if (usbPending || voice.active || voicePending) return;
  usbPending = true;
  renderControls();
  try {
    await api(connect ? "/api/device/connect" : "/api/device/disconnect", connect ? {port: $("ports").value} : {});
    const ok = await refreshDevice();
    if (ok) notice(connect ? "USB connected. Device controls are ready." : "USB disconnected.");
  } catch (err) { error(err); }
  finally { usbPending = false; renderControls(); }
}
$("connect").addEventListener("click", () => changeUsb(true));
$("disconnect").addEventListener("click", () => changeUsb(false));

$("voiceResume").addEventListener("click", async () => {
  if (voicePending) return;
  voicePending = true;
  renderControls();
  try {
    await api("/api/voice/resume", {});
    notice("Resuming voice. Wait for the local wake indicator.");
    await refreshStatus();
  } catch (err) { error(err); }
  finally { voicePending = false; renderVoice(); renderControls(); }
});
$("voiceStop").addEventListener("click", async () => {
  if (voicePending) return;
  voicePending = true;
  renderControls();
  try {
    voice = await api("/api/voice/stop", {});
    notice("Pausing voice. Resume voice when you want the microphone on again.");
    await refreshStatus();
  } catch (err) { error(err); }
  finally { voicePending = false; renderVoice(); renderControls(); }
});

async function unlock() {
  if (!access) {
    hostReady = false;
    $("providerStatus").textContent = "Locked";
    $("deviceStatus").textContent = "Status unavailable";
    error(Error("unauthorized"));
    renderVoice();
    renderControls();
    return;
  }
  const statusOk = await refreshStatus(true);
  const deviceOk = await refreshDevice();
  if (statusOk && deviceOk) notice("Control Room is ready.");
}

consumeAccess();
renderSettings();
renderControls();
window.addEventListener("hashchange", () => { if (consumeAccess()) unlock(); });
unlock();
setInterval(async () => {
  if (pollPending || !access) return;
  pollPending = true;
  try {
    const deviceOk = await refreshDevice();
    const statusOk = await refreshStatus();
    if (deviceOk && statusOk && connectionErrorNotice) {
      if ($("notice").textContent === connectionErrorNotice) notice("Connection restored. Control Room is ready.");
      connectionErrorNotice = "";
    }
  }
  finally { pollPending = false; }
}, 2000);
