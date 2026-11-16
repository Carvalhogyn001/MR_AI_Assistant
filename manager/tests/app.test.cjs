"use strict";

// Browser-independent regressions for UI state and request ownership.
// Run: node --test manager/tests/app.test.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const html = fs.readFileSync(path.join(__dirname, "../index.html"), "utf8");
const sources = ["history.js", "app.js"].map(file => fs.readFileSync(path.join(__dirname, "..", file), "utf8"));

class Element {
  constructor(id = "") {
    Object.assign(this, {id, value: "", textContent: "", className: "", dataset: {}, attributes: {},
      hidden: false, disabled: false, checked: false, children: [], handlers: {}, classes: new Set()});
    this.classList = {toggle: (name, on) => on ? this.classes.add(name) : this.classes.delete(name)};
  }
  setAttribute(name, value) { this.attributes[name] = value; }
  addEventListener(name, handler) { (this.handlers[name] ||= []).push(handler); }
  async fire(name, fields = {}) {
    const event = {preventDefault() {}, ...fields};
    for (const handler of this.handlers[name] || []) await handler(event);
  }
  append(...nodes) { nodes.forEach(node => { node.parent = this; this.children.push(node); }); }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  remove() {
    this.removed = true;
    if (this.parent) this.parent.children = this.parent.children.filter(node => node !== this);
  }
  get firstElementChild() { return this.children[0]; }
  focus() { this.document.activeElement = this; }
}

const settings = {
  provider: "gemini", model: "synthetic-text", base_url: "https://example.invalid", max_output_tokens: 256,
  daily_requests: 20, requests_per_minute: 4, max_key_budget_usd: 1, key_configured: true,
  gemini_free_tier_confirmed: true, remote_budget_confirmed: false
};
const response = (value, ok = true) => ({ok, json: async () => structuredClone(value)});
const flush = () => new Promise(resolve => setImmediate(resolve));

async function app({access = "test-only", unauthorized = false, savedAppearance = null,
  storageUnavailable = false, systemDark = false} = {}) {
  const elements = new Map();
  const groups = {face: [], command: [], panel: []};
  const ancestry = [];
  const voidTags = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]);
  for (const match of html.matchAll(/<\/?([a-z][a-z0-9-]*)\b([^>]*)>/gi)) {
    const tag = match[1].toLowerCase();
    if (match[0].startsWith("</")) {
      const index = ancestry.findLastIndex(entry => entry.tag === tag);
      if (index >= 0) ancestry.length = index;
      continue;
    }
    const attrs = {};
    for (const attribute of match[2].matchAll(/([\w-]+)="([^"]*)"/g)) attrs[attribute[1]] = attribute[2];
    const el = new Element(attrs.id);
    el.markupAncestors = ancestry.map(entry => entry.element);
    if (attrs.id) elements.set(attrs.id, el);
    if (attrs.value) el.value = attrs.value;
    el.hidden = /\bhidden\b/.test(match[2]);
    for (const group of Object.keys(groups)) {
      if (attrs["data-" + group]) { el.dataset[group] = attrs["data-" + group]; groups[group].push(el); }
    }
    if (!voidTags.has(tag)) ancestry.push({tag, element: el});
  }
  const doc = {
    documentElement: new Element("html"),
    activeElement: {id: ""},
    getElementById: id => elements.get(id)?.removed ? null : elements.get(id) || null,
    querySelectorAll: selector => groups[selector.match(/\[data-(.+)\]/)[1]] || [],
    createElement: () => { const element = new Element(); element.document = doc; return element; }
  };
  elements.forEach(element => { element.document = doc; });
  doc.getElementById("expression").value = "neutral";
  doc.getElementById("provider").value = "mock";
  doc.getElementById("messages").append(doc.getElementById("emptyChat"));
  const state = {
    status: {settings: structuredClone(settings), requests_today: 0, voice: {active: false, stage: "off", turns: 0}},
    device: {connected: true, ports: ["/dev/test-only"], state: {firmware: "test-only", face: "classic", expression: "neutral", brightness: 96, microphone_active: false}},
    calls: [], failStatus: false, failDevice: false, hangStatus: null, chat: null, interval: null,
    timers: new Map(), nextTimer: 0, appearanceWrites: [], appearanceListeners: []
  };
  state.systemAppearance = {
    matches: systemDark,
    addEventListener(name, listener) { state.appearanceListeners.push(listener); }
  };
  const context = vm.createContext({
    document: doc, TextEncoder, URLSearchParams, AbortController, location: {hash: access ? "#access=" + access : "", pathname: "/"},
    history: {replaceState() {}}, window: {
      addEventListener() {},
      matchMedia() { return state.systemAppearance; },
      localStorage: {
        getItem(key) {
          if (storageUnavailable) throw Error("Storage unavailable");
          assert.equal(key, "mr-robot.appearance");
          return savedAppearance;
        },
        setItem(key, value) {
          if (storageUnavailable) throw Error("Storage unavailable");
          state.appearanceWrites.push({key, value});
        }
      }
    },
    setInterval(callback) { state.interval = callback; },
    setTimeout(callback, milliseconds) {
      const id = ++state.nextTimer;
      state.timers.set(id, {callback, milliseconds});
      return id;
    },
    clearTimeout(id) { state.timers.delete(id); },
    fetch: async (route, options) => {
      state.calls.push({route, method: options.method});
      if (unauthorized) return response({error: "unauthorized"}, false);
      if (route === "/api/status") {
        if (state.failStatus) throw Error("synthetic network failure");
        const waitForAbort = () => new Promise((resolve, reject) => {
          options.signal?.addEventListener("abort", () => reject(Error("synthetic abort")), {once: true});
        });
        if (state.hangStatus === "headers") return waitForAbort();
        if (state.hangStatus === "body") return {ok: true, json: waitForAbort};
        return response(state.status);
      }
      if (route === "/api/device") {
        if (state.failDevice) throw Error("synthetic device failure");
        return response(state.device);
      }
      if (route === "/api/voice/stop") {
        state.status.voice = {active: false, stage: "off", turns: 0};
        state.status.voice_paused = true;
        return response(state.status.voice);
      }
      if (route === "/api/voice/resume") {
        state.status.voice_paused = false;
        return response({ok: true});
      }
      if (route === "/api/settings") {
        state.status.settings = {...state.status.settings, ...JSON.parse(options.body)};
        return response(state.status.settings);
      }
      if (route === "/api/device/apply-provider") {
        const {provider} = JSON.parse(options.body);
        assert.equal(provider, state.status.settings.provider);
        state.device = {connected: false, ports: ["/dev/test-only"],
          runtime: {firmware: provider === "muse" ? "muse" : "face-lab", online: true}};
        return response(state.device.runtime);
      }
      if (route === "/v1/chat") return state.chat;
      throw Error("Unexpected request: " + route);
    }
  });
  sources.forEach(source => vm.runInContext(source, context));
  await flush();
  return {...state, state, context, root: doc.documentElement, $: id => doc.getElementById(id), groups,
    setSystemDark(dark) {
      state.systemAppearance.matches = dark;
      state.appearanceListeners.forEach(listener => listener({matches: dark}));
    },
    run: expression => vm.runInContext(expression, context)};
}

