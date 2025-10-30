// @ts-nocheck
import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_BASE_URL ?? "http://localhost:8000",
        changeOrigin: true,
        secure: false
      }
    }
  },
  preview: {
    port: 4173
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src")
    }
  }
});

