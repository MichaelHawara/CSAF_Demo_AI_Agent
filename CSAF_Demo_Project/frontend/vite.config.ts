import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import open from "open";

export default defineConfig({
  plugins: [
    react(),
    {
      name: "open-control-monitor-tab",
      configureServer(server) {
        server.httpServer?.once("listening", () => {
          const address = server.httpServer?.address();
          const port = typeof address === "object" && address ? address.port : 5173;
          void open(`http://localhost:${port}/control`);
        });
      },
    },
  ],
  server: {
    port: 5173,
    open: true,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