test("locked window never performs requests or claims it is ready", async () => {
  const page = await app({access: ""});
  assert.equal(page.state.calls.length, 0);
  assert.match(page.$("notice").textContent, /tools\/manager\.py --open/);
  assert.equal(page.$("send").disabled, true);
  assert.equal(page.$("voiceResume").disabled, true);
  assert.equal(page.$("micState").textContent, "Microphone status unavailable");
});

test("saving Muse applies it to the connected board and refreshes both readouts", async () => {
  const page = await app();
  page.$("provider").value = "muse";
  await page.$("provider").fire("change");
  await page.$("settingsForm").fire("change");
  await page.$("settingsForm").fire("submit");
  assert.deepEqual(page.state.calls.filter(call => call.method === "POST").map(call => call.route),
    ["/api/settings", "/api/device/apply-provider"]);
  assert.equal(page.$("providerStatus").textContent, "Meta Muse");
  assert.match(page.$("deviceStatus").textContent, /Muse.*online/);
});

test("failed launch authentication is not overwritten by a ready notice", async () => {
  const page = await app({unauthorized: true});
  assert.match(page.$("notice").textContent, /tools\/manager\.py --open/);
  assert.equal(page.$("providerStatus").textContent, "Locked");
  assert.equal(page.$("send").disabled, true);
  assert.notEqual(page.$("connectionDot").dataset.connected, "true");
});

test("status polling cannot enable Send or duplicate an in-flight text request", async () => {
  const page = await app();
  let resolve;
  page.state.chat = new Promise(done => { resolve = done; });
  page.$("prompt").value = "Synthetic request";
  const pending = page.$("chatForm").fire("submit");
  await flush();
  assert.equal(page.$("send").disabled, true);
  assert.equal(page.state.timers.size, 0, "Action POSTs must not acquire a status-read deadline");
  await page.run("refreshStatus()");
  assert.equal(page.$("send").disabled, true);
  page.$("prompt").value = "A second request";
  await page.$("chatForm").fire("submit");
  assert.equal(page.state.calls.filter(call => call.route === "/v1/chat").length, 1);
  resolve(response({text: "Synthetic reply", is_mock: true}));
  await pending;
  assert.equal(page.$("send").disabled, false);
});

