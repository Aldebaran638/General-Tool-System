import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
  server: {
    // Proxy API requests to the backend so the frontend and API share the
    // same origin. This is required for:
    //   1. Local dev (avoids CORS preflight failures)
    //   2. WeCom H5 (cloudflare tunnel → Vite → backend works on mobile)
    proxy: {
      "/api": {
        target: process.env.BACKEND_URL ?? "http://localhost:8000",
        changeOrigin: true,
      },
      "/WW_verify_HUz4rWBElVbwEoOX.txt": {
        target: process.env.BACKEND_URL ?? "http://localhost:8000",
        changeOrigin: true,
      },
      "/uploads": {
        target: process.env.BACKEND_URL ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
