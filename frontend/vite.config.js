import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";
import { defineConfig } from "vite";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  build: {
    outDir: resolve(__dirname, "../src/flask_vite_demo/static/dist"),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "src/main.js"),
        style: resolve(__dirname, "src/main.css"),
      },
    },
  },
});
