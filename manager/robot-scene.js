import * as THREE from "./vendor/three.module.js";
import {OrbitControls} from "./vendor/OrbitControls.js";
import {RoundedBoxGeometry} from "./vendor/RoundedBoxGeometry.js";

const stage = document.getElementById("robotStage");
const face = document.getElementById("facePreview");
const canvas = document.getElementById("robotCanvas");
const buttons = document.getElementById("sceneControls");
const explode = document.getElementById("explodeRobot");
const rotate = document.getElementById("rotateRobot");
const reset = document.getElementById("resetRobot");
const motion = matchMedia("(prefers-reduced-motion: reduce)");

const partDetails = {
  display: ["AMOLED display", "The CO5300-driven 466 × 466 panel draws the pixel face, captions and Gallery images."],
  touch: ["Touch layer", "The CST9217 detects taps and swipes so Face Lab can change screens or start and cancel a voice turn."],
  pcb: ["Main circuit board", "The round PCB connects the display, processor, audio and power circuits."],
  processor: ["ESP32-S3 and flash", "The ESP32-S3 runs Face Lab or Muse. Flash holds firmware and settings, and PSRAM provides space for frames and audio buffers."],
  audio: ["Microphones and audio", "Two microphones feed the ES7210 capture circuit. The ES8311 and amplifier drive the speaker through its connector."],
  usb: ["USB-C", "Powers the board and carries firmware uploads, Control Room commands, voice audio and Gallery previews."],
  power: ["Power management", "The AXP2101 manages USB power and charging for a compatible single-cell battery through the onboard battery connector."],
  storage: ["microSD slot", "Accepts a removable microSD card. Face Lab can read card metadata. The current Gallery preview stays in PSRAM."],
  header: ["Expansion header", "The eight-pin header exposes power, serial and GPIO connections. The project’s green talk button connects through this header."]
};

