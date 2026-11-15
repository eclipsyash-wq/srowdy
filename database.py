# database.py - MongoDB Database for 𝗥𝗔𝗭𝗢𝗥 𝗫 𝗕𝗼𝘁
import os
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

PAID_PLANS = ["Core", "Elite", "Root", "X", "Custom"]

# MongoDB Connection with optimized pooling
MONGO_URL = os.getenv("MONGO_URL", "")
client = AsyncIOMotorClient(
    MONGO_URL,
    maxPoolSize=500,
    minPoolSize=50,
    maxIdleTimeMS=60000,
    connectTimeoutMS=10000,
    serverSelectionTimeoutMS=10000,
    socketTimeoutMS=30000,
    retryWrites=True,
    retryReads=True,
    w="majority",
    journal=False,
    compressors="zlib"
)
DB_NAME = os.getenv("DB_NAME", "razor_x_bot")
db = client[DB_NAME]

# Collections
users_col = db["users"]
keys_col = db["keys"]
proxies_col = db["proxies"]
sites_col = db["sites"]
cards_col = db["cards"]
global_sites_col = db["global_sites"]
joined_col = db["joined_users"]
feedback_col = db["feedbacks"]


async def init_db():
    """𝗜𝗻𝗶𝘁𝗶𝗮𝗹𝗶𝘇𝗲 𝗱𝗮𝘁𝗮𝗯𝗮𝘀𝗲 𝘄𝗶𝘁𝗵 𝗶𝗻𝗱𝗲𝘅𝗲𝘀"""
    try:
        # Drop conflicting indexes first
        try:
            await proxies_col.drop_index("user_id_1_proxy_url_1")
        except Exception:
            pass
        try:
            await proxies_col.drop_index("user_id_1_gate_1_proxy_url_1")
        except Exception:
            pass
        try:
            await sites_col.drop_index("user_id_1_site_1")
        except Exception:
            pass

        await users_col.create_index("user_id", unique=True, background=True)
        await keys_col.create_index("key", unique=True, background=True)
        await keys_col.create_index("status", background=True)
        await keys_col.create_index("key_expires_at", background=True)
        await keys_col.create_index("assigned_to", background=True)
        await proxies_col.create_index([("user_id", 1), ("gate", 1), ("proxy_url", 1)], background=True)
        await proxies_col.create_index([("user_id", 1), ("gate", 1)], background=True)
        await sites_col.create_index([("user_id", 1), ("site", 1)], background=True)
        await global_sites_col.create_index("site", unique=True, background=True)
        await cards_col.create_index("created_at", background=True)
        await cards_col.create_index("status", background=True)
        await joined_col.create_index("user_id", unique=True, background=True)
        await feedback_col.create_index("user_id", background=True)
        await feedback_col.create_index("created_at", background=True)
        await users_col.create_index("plan", background=True)
        await users_col.create_index("banned", background=True)
        await proxies_col.create_index("user_id", background=True)
        await sites_col.create_index("user_id", background=True)
        try:
            await migrate_proxy_gates()
        except Exception as mig_e:
            print(f"⚠︎ 𝗣𝗿𝗼𝘅𝘆 𝗴𝗮𝘁𝗲 𝗺𝗶𝗴𝗿𝗮𝘁𝗶𝗼𝗻: {mig_e}")
        print("✓ 𝗥𝗔𝗭𝗢𝗥 𝗫 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲 𝗶𝗻𝗶𝘁𝗶𝗮𝗹𝗶𝘇𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!")
    except Exception as e:
        print(f"⚠︎ 𝗗𝗕 𝗶𝗻𝗶𝘁 𝘄𝗮𝗿𝗻𝗶𝗻𝗴: {e}")


# ============ 𝗨𝗦𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧 ============

async def ensure_user(user_id: int, name: str = None, username: str = None):
    """𝗘𝗻𝘀𝘂𝗿𝗲 𝘂𝘀𝗲𝗿 𝗲𝘅𝗶𝘀𝘁𝘀 𝗶𝗻 𝗗𝗕"""
    try:
        update_doc = {}
        if name:
            update_doc["name"] = name
        if username:
            update_doc["username"] = username
            
        if update_doc:
            await users_col.update_one(
                {"user_id": user_id},
                {
                    "$setOnInsert": {
                        "user_id": user_id,
                        "plan": "Trial",
                        "expiry": None,
                        "banned": False,
                        "banned_by": None,
                        "credits": 250,
                        "created_at": datetime.datetime.utcnow()
                    },
                    "$set": update_doc
                },
                upsert=True
            )
        else:
            await users_col.update_one(
                {"user_id": user_id},
                {"$setOnInsert": {
                    "user_id": user_id,
                    "plan": "Trial",
                    "expiry": None,
                    "banned": False,
                    "banned_by": None,
                    "credits": 250,
                    "created_at": datetime.datetime.utcnow()
                }},
                upsert=True
            )
    except Exception:
        pass


