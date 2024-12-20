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

async def setup_redis(app):
    app.redis = redis.from_url(REDIS_URL)
    
async def close_redis(app):
    if hasattr(app, 'redis'):
        await app.redis.close()
        
@app.listener('before_server_start')
async def init(app, loop):
    await setup_redis(app)

@app.listener('after_server_stop')
async def cleanup(app, loop):
    await close_redis(app)

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
        views = await app.redis.incr(path)
        await app.redis.hset(path, "updateTime", datetime.datetime.now(datetime.timezone.utc).isoformat())
        logger.info(f"Path: {path}, Views: {views}")
        return response.empty(status=204, headers=cors_headers)
    except Exception as e:
        logger.error(f"Error while handling PUT request: {e}")
        return response.json({"error": "Internal Server Error"}, status=500, headers=cors_headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, fast=True)

