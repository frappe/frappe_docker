<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { mount, type Mounted } from "pele";

const props = defineProps<{ source: string }>();
const source = computed(() => decodeURIComponent(props.source));
const trigger = ref<HTMLElement>();
const inline = ref<HTMLElement>();
const dialog = ref<HTMLDialogElement>();
const canvas = ref<HTMLElement>();
const scale = ref("100%");
const message = ref("");
const error = ref("");
const ready = ref(false);
let diagram: Mounted | undefined;
let viewer: Mounted | undefined;
let observer: MutationObserver | undefined;
let previousOverflow = "";

onMounted(async () => {
  await document.fonts.ready;
  if (!inline.value) return;
  diagram = mount(inline.value, source.value, {
    autoDirection: false,
    zoom: false,
    onError: (reason) => {
      error.value = String(reason);
    },
    onRender: () => {
      error.value = "";
      ready.value = true;
    },
  });
});

watch(source, (text) => {
  diagram?.update(text);
  viewer?.update(text);
});

function updateScale() {
  const zoom = viewer?.zoom;
  scale.value = zoom ? `${Math.round((100 * zoom.scale) / zoom.fit)}%` : "100%";
}

function openViewer() {
  if (
    !diagram?.result ||
    error.value ||
    !dialog.value ||
    dialog.value.open ||
    !canvas.value
  )
    return;
  previousOverflow = document.body.style.overflow;
  dialog.value.showModal();
  document.body.style.overflow = "hidden";
  viewer = mount(canvas.value, source.value, {
    autoDirection: false,
    zoom: { controls: false, always: true, maxScale: 5 },
  });
  observer = new MutationObserver(updateScale);
  observer.observe(canvas.value, {
    subtree: true,
    attributes: true,
    attributeFilter: ["viewBox", "style"],
  });
  updateScale();
  canvas.value.querySelector<SVGElement>("svg")?.focus();
}

function closed() {
  observer?.disconnect();
  viewer?.destroy();
  viewer = undefined;
  document.body.style.overflow = previousOverflow;
  trigger.value?.focus({ preventScroll: true });
  message.value = "";
}

function keydown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopPropagation();
    dialog.value?.close();
    return;
  }
  if (
    event.ctrlKey ||
    event.metaKey ||
    event.altKey ||
    canvas.value?.contains(event.target as Node)
  )
    return;
  if (
    [
      "+",
      "=",
      "-",
      "0",
      "ArrowLeft",
      "ArrowRight",
      "ArrowUp",
      "ArrowDown",
    ].includes(event.key)
  ) {
    event.preventDefault();
    canvas.value?.dispatchEvent(
      new KeyboardEvent("keydown", { key: event.key }),
    );
  }
}

function wheel(event: WheelEvent) {
  if (event.ctrlKey || event.metaKey) return;
  event.preventDefault();
  // Keep ordinary wheel zoom in fullscreen, using Pele's pointer-centered zoom.
  canvas.value?.dispatchEvent(
    new WheelEvent("wheel", {
      deltaY: event.deltaY,
      clientX: event.clientX,
      clientY: event.clientY,
      ctrlKey: true,
    }),
  );
}

async function copySource() {
  try {
    await navigator.clipboard.writeText(source.value);
    message.value = "Diagram source copied.";
  } catch {
    message.value = "Could not copy the diagram source.";
  }
}

function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

async function exportDiagram(format: "svg" | "png") {
  try {
    // Export the unzoomed inline diagram and resolve its inherited theme colors.
    const original = inline.value?.querySelector("svg");
    if (!original) return;
    const svg = original.cloneNode(true) as SVGSVGElement;
    const styles = getComputedStyle(original);
    for (const name of styles) {
      if (name.startsWith("--pele-"))
        svg.style.setProperty(name, styles.getPropertyValue(name));
    }
    svg.style.removeProperty("max-width");
    const markup = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([markup], { type: "image/svg+xml" });
    if (format === "svg") {
      download(blob, "diagram.svg");
      return;
    }
    const image = new Image();
    const url = URL.createObjectURL(blob);
    try {
      await new Promise<void>((resolve, reject) => {
        image.onload = () => resolve();
        image.onerror = reject;
        image.src = url;
      });
      const size = svg.viewBox.baseVal;
      const factor = Math.min(2, 4096 / Math.max(size.width, size.height));
      const output = document.createElement("canvas");
      output.width = Math.ceil(size.width * factor);
      output.height = Math.ceil(size.height * factor);
      const context = output.getContext("2d")!;
      context.fillStyle = styles.getPropertyValue("--pele-bg").trim();
      context.fillRect(0, 0, output.width, output.height);
      context.drawImage(image, 0, 0, output.width, output.height);
      const png = await new Promise<Blob | null>((resolve) =>
        output.toBlob(resolve),
      );
      if (!png) throw new Error("PNG export failed");
      download(png, "diagram.png");
    } finally {
      URL.revokeObjectURL(url);
    }
  } catch {
    message.value = "Could not download the diagram.";
  }
}

