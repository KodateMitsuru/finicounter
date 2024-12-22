const express = require("express");
const Redis = require("ioredis");
const app = express();
app.use(express.json());

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const redis = new Redis(REDIS_URL);

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "*",
  "Access-Control-Allow-Headers": "Content-Type",
};

app.options("/api/pageViews", (req, res) => {
  res.set(corsHeaders).json({});
});

app.get("/api/pageViews", async (req, res) => {
  try {
    const path = req.query.path;
    if (!path) return res.set(corsHeaders).status(404).json({ error: "Path parameter is required" });
    let views = await redis.get(path);
    views = parseInt(views) || 0;
    res.set(corsHeaders).json({ count: views });
  } catch (e) {
    res.set(corsHeaders).status(500).json({ error: "Internal Server Error" });
  }
});

app.put("/api/pageViews", async (req, res) => {
  try {
    const path = req.body.path;
    if (!path) return res.set(corsHeaders).status(400).json({ error: "Path parameter is required" });

    const keyType = await redis.type(path);
    if (keyType !== "string" && keyType !== "none") {
      return res.set(corsHeaders).status(400).json({ error: "Key type mismatch" });
    }
    if (keyType === "none") {
      await redis.set(path, 0);
    }
    await redis.incr(path);
    res.set(corsHeaders).status(204).send();
  } catch (e) {
    res.set(corsHeaders).status(500).json({ error: `${e}` });
  }
});

// 错误处理中间件
app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({ error: "Invalid JSON" });
  }
  next();
});

app.listen(8000, () => console.log("Server running on port 8000"));


