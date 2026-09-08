import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "..", "");
  if (mode !== "production" && !env.API_KEY) {
    throw new Error("API_KEY must be configured in the root .env file");
  }

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: true,
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
          ...(env.API_KEY ? { headers: { "X-API-Key": env.API_KEY } } : {}),
        },
      },
    },
  };
});