async def check_and_expire_plan(user_id: int) -> str | None:
    """Downgrade an expired paid plan to Trial. Returns the previous plan tier, or None."""
    now = datetime.datetime.utcnow()
    old = await users_col.find_one_and_update(
        {
            "user_id": user_id,
            "plan": {"$in": PAID_PLANS},
            "expiry": {"$lt": now},
        },
        {
            "$set": {
                "plan": "Trial",
                "expiry": None,
                "pending_expiry_notify": True,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.BEFORE,
    )
    if not old:
        return None
    plan = old.get("plan", "Trial")
    return "Trial" if plan == "Bronze" else plan


async def get_user_plan(user_id: int) -> str:
    """𝗚𝗲𝘁 𝘂𝘀𝗲𝗿'𝘀 𝗰𝘂𝗿𝗿𝗲𝗻𝘁 𝗽𝗹𝗮𝗻"""
    expired_plan = await check_and_expire_plan(user_id)
    if expired_plan:
        return "Trial"

    user = await users_col.find_one({"user_id": user_id}, {"plan": 1})
    if not user:
        return "Trial"

    plan = user.get("plan", "Trial")
    if plan == "Bronze":
        return "Trial"
    return plan


async def set_user_plan(user_id: int, plan: str, days: int = 0):
    """𝗦𝗲𝘁 𝘂𝘀𝗲𝗿 𝗽𝗹𝗮𝗻 𝘄𝗶𝘁𝗵 𝗲𝘅𝗽𝗶𝗿𝘆"""
    expiry = None
    if days > 0:
        expiry = datetime.datetime.utcnow() + datetime.timedelta(days=days)

    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "plan": plan,
            "expiry": expiry,
            "premium_days": days,
            "updated_at": datetime.datetime.utcnow()
        },
        "$unset": {
            "pending_expiry_notify": "",
            "plan_expiry_notified": "",
        }},
        upsert=True
    )


async def is_premium_user(user_id: int) -> bool:
    """𝗖𝗵𝗲𝗰𝗸 𝗶𝗳 𝘂𝘀𝗲𝗿 𝗵𝗮𝘀 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗽𝗹𝗮𝗻"""
    plan = await get_user_plan(user_id)
    return plan in PAID_PLANS


async def get_user_expiry(user_id: int):
    """Return active plan expiry datetime, or None."""
    await check_and_expire_plan(user_id)
    user = await users_col.find_one({"user_id": user_id}, {"expiry": 1, "plan": 1})
    if not user:
        return None
    if user.get("plan") not in PAID_PLANS:
        return None
    return user.get("expiry")


async def is_banned_user(user_id: int) -> bool:
    """𝗖𝗵𝗲𝗰𝗸 𝗶𝗳 𝘂𝘀𝗲𝗿 𝗶𝘀 𝗯𝗮𝗻𝗻𝗲𝗱"""
    user = await users_col.find_one({"user_id": user_id}, {"banned": 1})
    return user.get("banned", False) if user else False


# ============ CREDITS ============

async def get_user_credits(user_id: int):
    user = await users_col.find_one({"user_id": user_id}, {"credits": 1})
    if not user:
        return 0
    return user.get("credits", 0)


async def set_user_credits(user_id: int, amount: int):
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"credits": amount}},
        upsert=True
    )


async def add_user_credits(user_id: int, amount: int):
    await users_col.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": amount}},
        upsert=True
    )


async def deduct_credit(user_id: int, amount: int = 1) -> bool:
    try:
        import json
        admin_ids = json.loads(os.getenv("ADMIN_ID", "[]"))
        if user_id in admin_ids:
            return True
    except Exception:
        pass
    plan = await get_user_plan(user_id)
    if plan in PAID_PLANS:
        return True
    result = await users_col.update_one(
        {"user_id": user_id, "credits": {"$gte": amount}},
        {"$inc": {"credits": -amount}}
    )
    return result.modified_count > 0


