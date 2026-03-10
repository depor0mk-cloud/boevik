import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
import { bot } from "./src/bot.js";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  // Health check / API routes
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", bot: "running" });
  });

  // Start the Telegram Bot
  try {
    bot.start();
    console.log("🤖 Telegram Bot started successfully");
  } catch (error) {
    console.error("❌ Failed to start Telegram Bot:", error);
  }

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    // Serve static files in production
    app.use(express.static(path.join(__dirname, "dist")));
    app.get("*", (req, res) => {
      res.sendFile(path.join(__dirname, "dist", "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`🌐 Web server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
