// electron.vite.config.ts
import { defineConfig, externalizeDepsPlugin } from "electron-vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "path";
import { copyFileSync, existsSync, mkdirSync } from "fs";
var __electron_vite_injected_dirname = "P:\\zorivest\\ui";
var electron_vite_config_default = defineConfig({
  main: {
    plugins: [
      externalizeDepsPlugin(),
      {
        name: "copy-splash-assets",
        closeBundle() {
          const destDir = resolve(__electron_vite_injected_dirname, "out/main");
          if (!existsSync(destDir)) mkdirSync(destDir, { recursive: true });
          copyFileSync(resolve(__electron_vite_injected_dirname, "src/main/splash.html"), resolve(destDir, "splash.html"));
          copyFileSync(resolve(__electron_vite_injected_dirname, "src/main/splash-icon.png"), resolve(destDir, "splash-icon.png"));
        }
      }
    ]
  },
  preload: {
    plugins: [externalizeDepsPlugin()]
  },
  renderer: {
    server: {
      port: 7173
    },
    resolve: {
      alias: {
        "@": resolve("src/renderer/src")
      }
    },
    plugins: [
      react({
        babel: {
          plugins: [["babel-plugin-react-compiler", {}]]
        }
      }),
      tailwindcss()
    ]
  }
});
export {
  electron_vite_config_default as default
};