test("lost host status clears the listening claim, keeps Stop, and recovers", async () => {
  const page = await app();
  page.state.status.voice = {active: true, stage: "listening", turns: 0};
  await page.run("refreshStatus()");
  assert.equal(page.$("facePreview").dataset.state, "listening");
  page.state.failStatus = true;
  await page.run("refreshStatus()");
  assert.equal(page.$("micState").textContent, "Microphone status unavailable");
  assert.equal(page.$("voiceStop").hidden, false);
  assert.equal(page.$("voiceStop").disabled, false);
  assert.equal(page.$("connectionDot").dataset.connected, "false");
  page.state.failStatus = false;
  page.state.status.voice = {active: false, stage: "off", turns: 1};
  await page.state.interval();
  assert.equal(page.$("micState").textContent, "Microphone off");
  assert.equal(page.$("notice").textContent, "Connection restored. Control Room is ready.");
});

test("lost device status never retains a live mic indicator", async () => {
  const page = await app();
  page.state.status.voice = {active: true, stage: "waiting_for_wake", turns: 0};
  await page.run("refreshStatus()");
  page.state.failDevice = true;
  await page.run("refreshDevice()");
  assert.equal(page.$("micState").textContent, "Microphone status unavailable");
  assert.equal(page.$("voiceHeading").textContent, "Voice status unavailable.");
  assert.equal(page.$("voiceStop").hidden, false);
});

test("voice stages keep wake capture, question capture, and playback distinct", async () => {
  const page = await app();
  const cases = [
    ["waiting_for_tap", "ready", "Microphone off"],
    ["waiting_for_followup", "listening", "Microphone on · local follow-up"],
    ["waiting_for_wake", "wake", "Microphone on · local wake"],
    ["listening", "listening", "Microphone on · question"],
    ["thinking", "thinking", "Microphone off"],
    ["sending_reply", "receiving", "Microphone off"],
    ["speaking", "speaking", "Microphone off"]
  ];
  for (const [stage, visual, mic] of cases) {
    page.state.status.voice = {active: true, stage, turns: 0};
    await page.run("refreshStatus()");
    assert.equal(page.$("facePreview").dataset.state, visual);
    assert.equal(page.$("micState").textContent, mic);
    assert.equal(page.$("send").disabled, stage !== "waiting_for_wake");
  }
});

test("Ollama model changes save on the host and preserve the Face Lab USB connection", async () => {
  const page = await app();
  page.state.status.settings.provider = "ollama";
  page.state.status.settings.model = "x/z-image-turbo";
  await page.run("refreshStatus(true)");
  assert.equal(page.$("ollamaModel").value, "x/z-image-turbo:latest");
  assert.equal(page.$("model").disabled, true);
  page.state.status.voice = {active: true, stage: "waiting_for_wake", mode: "image"};
  await page.run("refreshStatus()");
  page.$("ollamaModel").value = "qwen3.6:latest";
  await page.$("ollamaModel").fire("change");
  assert.equal(page.$("model").value, "qwen3.6:latest");
  await page.$("settingsForm").fire("submit");
  assert.equal(page.state.status.settings.model, "qwen3.6:latest");
  assert.deepEqual(page.state.calls.filter(call => call.method === "POST").map(call => call.route),
    ["/api/voice/stop", "/api/settings", "/api/voice/resume"]);
  assert.equal(page.state.status.voice_paused, false);
  page.$("ollamaModel").value = "custom";
  await page.$("ollamaModel").fire("change");
  assert.equal(page.$("model").disabled, false);
  assert.equal(page.$("model").value, "");
});

test("polling preserves unsaved provider fields and blocks requests until saved", async () => {
  const page = await app();
  page.$("model").value = "my-unsaved-model";
  await page.$("settingsForm").fire("input");
  await page.run("refreshStatus()");
  assert.equal(page.$("model").value, "my-unsaved-model");
  assert.equal(page.$("send").disabled, true);
  assert.equal(page.$("voiceResume").disabled, true);
  assert.equal(page.$("settingsBadge").textContent, "UNSAVED CHANGES");
});

test("a current microphone diagnostic takes priority over a retained voice error", async () => {
  const page = await app();
  page.state.status.voice = {active: false, stage: "stopped", turns: 0, error: "voice_too_quiet"};
  await page.run("refreshStatus()");
  assert.equal(page.$("faceMode").textContent, "VOICE STOPPED");
  page.state.device.state.microphone_armed = true;
  await page.run("refreshDevice()");
  assert.equal(page.$("faceMode").textContent, "MIC TEST ARMED");
  page.state.device.state.microphone_active = true;
  await page.run("refreshDevice()");
  assert.equal(page.$("faceMode").textContent, "MIC TEST");
  assert.equal(page.$("micState").textContent, "Microphone on · diagnostic");
  // Active host voice owns USB; cached device diagnostics must not override it.
  page.state.status.voice = {active: true, stage: "thinking", turns: 0};
  await page.run("refreshStatus()");
  assert.equal(page.$("faceMode").textContent, "THINKING");
  assert.equal(page.$("micState").textContent, "Microphone off");
});

