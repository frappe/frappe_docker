import { defineConfig, UserConfig } from "vitepress";
import { withSidebar } from "vitepress-sidebar";

// https://vitepress.dev/reference/site-config
const vitePressOptions: UserConfig = {
  title: "Frappe Docker Docs",
  description: "Frappe in a Container",
  base: "/frappe_docker/",
  head: [["link", { rel: "icon", href: "/frappe_docker/favicon.png" }]],
  themeConfig: {
    logo: "/frappe-docker.png",
    // https://vitepress.dev/reference/default-theme-config
    nav: [{ text: "Home", link: "/" }],

    socialLinks: [
      { icon: "github", link: "https://github.com/frappe/frappe_docker/" },
    ],
  },
};

const vitePressSidebarOptions = {
  documentRootPath: ".",
  useTitleFromFrontmatter: true,
  useFolderTitleFromIndexFile: true,
};

export default defineConfig(
  withSidebar(vitePressOptions, vitePressSidebarOptions),
);
