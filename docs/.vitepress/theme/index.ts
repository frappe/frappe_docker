import DefaultTheme from "vitepress/theme";
import type { Theme } from "vitepress";
import { defineAsyncComponent } from "vue";

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component(
      "PeleDiagram",
      defineAsyncComponent(() => import("./PeleDiagram.vue")),
    );
  },
} satisfies Theme;
