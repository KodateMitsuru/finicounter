from sanic import Sanic, response
import datetime
import logging
import os
import pymongo


logger = logging.getLogger("finicounter")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)

MONGODB_URL = os.environ.get("MONGODB_URL")
DB_NAME = os.environ.get("DB_NAME") if os.environ.get("DB_NAME") is not None else "MyCounter"
COLLECTION_NAME = "Counter"

cors_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "Content-Type"
}

mongoClient = pymongo.MongoClient(MONGODB_URL)
db = mongoClient[DB_NAME]
collection = db[COLLECTION_NAME]

app = Sanic("finicounter")

@app.route("/api/pageViews", methods=["OPTIONS"])
async def options_handler(request):
    return response.json({}, headers=cors_headers)

@app.route("/api/pageViews", methods=["GET"])
async def get_page_views(request):
    path = request.args.get("path")
    if not path:
        return response.json({"error": "Path parameter is required"}, status=404, headers=cors_headers)
    result = collection.find_one({"path": path})
    logger.info(f"Path: {path}, Result: {result}")
    views = result["views"] if result else 0
    return response.json({"count": views}, headers=cors_headers)

@app.route("/api/pageViews", methods=["PUT"])
async def update_page_views(request):
    data = request.json
    path = data.get("path")
    if not path:
        return response.json({"error": "Path parameter is required"}, status=400, headers=cors_headers)
    logger.info(f"Path: {path}")
    result = collection.find_one_and_update(
        {"path": path},
        {"$inc": {"views": 1}, "$set": {"updateTime": datetime.datetime.now(datetime.timezone.utc)}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER,
        maxTimeMS=50
    )
    logger.info(f"Path: {path}, Result: {result}")
    return response.empty(status=204, headers=cors_headers)

