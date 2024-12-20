from sanic import Sanic, response
import datetime
import logging
import os
import redis.asyncio as redis


logger = logging.getLogger("finicounter")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

cors_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "Content-Type"
}

app = Sanic(__name__)
    
@app.listener("after_server_start")
async def init(app):
    app.redis = redis.from_url(REDIS_URL)

@app.listener("before_server_stop")
async def cleanup(app):
    if hasattr(app, 'redis'):
        await app.redis.close()

@app.route("/api/pageViews", methods=["OPTIONS"])
async def options_handler(request):
    return response.json({}, headers=cors_headers)

@app.route("/api/pageViews", methods=["GET"])
async def get_page_views(request):
    try:
        path = request.args.get("path")
        if not path:
            return response.json({"error": "Path parameter is required"}, status=404, headers=cors_headers)
        views = await app.redis.get(path)
        views = int(views) if views else 0
        logger.info(f"Path: {path}, Views: {views}")
        return response.json({"count": views}, headers=cors_headers)
    except Exception as e:
        logger.error(f"Error while handling GET request: {e}")
        return response.json({"error": "Internal Server Error"}, status=500, headers=cors_headers)

@app.route("/api/pageViews", methods=["PUT"])
async def update_page_views(request):
    try:
        data = request.json
        path = data.get("path")
        if not path:
            return response.json({"error": "Path parameter is required"}, status=400, headers=cors_headers)
        
        # 检查键的类型并初始化
        key_type = await app.redis.type(path)
        if key_type == b'none':
            await app.redis.set(path, 0)
        
        views = await app.ctx.redis.incr(path)
        await app.redis.hset(path, "updateTime", datetime.datetime.now(datetime.timezone.utc).isoformat())
        logger.info(f"Path: {path}, Views: {views}")
        return response.empty(status=204, headers=cors_headers)
    except Exception as e:
        logger.error(f"Error while handling PUT request: {e}")
        return response.json({"error": "Internal Server Error"}, status=500, headers=cors_headers)
    