function makeRobot() {
  const material = (color, roughness = .66, metalness = 0) => new THREE.MeshStandardMaterial({color, roughness, metalness});
  const glass = material(0x101b1e, .22, .23);
  const rim = material(0x20292a, .44, .2);
  const panelEdge = material(0x393f40, .5, .2);
  const pcbFinish = material(0x145584, .68);
  const ink = material(0x1a2227);
  const traces = material(0x53a1bb);
  const solder = material(0xb7cbc9, .49, .46);
  const gold = material(0xd4a44d, .45, .48);
  const connector = material(0xeae2cb);
  const phosphor = new THREE.MeshBasicMaterial({color: 0xd9ffac, toneMapped: false, fog: false});
  const warm = new THREE.MeshBasicMaterial({color: 0xffa26e, toneMapped: false, fog: false});
  const unit = new THREE.BoxGeometry();
  const discGeometry = new THREE.CylinderGeometry(1, 1, 1, 96);
  const object = new THREE.Group();
  const parts = {};

  function mesh(parent, geometry, finish, x, y, z) {
    const part = new THREE.Mesh(geometry, finish);
    part.position.set(x, y, z);
    parent.add(part);
    return part;
  }

  function box(parent, finish, x, y, z, w, h, d, radius = 0) {
    if (radius) return mesh(parent, new RoundedBoxGeometry(w, h, d, 2, radius), finish, x, y, z);
    const part = mesh(parent, unit, finish, x, y, z);
    part.scale.set(w, h, d);
    return part;
  }

  function disc(parent, finish, x, y, z, radius, depth) {
    const part = mesh(parent, discGeometry, finish, x, y, z);
    part.scale.set(radius, depth, radius);
    part.rotation.x = Math.PI / 2;
    return part;
  }

  function part(id, x, y, z) {
    const group = new THREE.Group();
    group.userData.partId = id;
    object.add(group);
    parts[id] = {group, offset: new THREE.Vector3(x, y, z)};
    return group;
  }

  function packageOnBoard(parent, x, y, size, pins) {
    box(parent, ink, x, y, -.33, size, size, .16, .035);
    box(parent, rim, x, y, -.414, size * .56, .047, .01);
    for (let index = 0; index < pins; index++) {
      const step = size * (.7 * (index / (pins - 1) - .5));
      for (const side of [-1, 1]) {
        box(parent, solder, x + step, y + side * (size / 2), -.27, .024, .13, .04);
        box(parent, solder, x + side * (size / 2), y + step, -.27, .13, .024, .04);
      }
    }
  }

  const display = part("display", -1.7, -.64, 1.95);
  disc(display, panelEdge, 0, 0, .19, 1.86, .18);
  disc(display, glass, 0, 0, .30, 1.76, .055);
  const eyes = [-.55, .55].map(x => box(display, phosphor, x, .22, .334, .25, .40, .016));
  const mouth = box(display, phosphor, 0, -.32, .334, .30, .083, .016);
  const cheeks = [-.82, .82].map(x => box(display, warm, x, -.16, .334, .16, .082, .016));
  const activity = Array.from({length: 5}, (_, index) =>
    box(display, phosphor, -.57 + index * .285, .06, .334, .125, .22, .016));

  const touch = part("touch", -.85, 1.66, 2.05);
  mesh(touch, new THREE.TorusGeometry(1.815, .043, 10, 96), rim, 0, 0, .339);
  mesh(touch, new THREE.TorusGeometry(1.835, .017, 8, 96), panelEdge, 0, 0, .296);
  const touchGlass = new THREE.MeshBasicMaterial({
    color: 0x81bdae, transparent: true, opacity: .11, depthWrite: false, side: THREE.DoubleSide, toneMapped: false
  });
  const lens = mesh(touch, new THREE.CircleGeometry(1.798, 96), touchGlass, 0, 0, .352);
  const flex = box(touch, gold, .02, -1.68, .324, .52, .35, .035, .015);

  const pcb = part("pcb", 1.28, -.05, -1.22);
  disc(pcb, rim, 0, 0, -.085, 1.879, .145);
  disc(pcb, pcbFinish, 0, 0, -.178, 1.811, .075);
  for (const [x, y] of [[0, 1.63], [-1.12, -1.18], [1.12, -1.18]]) {
    mesh(pcb, new THREE.TorusGeometry(.115, .035, 8, 16), gold, x, y, -.233);
    disc(pcb, rim, x, y, -.238, .08, .013);
  }
  for (const [x, y] of [[-1.40, .79], [-1.36, -.65], [1.31, -.78]]) {
    box(pcb, connector, x, y, -.27, .19, .23, .095, .021);
  }
  const contact = new THREE.Object3D();
  const pads = new THREE.InstancedMesh(unit, solder, 60);
  for (let index = 0; index < pads.count; index++) {
    const angle = index * 2.39996;
    const radius = .28 + (index % 12) * .111;
    contact.position.set(Math.cos(angle) * radius, Math.sin(angle) * radius, -.223);
    contact.rotation.z = (index % 4) * Math.PI / 2;
    contact.scale.set(.08, .045, .018);
    contact.updateMatrix();
    pads.setMatrixAt(index, contact.matrix);
  }
  pcb.add(pads);
  for (let i = 0; i < 9; i++) {
    const y = -.95 + i * .18;
    const points = [new THREE.Vector3(-1.35, y, -.221), new THREE.Vector3(-.78, y, -.221),
      new THREE.Vector3(-.45, y + .24, -.221), new THREE.Vector3(.87, y + .24, -.221)];
    for (let j = 0; j < points.length - 1; j++) {
      const delta = new THREE.Vector3().subVectors(points[j + 1], points[j]);
      const center = points[j].clone().addScaledVector(delta, .5);
      box(pcb, traces, center.x, center.y, center.z, delta.length(), .011, .003).rotation.z = Math.atan2(delta.y, delta.x);
    }
  }

  const processor = part("processor", .06, -1.83, 1.32);
  packageOnBoard(processor, .64, .20, .65, 8);
  packageOnBoard(processor, .41, -.68, .4, 5);
  box(processor, connector, 1.62, .03, -.248, .15, .54, .047, .018);

  const audio = part("audio", -.18, 1.73, -.55);
  packageOnBoard(audio, -.53, .75, .44, 5);
  for (const y of [.90,-.82]) {
    const mic = box(audio, solder, -1.24, y, -.30, .29, .27, .15, .035);
    mic.rotation.z = y > 0 ? -.42 : .44;
    disc(audio, ink, -1.24, y, -.382, .035, .025);
  }
  box(audio, connector, .50, 1.27, -.29, .51, .25, .13, .03);

  const usb = part("usb", -1.86, .42, .25);
  box(usb, solder, -1.74, 0, -.32, .50, .53, .27, .07);
  box(usb, ink, -2.002, 0, -.32, .022, .38, .15, .01);
  box(usb, solder, -2.019, 0, -.32, .027, .28, .045);

  const power = part("power", 1.06, 1.65, -1.5);
  packageOnBoard(power, -.53, -.19, .49, 6);
  box(power, connector, -.56, 1.28, -.29, .54, .25, .13, .03);
  for (const x of [-.69, -.43]) box(power, gold, x, 1.28, -.367, .085, .125, .029);

  const storage = part("storage", 1.90, -1.44, -.80);
  box(storage, solder, 1.11, -.58, -.19, .68, .55, .16, .035);
  box(storage, ink, 1.40, -.58, -.19, .11, .47, .085, .019);
  for (let n = 0; n < 7; n++) box(storage, gold, 1.36, -.73 + .047 * n, -.277, .12, .019, .017);

  const header = part("header", .60, -1.46, -.75);
  box(header, ink, 0, -1.36, -.29, 1.64, .25, .155, .025);
  for (let n = 0; n < 8; n++) {
    const x = -.69 + .197 * n;
    box(header, rim, x, -1.36, -.373, .131, .135, .02, .01);
    box(header, gold, x, -1.36, -.388, .055, .062, .013);
  }

  return {object, parts, eyes, mouth, cheeks, activity, phosphor, touchGlass, lens, flex};
}

