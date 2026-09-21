import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, "../web/canvas"),
    emptyOutDir: true,
    lib: {
      entry: path.resolve(__dirname, "src/main.jsx"),
      name: "ATERecipeCanvas",
      formats: ["iife"],
      fileName: () => "recipe-canvas.js",
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
        assetFileNames: "recipe-canvas.[ext]",
      },
    },
  },
});