async def get_user_joined_date(user_id: int):
    user = await users_col.find_one({"user_id": user_id}, {"created_at": 1})
    if not user:
        return None
    return user.get("created_at")


# ============ 𝗝𝗢𝗜𝗡 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗖𝗔𝗖𝗛𝗘 ============

async def mark_user_joined(user_id: int):
    """𝗠𝗮𝗿𝗸 𝗮 𝘂𝘀𝗲𝗿 𝗮𝘀 𝗵𝗮𝘃𝗶𝗻𝗴 𝗷𝗼𝗶𝗻𝗲𝗱 𝗿𝗲𝗾𝘂𝗶𝗿𝗲𝗱 𝗰𝗵𝗮𝘁𝘀"""
    await joined_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "joined_at": datetime.datetime.utcnow()}},
        upsert=True
    )


async def is_user_marked_joined(user_id: int) -> bool:
    """𝗖𝗵𝗲𝗰𝗸 𝗶𝗳 𝘂𝘀𝗲𝗿 𝗶𝘀 𝗺𝗮𝗿𝗸𝗲𝗱 𝗮𝘀 𝗷𝗼𝗶𝗻𝗲𝗱"""
    doc = await joined_col.find_one({"user_id": user_id}, {"_id": 1})
    return doc is not None


async def remove_joined_mark(user_id: int):
    """𝗥𝗲𝗺𝗼𝘃𝗲 𝘁𝗵𝗲 𝗷𝗼𝗶𝗻𝗲𝗱 𝗺𝗮𝗿𝗸"""
    await joined_col.delete_one({"user_id": user_id})


# ============ 𝗞𝗘𝗬 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧 ============

KEY_PREFIX = "Razor-"
KEY_UNUSED_TTL_HOURS = 24
MAX_KEYS_PER_GENERATE = 50


def _generate_key_code(length: int = 20) -> str:
    import secrets
    import string as _string
    alphabet = _string.ascii_letters + _string.digits
    return KEY_PREFIX + "".join(secrets.choice(alphabet) for _ in range(length))


async def create_keys(amount: int, days: int, created_by: int, assigned_to: int | None = None):
    """Create unused redeem keys. Returns list of key strings."""
    amount = max(1, min(int(amount), MAX_KEYS_PER_GENERATE))
    days = max(1, int(days))
    now = datetime.datetime.utcnow()
    key_expires_at = now + datetime.timedelta(hours=KEY_UNUSED_TTL_HOURS)
    created = []
    for _ in range(amount):
        for _attempt in range(8):
            code = _generate_key_code()
            doc = {
                "key": code,
                "days": days,
                "status": "unused",
                "assigned_to": assigned_to,
                "created_by": created_by,
                "created_at": now,
                "key_expires_at": key_expires_at,
                "redeemed_by": None,
                "redeemed_at": None,
            }
            try:
                await keys_col.insert_one(doc)
                created.append(code)
                break
            except Exception:
                continue
    return created


async def get_key_doc(key: str):
    if not key:
        return None
    return await keys_col.find_one({"key": key.strip()})


async def expire_stale_unused_keys() -> int:
    """Mark unused keys past 24h as expired."""
    now = datetime.datetime.utcnow()
    result = await keys_col.update_many(
        {
            "status": "unused",
            "key_expires_at": {"$lt": now},
        },
        {"$set": {"status": "expired", "expired_at": now}},
    )
    return result.modified_count