function makeStage(world) {
  const grid = new THREE.GridHelper(32, 64, 0x76836a, 0x63715b);
  grid.material.transparent = true;
  grid.material.opacity = .19;
  grid.position.y = -2.13;
  world.add(grid);

  const textureCanvas = document.createElement("canvas");
  textureCanvas.width = textureCanvas.height = 128;
  const ctx = textureCanvas.getContext("2d");
  const gradient = ctx.createRadialGradient(64, 64, 15, 64, 64, 62);
  gradient.addColorStop(0, "rgba(12,16,9,.76)");
  gradient.addColorStop(.55, "rgba(12,16,9,.52)");
  gradient.addColorStop(1, "rgba(12,16,9,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 128, 128);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(6.1, 4.4),
    new THREE.MeshBasicMaterial({map: new THREE.CanvasTexture(textureCanvas), transparent: true, depthWrite: false}));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -2.12;
  world.add(shadow);
  return shadow;
}

function mount() {
  const renderer = new THREE.WebGLRenderer({canvas, alpha: true, antialias: true, powerPreference: "low-power"});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.65));
  let shaderFailed = false;
  renderer.debug.onShaderError = () => { shaderFailed = true; };
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.38;
  const world = new THREE.Scene();
  world.fog = new THREE.FogExp2(0x252c22, .056);
  world.add(new THREE.HemisphereLight(0xfdf6da, 0x667760, 2.25));
  const keyLight = new THREE.DirectionalLight(0xffe4bb, 2.8);
  keyLight.position.set(-4, 8, 5);
  world.add(keyLight);
  const edgeLight = new THREE.DirectionalLight(0xd1eacf, 2.1);
  edgeLight.position.set(3, 5, -4);
  world.add(edgeLight);

  const robot = makeRobot();
  const shadow = makeStage(world);
  world.add(robot.object);

  const camera = new THREE.OrthographicCamera(-3, 3, 3, -3, .1, 70);
  camera.position.set(3.5, 2.65, 10.2);
  const orbit = new OrbitControls(camera, canvas);
  orbit.target.set(0, -.05, 0);
  orbit.enablePan = false;
  orbit.enableZoom = false;
  orbit.rotateSpeed = .7;
  orbit.minPolarAngle = .55;
  orbit.maxPolarAngle = 1.51;
  orbit.update();
  orbit.saveState();

  let inView = false;
  let frame = 0;
  let lastDraw = 0;
  let width = 0;
  let height = 0;
  let spread = 0;
  let selectedPart = "display";
  const inspector = document.getElementById("partsInspector");
  const optionList = document.getElementById("partOptions");
  const orbitHint = document.getElementById("orbitHint");
  const activePart = document.getElementById("activePart");
  const partButtons = new Map();
  const outline = new THREE.BoxHelper(robot.parts.display.group, 0xd9ffac);
  outline.visible = false;
  world.add(outline);

  function inspect(id) {
    selectedPart = id;
    const [name, description] = partDetails[id];
    activePart.textContent = name;
    document.getElementById("partTitle").textContent = name;
    document.getElementById("partDescription").textContent = description;
    for (const [partId, button] of partButtons) button.setAttribute("aria-pressed", String(id === partId));
    schedule();
  }

  for (const [id, [name]] of Object.entries(partDetails)) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = name;
    button.addEventListener("click", () => inspect(id));
    optionList.append(button);
    partButtons.set(id, button);
  }
  inspect(selectedPart);

  const ray = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let press = null;
  canvas.addEventListener("pointerdown", event => {
    press = event.isPrimary && event.button === 0 ? {id: event.pointerId, x: event.clientX, y: event.clientY} : null;
  });
  canvas.addEventListener("pointercancel", () => { press = null; });
  canvas.addEventListener("pointerup", event => {
    const start = press;
    press = null;
    if (!start || start.id !== event.pointerId || explode.getAttribute("aria-pressed") !== "true" ||
        Math.hypot(event.clientX - start.x, event.clientY - start.y) > 7) return;
    const rect = canvas.getBoundingClientRect();
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, 1 - (event.clientY - rect.top) / rect.height * 2);
    ray.setFromCamera(pointer, camera);
    const hit = ray.intersectObject(robot.object, true).find(({object}) => object.visible);
    let group = hit?.object;
    while (group && !group.userData.partId) group = group.parent;
    if (group) inspect(group.userData.partId);
  });

  function draw(now) {
    const time = motion.matches ? 0 : now / 1000;
    const desired = explode.getAttribute("aria-pressed") === "true" ? 1 : 0;
    if (motion.matches || Math.abs(desired - spread) < .003) spread = desired;
    else spread = THREE.MathUtils.lerp(spread, desired, .18);
    for (const {group, offset} of Object.values(robot.parts)) group.position.copy(offset).multiplyScalar(spread);
    // Turn the PCB toward the viewer so the rear traces and pads can be inspected.
    robot.parts.pcb.group.rotation.y = Math.PI * spread;
    robot.lens.visible = spread > .1;
    robot.flex.visible = spread > .1;
    robot.touchGlass.opacity = selectedPart === "touch" ? .24 : .11;
    outline.visible = desired === 1;
    if (outline.visible) {
      const group = robot.parts[selectedPart].group;
      if (outline.object !== group) outline.object = group;
      outline.update();
    }
    shadow.scale.setScalar(1 + .14 * spread);
    const zoom = 1 / (1 + .55 * spread);
    if (camera.zoom !== zoom) {
      camera.zoom = zoom;
      camera.updateProjectionMatrix();
    }

    const state = face.dataset.state;
    const reaction = face.dataset.reaction;
    const style = face.classList;
    const thinking = ["thinking", "receiving", "creating"].includes(state);
    const listening = state === "listening";
    const speaking = state === "speaking";
    const showActivity = listening || thinking;
    robot.phosphor.color.setHex(state === "error" ? 0xff8461 : listening ? 0xffc888 : thinking ? 0xb6daff : style.contains("orbit") ? 0xdfc6ff : style.contains("classic") ? 0xa3ffe4 : 0xd9ffac);
    const blink = !motion.matches && time % 5 > 4.88;
    robot.eyes.forEach((eye, index) => {
      eye.visible = !showActivity;
      let height = blink || style.contains("sleepy") || (index === 1 && style.contains("wink")) ? .18 :
        reaction === "happy" || state === "done" || style.contains("happy") ? .40 :
          style.contains("surprised") || (index === 1 && (reaction === "curious" || style.contains("curious"))) ? 1.33 : 1;
      if (style.contains("squint") && index === 1) height = .46;
      eye.scale.y = .40 * height;
      eye.rotation.z = style.contains("dizzy") ? (index ? -.56 : .56) :
        reaction === "soft" || style.contains("concerned") ? (index ? -.24 : .24) : 0;
    });
    robot.mouth.visible = !showActivity;
    robot.mouth.scale.y = .083 * (speaking ? Math.max(1.1, 3 * Math.abs(Math.sin(time * 14))) : style.contains("surprised") ? 2 : 1);
    robot.cheeks.forEach(cheek => { cheek.visible = !showActivity && style.contains("blush"); });
    robot.activity.forEach((bar, index) => {
      bar.visible = showActivity;
      bar.scale.y = .22 * (thinking ? .55 : .65 + .9 * Math.abs(Math.sin(time * 7 + index)));
      bar.position.y = thinking ? .06 + .10 * Math.sin(time * 5 - index) : .06;
    });

    renderer.render(world, camera);
    stage.dataset.scene = shaderFailed ? "fallback" : "ready";
    buttons.hidden = shaderFailed;
    activePart.hidden = shaderFailed || !desired;
  }

  function schedule() {
    if (!frame && width && inView && !shaderFailed && !document.hidden && stage.dataset.scene !== "lost") {
      frame = requestAnimationFrame(tick);
    }
  }

  function tick(now) {
    frame = 0;
    if (!inView || document.hidden || stage.dataset.scene === "lost") return;
    if (motion.matches || now - lastDraw >= 28) {
      lastDraw = now;
      draw(now);
    }
    if (!motion.matches) schedule();
  }

  function resize() {
    ({clientWidth: width, clientHeight: height} = stage);
    if (!width || !height) return;
    const aspect = width / height;
    const span = Math.max(2.67, 2.72 / aspect);
    camera.top = span;
    camera.bottom = -span;
    camera.left = -span * aspect;
    camera.right = span * aspect;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
    // Resizing resets the canvas buffer. Paint one frame even below the fold.
    if (!document.hidden && stage.dataset.scene !== "lost") draw(performance.now());
    schedule();
  }

  explode.addEventListener("click", () => {
    const open = explode.getAttribute("aria-pressed") === "true";
    explode.setAttribute("aria-pressed", String(!open));
    explode.textContent = open ? "Exploded view" : "Assemble robot";
    inspector.hidden = open;
    orbitHint.textContent = open ? "Drag to rotate" : "Click a part";
    if (!open) orbit.reset();
    schedule();
  });
  rotate.addEventListener("click", () => {
    const offset = new THREE.Vector3().subVectors(camera.position, orbit.target);
    offset.applyAxisAngle(camera.up, Math.PI / 5);
    camera.position.copy(orbit.target).add(offset);
    orbit.update();
    schedule();
  });
  reset.addEventListener("click", () => { orbit.reset(); schedule(); });
  orbit.addEventListener("change", schedule);
  new ResizeObserver(resize).observe(stage);
  new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; schedule(); }).observe(stage);
  new MutationObserver(schedule).observe(face, {attributes: true, attributeFilter: ["class", "data-state", "data-reaction"]});
  motion.addEventListener("change", schedule);
  document.addEventListener("visibilitychange", schedule);
  canvas.addEventListener("webglcontextlost", event => {
    event.preventDefault();
    stage.dataset.scene = "lost";
    buttons.hidden = true;
    activePart.hidden = true;
  });
  canvas.addEventListener("webglcontextrestored", () => {
    shaderFailed = false;
    stage.dataset.scene = "restoring";
    schedule();
  });
}

try {
  mount();
} catch (_) {
  stage.dataset.scene = "fallback";
}