test("tabs support arrows and Home/End with one selected panel", async () => {
  const page = await app();
  await page.$("tab-conversation").fire("keydown", {key: "ArrowRight"});
  assert.equal(page.$("tab-device").attributes["aria-selected"], "true");
  assert.equal(page.$("panel-conversation").hidden, true);
  assert.equal(page.$("panel-device").hidden, false);
  await page.$("tab-device").fire("keydown", {key: "End"});
  assert.equal(page.$("panel-connection").hidden, false);
  await page.$("tab-connection").fire("keydown", {key: "Home"});
  assert.equal(page.$("panel-conversation").hidden, false);
});

test("Stop remains visible and usable in every tab during voice", async () => {
  const page = await app();
  page.state.status.voice = {active: true, stage: "waiting_for_wake", turns: 0};
  await page.run("refreshStatus()");
  for (const tab of page.groups.panel) {
    await tab.fire("click");
    const stop = page.$("voiceStop");
    assert.equal(stop.hidden || stop.markupAncestors.some(parent => parent.hidden), false,
      "Stop must stay visible in " + tab.dataset.panel);
    assert.equal(stop.disabled, false);
  }
});

test("stalled status headers or body expire, clear stale mic state and recover", async () => {
  for (const stalledPart of ["headers", "body"]) {
    const page = await app();
    page.state.status.voice = {active: true, stage: "listening", turns: 0};
    await page.run("refreshStatus()");
    page.state.hangStatus = stalledPart;
    const pending = page.run("refreshStatus()");
    await flush();
    for (const [id, timer] of page.state.timers) {
      assert.equal(timer.milliseconds, 10000);
      page.state.timers.delete(id);
      timer.callback();
    }
    await flush();
    assert.equal(page.$("micState").textContent, "Microphone status unavailable", stalledPart);
    assert.equal(page.$("voiceStop").hidden, false);
    assert.equal(page.$("voiceStop").disabled, false);
    assert.equal(page.$("connectionDot").dataset.connected, "false");
    assert.equal(await pending, false);
    page.state.hangStatus = null;
    page.state.status.voice = {active: false, stage: "off", turns: 1};
    await page.state.interval();
    assert.equal(page.$("micState").textContent, "Microphone off");
    assert.equal(page.state.timers.size, 0);
  }
});

test("Light is the default, while a saved System preference follows the OS", async () => {
  const fresh = await app({systemDark: false});
  assert.equal(fresh.$("themeSelect").value, "light");
  assert.equal(fresh.root.dataset.theme, "light");
  assert.equal(fresh.state.appearanceWrites.length, 0);
  const page = await app({savedAppearance: "system", systemDark: true});
  assert.equal(page.$("themeSelect").value, "system");
  assert.equal(page.root.dataset.theme, "dark");
  page.setSystemDark(false);
  assert.equal(page.root.dataset.theme, "light");
  assert.equal(page.state.appearanceWrites.length, 0);
});

test("a saved choice overrides the OS and only the theme is written to localStorage", async () => {
  const page = await app({savedAppearance: "light", systemDark: true});
  assert.equal(page.root.dataset.theme, "light");
  page.setSystemDark(true);
  assert.equal(page.root.dataset.theme, "light");
  page.$("themeSelect").value = "dark";
  await page.$("themeSelect").fire("change");
  page.setSystemDark(false);
  assert.equal(page.root.dataset.theme, "dark");
  assert.deepEqual(page.state.appearanceWrites, [{key: "mr-robot.appearance", value: "dark"}]);
  page.$("themeSelect").value = "system";
  await page.$("themeSelect").fire("change");
  assert.equal(page.root.dataset.theme, "light");
  page.setSystemDark(true);
  assert.equal(page.root.dataset.theme, "dark");
});

test("invalid saved appearance falls back to Light without changing stored data", async () => {
  const page = await app({savedAppearance: "invalid-value", systemDark: false});
  assert.equal(page.root.dataset.theme, "light");
  assert.equal(page.$("themeSelect").value, "light");
  assert.equal(page.state.appearanceWrites.length, 0);
});

test("unavailable appearance storage never prevents startup or a theme change", async () => {
  const page = await app({storageUnavailable: true, systemDark: false});
  assert.equal(page.$("notice").textContent, "Control Room is ready.");
  assert.equal(page.root.dataset.theme, "light");
  page.$("themeSelect").value = "light";
  await page.$("themeSelect").fire("change");
  assert.equal(page.root.dataset.theme, "light");
  assert.match(page.$("themeDescription").textContent, /this window only/);
  assert.equal(page.$("send").disabled, false);
});
