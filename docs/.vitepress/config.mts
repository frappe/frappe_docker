import { defineConfig } from "vitepress";
import { withSidebar } from "vitepress-sidebar";

// https://vitepress.dev/reference/site-config
const vitePressOptions = {
  title: "Frappe Docker Docs",
  description: "Frappe in a Container",
  base: "/frappe_docker/",
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
  documentRootPath: "./docs",
  useTitleFromFrontmatter: true,
  useFolderTitleFromIndexFile: true,
};

export default defineConfig(
  withSidebar(vitePressOptions, vitePressSidebarOptions)
);
