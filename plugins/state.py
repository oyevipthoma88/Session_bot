import time
import logging

USER_STATE = {}
MAX_AGE = 900  # 15 minutes

def set_state(uid, step, **data):
    USER_STATE[uid] = {"step": step, "data": data, "ts": time.time()}

def get_state(uid):
    return USER_STATE.get(uid)

def clear_state(uid):
    return USER_STATE.pop(uid, None)

async def cleanup_stale():
    now = time.time()
    stale = [u for u, s in list(USER_STATE.items()) if now - s["ts"] > MAX_AGE]
    for u in stale:
        st = USER_STATE.pop(u, None)
        client = st["data"].get("client") if st else None
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
        logging.info(f"[STATE] cleaned stale uid={u}")
    return len(stale)
