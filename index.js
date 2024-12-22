const express = require("express");
const Redis = require("ioredis");
const cors = require("cors");
const app = express();
app.use(express.json());

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const redis = new Redis(REDIS_URL);

const corsOptions = {
  origin: "*",
  methods: "*",
  allowedHeaders: "Content-Type"
};

app.use(cors(corsOptions));

app.options("/api/pageViews", cors(corsOptions), (req, res) => {
  res.json({});
});

app.get("/api/pageViews", cors(corsOptions), async (req, res) => {
  try {
    const path = req.query.path;
    const pathRegex = /^\/posts\/\d{4}\/\d{2}\/\d{2}\/.+\/$/;
    if (!path || !pathRegex.test(path)) {
      return res.status(404).json({ error: "Invalid path format" });
    }
    let views = await redis.get(path);
    views = parseInt(views) || 0;
    res.json({ count: views });
  } catch (e) {
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.put("/api/pageViews", cors(corsOptions), async (req, res) => {
  try {
    const path = req.body.path;
    const pathRegex = /^\/posts\/\d{4}\/\d{2}\/\d{2}\/.+\/$/;
    if (!path || !pathRegex.test(path)) {
      return res.status(400).json({ error: "Invalid path format" });
    }

    const keyType = await redis.type(path);
    if (keyType !== "string" && keyType !== "none") {
      return res.status(400).json({ error: "Key type mismatch" });
    }
    if (keyType === "none") {
      await redis.set(path, 0);
    }
    await redis.incr(path);
    res.status(204).send();
  } catch (e) {
    res.status(500).json({ error: `${e}` });
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


