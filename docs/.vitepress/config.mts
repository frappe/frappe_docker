import { defineConfig, UserConfig } from "vitepress";
import { withSidebar } from "vitepress-sidebar";

// https://vitepress.dev/reference/site-config
const vitePressOptions: UserConfig = {
  title: "Frappe Docker Docs",
  description: "Frappe in a Container",
  base: "/frappe_docker/",
  head: [["link", { rel: "icon", href: "/frappe_docker/favicon.png" }]],
  markdown: {
    config(md) {
      const fence = md.renderer.rules.fence!;
      md.renderer.rules.fence = (tokens, index, options, env, self) => {
        const token = tokens[index];
        if (["mermaid", "mmd"].includes(token.info.trim())) {
          return `<ClientOnly><PeleDiagram source="${encodeURIComponent(token.content)}" /></ClientOnly>`;
        }
        return fence(tokens, index, options, env, self);
      };
    },
  },
  themeConfig: {
    logo: "/frappe-docker.png",
    // https://vitepress.dev/reference/default-theme-config
    nav: [{ text: "Home", link: "/" }],

    socialLinks: [
      { icon: "github", link: "https://github.com/frappe/frappe_docker/" },
    ],
    search: {
      provider: "local",
    },
  },
};

const vitePressSidebarOptions = {
  documentRootPath: ".",
  useTitleFromFrontmatter: true,
  useFolderTitleFromIndexFile: true,
  useFolderLinkFromIndexFile: true,
};

export default defineConfig(
  withSidebar(vitePressOptions, vitePressSidebarOptions),
);