async def get_remaining_keys(limit: int = 500):
    """Return unused keys that have not auto-expired yet."""
    await expire_stale_unused_keys()
    now = datetime.datetime.utcnow()
    cursor = keys_col.find(
        {
            "status": "unused",
            "key_expires_at": {"$gt": now},
        },
        {"key": 1, "days": 1, "assigned_to": 1, "created_at": 1, "key_expires_at": 1, "_id": 0},
    ).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def redeem_key(key: str, user_id: int) -> dict:
    """
    Attempt to redeem a key for user_id.
    Returns {"ok": bool, "error": str|None, "days": int|None, "key_doc": dict|None}
    error values: not_found | already_redeemed | expired | not_yours | already_premium
    """
    await expire_stale_unused_keys()
    code = (key or "").strip()
    if not code:
        return {"ok": False, "error": "not_found", "days": None, "key_doc": None}

    doc = await keys_col.find_one({"key": code})
    if not doc:
        return {"ok": False, "error": "not_found", "days": None, "key_doc": None}

    status = doc.get("status", "unused")
    if status == "redeemed":
        return {"ok": False, "error": "already_redeemed", "days": None, "key_doc": doc}
    if status == "expired":
        return {"ok": False, "error": "expired", "days": None, "key_doc": doc}

    now = datetime.datetime.utcnow()
    expires_at = doc.get("key_expires_at")
    if expires_at and expires_at < now:
        await keys_col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": "expired", "expired_at": now}},
        )
        return {"ok": False, "error": "expired", "days": None, "key_doc": doc}

    assigned_to = doc.get("assigned_to")
    if assigned_to is not None and int(assigned_to) != int(user_id):
        return {"ok": False, "error": "not_yours", "days": None, "key_doc": doc}

    if await is_premium_user(user_id):
        return {"ok": False, "error": "already_premium", "days": None, "key_doc": doc}

    days = int(doc.get("days") or 1)
    claimed = await keys_col.find_one_and_update(
        {"_id": doc["_id"], "status": "unused"},
        {
            "$set": {
                "status": "redeemed",
                "redeemed_by": user_id,
                "redeemed_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        fresh = await keys_col.find_one({"key": code})
        if fresh and fresh.get("status") == "redeemed":
            return {"ok": False, "error": "already_redeemed", "days": None, "key_doc": fresh}
        if fresh and fresh.get("status") == "expired":
            return {"ok": False, "error": "expired", "days": None, "key_doc": fresh}
        return {"ok": False, "error": "already_redeemed", "days": None, "key_doc": fresh}

    await set_user_plan(user_id, "Custom", days)
    return {"ok": True, "error": None, "days": days, "key_doc": claimed}


# ============ 𝗣𝗥𝗢𝗫𝗬 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧 ============

PROXY_GATES = ("shopify",)


def _norm_proxy_gate(gate: str) -> str:
    g = (gate or "shopify").strip().lower()
    return g if g in PROXY_GATES else "shopify"


async def migrate_proxy_gates():
    """Backfill gate field for proxies saved before the gate field existed."""
    old = await proxies_col.find({"gate": {"$exists": False}}).to_list(length=10000)
    for doc in old:
        await proxies_col.update_one({"_id": doc["_id"]}, {"$set": {"gate": "shopify"}})
    return len(old)


async def add_proxy_db(user_id: int, proxy_data: dict, gate: str = "shopify"):
    """Add proxy for user into a gate pool (shopify)."""
    gate = _norm_proxy_gate(gate)
    proxy_doc = {
        "user_id": user_id,
        "gate": gate,
        "ip": proxy_data.get("ip"),
        "port": proxy_data.get("port"),
        "username": proxy_data.get("username"),
        "password": proxy_data.get("password"),
        "proxy_url": proxy_data.get("proxy_url"),
        "proxy_type": proxy_data.get("type", "http"),
        "added_at": datetime.datetime.utcnow()
    }
    await proxies_col.insert_one(proxy_doc)


async def get_all_user_proxies(user_id: int, gate: str = "shopify"):
    """Get all proxies for user in one gate pool."""
    gate = _norm_proxy_gate(gate)
    cursor = proxies_col.find({"user_id": user_id, "gate": gate}).sort("added_at", 1)
    return await cursor.to_list(length=1000)


async def get_proxy_count(user_id: int, gate: str = "shopify") -> int:
    """Get user's proxy count for one gate pool."""
    gate = _norm_proxy_gate(gate)
    return await proxies_col.count_documents({"user_id": user_id, "gate": gate})


async def get_random_proxy(user_id: int, gate: str = "shopify"):
    """Get random proxy for user in one gate pool."""
    gate = _norm_proxy_gate(gate)
    pipeline = [
        {"$match": {"user_id": user_id, "gate": gate}},
        {"$sample": {"size": 1}}
    ]
    result = await proxies_col.aggregate(pipeline).to_list(length=1)
    return result[0] if result else None


async def remove_proxy_by_index(user_id: int, index: int, gate: str = "shopify"):
    """Remove proxy by index within a gate pool."""
    proxies = await get_all_user_proxies(user_id, gate=gate)
    if 0 <= index < len(proxies):
        proxy = proxies[index]
        await proxies_col.delete_one({"_id": proxy["_id"]})
        return proxy
    return None


async def remove_proxy_by_url(user_id: int, proxy_url: str, gate: str = "shopify"):
    """Remove proxy by URL within a gate pool."""
    gate = _norm_proxy_gate(gate)
    result = await proxies_col.delete_one({
        "user_id": user_id,
        "gate": gate,
        "proxy_url": proxy_url
    })
    return result.deleted_count > 0


async def clear_all_proxies(user_id: int, gate: str = "shopify") -> int:
    """Clear all proxies for user in one gate pool."""
    gate = _norm_proxy_gate(gate)
    result = await proxies_col.delete_many({"user_id": user_id, "gate": gate})
    return result.deleted_count


# ============ 𝗦𝗜𝗧𝗘 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧 ============

async def add_site_db(user_id: int, site: str) -> bool:
    """𝗔𝗱𝗱 𝘀𝗶𝘁𝗲 𝗳𝗼𝗿 𝘂𝘀𝗲𝗿"""
    try:
        await sites_col.update_one(
            {"user_id": user_id, "site": site},
            {"$setOnInsert": {
                "user_id": user_id,
                "site": site,
                "added_at": datetime.datetime.utcnow()
            }},
            upsert=True
        )
        return True
    except Exception:
        return False


async def get_user_sites(user_id: int):
    """𝗚𝗲𝘁 𝗮𝗹𝗹 𝘀𝗶𝘁𝗲𝘀 𝗳𝗼𝗿 𝘂𝘀𝗲𝗿"""
    cursor = sites_col.find({"user_id": user_id}, {"site": 1, "_id": 0})
    docs = await cursor.to_list(length=3000)
    return [doc["site"] for doc in docs]


async def remove_site_db(user_id: int, site: str) -> bool:
    """𝗥𝗲𝗺𝗼𝘃𝗲 𝘀𝗶𝘁𝗲 𝗳𝗼𝗿 𝘂𝘀𝗲𝗿"""
    result = await sites_col.delete_one({"user_id": user_id, "site": site})
    return result.deleted_count > 0


# ============ 𝗚𝗟𝗢𝗕𝗔𝗟 𝗦𝗜𝗧𝗘𝗦 ============

async def add_global_site(site: str) -> bool:
    """𝗔𝗱𝗱 𝗴𝗹𝗼𝗯𝗮𝗹 𝘀𝗶𝘁𝗲"""
    try:
        await global_sites_col.update_one(
            {"site": site},
            {"$setOnInsert": {
                "site": site,
                "added_at": datetime.datetime.utcnow()
            }},
            upsert=True
        )
        return True
    except:
        return False


async def get_global_sites():
    """𝗚𝗲𝘁 𝗮𝗹𝗹 𝗴𝗹𝗼𝗯𝗮𝗹 𝘀𝗶𝘁𝗲𝘀"""
    cursor = global_sites_col.find({}, {"site": 1, "_id": 0})
    docs = await cursor.to_list(length=10000)
    return [doc["site"] for doc in docs]


async def remove_global_site(site: str) -> bool:
    """𝗥𝗲𝗺𝗼𝘃𝗲 𝗴𝗹𝗼𝗯𝗮𝗹 𝘀𝗶𝘁𝗲"""
    result = await global_sites_col.delete_one({"site": site})
    return result.deleted_count > 0


async def count_global_sites() -> int:
    """𝗖𝗼𝘂𝗻𝘁 𝗴𝗹𝗼𝗯𝗮𝗹 (𝘀𝗵𝗮𝗿𝗲𝗱) 𝘀𝗶𝘁𝗲𝘀"""
    return await global_sites_col.count_documents({})


async def add_global_sites_bulk(sites) -> int:
    """𝗔𝗱𝗱 𝗺𝗮𝗻𝘆 𝗴𝗹𝗼𝗯𝗮𝗹 𝘀𝗶𝘁𝗲𝘀, 𝗶𝗴𝗻𝗼𝗿𝗶𝗻𝗴 𝗱𝘂𝗽𝗹𝗶𝗰𝗮𝘁𝗲𝘀. Returns number added."""
    added = 0
    for site in sites:
        if not site:
            continue
        try:
            result = await global_sites_col.update_one(
                {"site": site},
                {"$setOnInsert": {
                    "site": site,
                    "added_at": datetime.datetime.utcnow()
                }},
                upsert=True
            )
            if result.upserted_id is not None:
                added += 1
        except Exception:
            pass
    return added


async def clear_global_sites() -> int:
    """𝗖𝗹𝗲𝗮𝗿 𝘁𝗵𝗲 𝗲𝗻𝘁𝗶𝗿𝗲 𝗴𝗹𝗼𝗯𝗮𝗹 (𝘀𝗵𝗮𝗿𝗲𝗱) 𝘀𝗶𝘁𝗲 𝗽𝗼𝗼𝗹"""
    result = await global_sites_col.delete_many({})
    return result.deleted_count


async def seed_global_sites_from_user(user_id: int) -> int:
    """Seed the shared pool from a user's personal sites if the pool is empty.

    This is a one-time, non-destructive migration so that existing deployments
    (where free users used to read the admin's personal site list) keep working
    after the shared pool is decoupled from any single user's personal list.
    Returns the number of sites seeded (0 if the pool already had sites).
    """
    if await count_global_sites() > 0:
        return 0
    cursor = sites_col.find({"user_id": user_id}, {"site": 1, "_id": 0})
    docs = await cursor.to_list(length=50000)
    sites = [doc["site"] for doc in docs if doc.get("site")]
    if not sites:
        return 0
    return await add_global_sites_bulk(sites)



# ============ 𝗖𝗔𝗥𝗗 𝗛𝗜𝗦𝗧𝗢𝗥𝗬 ============

async def track_user_stats(user_id: int, status: str):
    """𝗧𝗿𝗮𝗰𝗸 𝘂𝘀𝗲𝗿 𝗴𝗮𝘁𝗲 𝘀𝘁𝗮𝘁𝘀 (𝗻𝗼 𝗰𝗮𝗿𝗱 𝘀𝘁𝗼𝗿𝗮𝗴𝗲)"""
    try:
        if user_id is None:
            return
        status_upper = status.upper()
        inc_doc = {"total_checked": 1}
        if status_upper == "CHARGED":
            inc_doc["total_charged"] = 1
            inc_doc["hits"] = 1
        elif status_upper == "APPROVED":
            inc_doc["total_approved"] = 1
        elif status_upper == "DECLINED":
            inc_doc["total_declined"] = 1

        await users_col.update_one(
            {"user_id": user_id},
            {"$inc": inc_doc},
            upsert=True
        )
    except Exception:
        pass



async def get_total_cards_count() -> int:
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_checked"}}}]
    result = await users_col.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def get_charged_count() -> int:
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_charged"}}}]
    result = await users_col.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def get_approved_count() -> int:
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_approved"}}}]
    result = await users_col.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def get_declined_count() -> int:
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_declined"}}}]
    result = await users_col.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


# ============ 𝗙𝗘𝗘𝗗𝗕𝗔𝗖𝗞 ============

async def save_feedback(user_id: int, user_name: str, message_id: int, chat_id: int, media_type: str):
    """𝗦𝗮𝘃𝗲 𝗳𝗲𝗲𝗱𝗯𝗮𝗰𝗸 𝘁𝗼 𝗗𝗕"""
    try:
        await feedback_col.insert_one({
            "user_id": user_id,
            "user_name": user_name,
            "message_id": message_id,
            "chat_id": chat_id,
            "media_type": media_type,
            "created_at": datetime.datetime.utcnow()
        })
    except Exception:
        pass


async def get_feedback_count() -> int:
    """𝗚𝗲𝘁 𝘁𝗼𝘁𝗮𝗹 𝗳𝗲𝗲𝗱𝗯𝗮𝗰𝗸 𝗰𝗼𝘂𝗻𝘁"""
    return await feedback_col.estimated_document_count()


# ============ 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦 ============

async def get_total_users() -> int:
    return await users_col.estimated_document_count()


async def get_all_user_ids():
    """Get all registered user IDs for broadcasts."""
    cursor = users_col.find({}, {"user_id": 1, "_id": 0})
    docs = await cursor.to_list(length=500000)
    return [doc["user_id"] for doc in docs if doc.get("user_id")]


async def get_premium_count() -> int:
    now = datetime.datetime.utcnow()
    return await users_col.count_documents({
        "plan": {"$in": PAID_PLANS},
        "expiry": {"$gt": now},
    })


async def get_all_premium_users():
    cursor = users_col.find(
        {"plan": {"$in": PAID_PLANS}},
        {"user_id": 1, "plan": 1, "expiry": 1, "_id": 0}
    )
    return await cursor.to_list(length=1000)


async def get_active_premium_users():
    """Return paid users whose plan expiry is still in the future."""
    now = datetime.datetime.utcnow()
    cursor = users_col.find(
        {
            "plan": {"$in": PAID_PLANS},
            "expiry": {"$gt": now},
        },
        {"user_id": 1, "plan": 1, "expiry": 1, "_id": 0}
    )
    return await cursor.to_list(length=1000)


async def expire_due_plans() -> int:
    """Downgrade all expired paid plans and queue expiry notifications."""
    now = datetime.datetime.utcnow()
    result = await users_col.update_many(
        {
            "plan": {"$in": PAID_PLANS},
            "expiry": {"$lt": now},
        },
        {
            "$set": {
                "plan": "Trial",
                "expiry": None,
                "pending_expiry_notify": True,
                "updated_at": now,
            }
        },
    )
    return result.modified_count


async def get_pending_expiry_notifications(limit: int = 200):
    cursor = users_col.find(
        {"pending_expiry_notify": True},
        {"user_id": 1, "_id": 0}
    ).limit(limit)
    return await cursor.to_list(length=limit)


async def clear_pending_expiry_notification(user_id: int):
    await users_col.update_one(
        {"user_id": user_id},
        {
            "$unset": {"pending_expiry_notify": ""},
            "$set": {"plan_expiry_notified": True},
        },
    )


async def get_total_sites_count() -> int:
    return await sites_col.estimated_document_count()


async def get_users_with_sites() -> int:
    pipeline = [{"$group": {"_id": "$user_id"}}]
    result = await sites_col.aggregate(pipeline).to_list(length=10000)
    return len(result)


async def get_sites_per_user():
    pipeline = [
        {"$group": {"_id": "$user_id", "cnt": {"$sum": 1}}},
        {"$project": {"user_id": "$_id", "cnt": 1, "_id": 0}}
    ]
    return await sites_col.aggregate(pipeline).to_list(length=1000)


async def get_all_sites_detail():
    cursor = sites_col.find().sort("user_id", 1)
    return await cursor.to_list(length=10000)


# ============ HITS TRACKING ============
async def get_top_hits(limit: int = 10):
    """Get top users by hits from database"""
    try:
        cursor = users_col.find({"hits": {"$gt": 0}}, {"user_id": 1, "hits": 1, "name": 1, "username": 1}).sort("hits", -1).limit(limit)
        return await cursor.to_list(length=limit)
    except Exception as e:
        print(f"Error getting top hits: {e}")
    return []


async def get_total_hits() -> int:
    """Get total hits across all users"""
    try:
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$hits"}}}]
        result = await users_col.aggregate(pipeline).to_list(length=1)
        if result:
            return result[0].get("total", 0)
    except Exception as e:
        print(f"Error getting total hits: {e}")
    return 0


# ============ SHOPIFY SESSION PERSISTENCE ============
async def save_sh_session(session: dict):
    """Save shopify check session to database (exclude non-serializable objects like msg)"""
    try:
        doc = {
            "session_id": session.get("session_id"),
            "user_id": session.get("user_id"),
            "total": session.get("total"),
            "results": session.get("results") or [],
            "start": session.get("start"),
            "name": session.get("name"),
            "view_page": session.get("view_page", 0),
            "done": session.get("done", False),
            "stopped": session.get("stopped", False),
            "updated_at": datetime.datetime.utcnow()
        }
        await db["sh_sessions"].update_one(
            {"session_id": doc["session_id"]},
            {"$set": doc},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving sh session: {e}")


async def get_sh_session(session_id: str):
    """Load shopify check session from database"""
    try:
        return await db["sh_sessions"].find_one({"session_id": session_id})
    except Exception as e:
        print(f"Error loading sh session: {e}")
    return None


# ============ USER STATS ============
async def get_user_stats(user_id: int):
    """Get stats (checked, charged, approved, declined) for a user"""
    try:
        user = await users_col.find_one({"user_id": user_id})
        if user:
            return (
                user.get("total_checked", 0),
                user.get("total_charged", 0),
                user.get("total_approved", 0),
                user.get("total_declined", 0)
            )
    except Exception:
        pass
    return 0, 0, 0, 0