onBeforeUnmount(() => {
  diagram?.destroy();
  observer?.disconnect();
  viewer?.destroy();
  if (dialog.value?.open) {
    dialog.value.close();
    document.body.style.overflow = previousOverflow;
  }
});
</script>

<template>
  <p v-if="error" role="alert">{{ error }}</p>
  <figure
    ref="trigger"
    class="pele-diagram"
    role="button"
    tabindex="0"
    :aria-busy="!ready && !error"
    :aria-disabled="!ready || !!error"
    aria-label="Open diagram in fullscreen viewer"
    @click="openViewer"
    @keydown.enter.prevent="openViewer"
    @keydown.space.prevent="openViewer"
  >
    <span v-if="!ready && !error" role="status">Loading diagram…</span>
    <div ref="inline" />
  </figure>
  <Teleport to="body">
    <dialog
      ref="dialog"
      class="pele-dialog"
      aria-label="Diagram viewer"
      @close="closed"
      @keydown.capture="keydown"
    >
      <div class="pele-toolbar" role="toolbar" aria-label="Diagram controls">
        <output aria-label="Zoom level" aria-live="polite">{{ scale }}</output>
        <button type="button" aria-label="Close" @click="dialog?.close()">
          ✕
        </button>
        <button
          type="button"
          aria-label="Zoom in"
          @click="viewer?.zoom?.zoomBy(1.25)"
        >
          +
        </button>
        <button
          type="button"
          aria-label="Zoom out"
          @click="viewer?.zoom?.zoomBy(0.8)"
        >
          −
        </button>
        <button
          type="button"
          aria-label="Reset zoom"
          @click="viewer?.zoom?.reset()"
        >
          ↻
        </button>
        <button
          type="button"
          aria-label="Copy diagram source"
          @click="copySource"
        >
          Copy
        </button>
        <button
          type="button"
          aria-label="Download SVG"
          @click="exportDiagram('svg')"
        >
          SVG
        </button>
        <button
          type="button"
          aria-label="Download PNG"
          @click="exportDiagram('png')"
        >
          PNG
        </button>
        <span class="pele-status" role="status">{{ message }}</span>
      </div>
      <div ref="canvas" class="pele-canvas" @wheel="wheel" />
    </dialog>
  </Teleport>
</template>

<style scoped>
.pele-diagram,
.pele-dialog {
  --pele-bg: var(--vp-c-bg);
  --pele-fg: var(--vp-c-text-1);
  --pele-muted: var(--vp-c-text-2);
  --pele-line: var(--vp-c-text-2);
  --pele-surface: var(--vp-c-bg-soft);
  --pele-surface-alt: var(--vp-c-bg-alt);
  --pele-border: var(--vp-c-text-3);
  --pele-accent: var(--vp-c-brand-1);
  --pele-font: var(--vp-font-family-base);
}
.pele-diagram {
  margin: 16px 0;
  padding: 16px;
  cursor: zoom-in;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 5%);
  transition:
    border-color 200ms ease,
    box-shadow 200ms ease,
    transform 200ms ease;
}
@media (hover: hover) and (pointer: fine) {
  .pele-diagram[aria-disabled="false"]:hover {
    border-color: var(--vp-c-brand-1);
    box-shadow: 0 4px 16px rgb(0 0 0 / 10%);
    transform: translateY(-2px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .pele-diagram {
    transition: none;
  }
  .pele-diagram[aria-disabled="false"]:hover {
    transform: none;
  }
}
.pele-diagram:focus-visible,
button:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 3px;
}
.pele-dialog {
  position: fixed;
  inset: 0;
  width: 100%;
  max-width: none;
  height: 100%;
  max-height: none;
  margin: 0;
  border: 0;
  padding: 0;
  color: var(--vp-c-text-1);
  background: var(--vp-c-bg);
}
.pele-canvas {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 80px 16px 16px;
  overflow: hidden;
}
.pele-canvas :deep(svg) {
  width: auto;
  max-width: 100%;
  max-height: 100%;
}
.pele-toolbar {
  position: absolute;
  z-index: 1;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
  max-width: calc(100% - 24px);
  padding: 8px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg-soft);
}
button,
output {
  min-width: 36px;
  padding: 6px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 4px;
  font: inherit;
  font-size: 14px;
  color: inherit;
}
button {
  cursor: pointer;
}
button:hover {
  background: var(--vp-c-bg-alt);
}
.pele-status {
  font-size: 12px;
}
@media (max-width: 600px) {
  .pele-canvas {
    padding-top: 128px;
  }
}
</style>
