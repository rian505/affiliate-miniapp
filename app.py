#!/usr/bin/env python3
"""Telegram Mini App backend — Affiliate + AI Prompt Generator."""
import os
import hmac
import hashlib
import json
import time
import httpx
from datetime import datetime
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ---- Config ----
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USERS = {
    u.strip() for u in os.environ.get("TELEGRAM_ALLOWED_USERS", "").split(",") if u.strip()
}
SHEET_ID = os.environ.get("AFFILIATE_SHEET_ID", "18hYBq3q4osQ2h3FgFB2LysCQDA6gsYGAnMKgzWGT4L0")
SHEET_TAB = "Produk Affiliate"
TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", os.path.expanduser("~/.hermes/google_token.json"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHEETS_ENABLED = bool(os.environ.get("GOOGLE_TOKEN_PATH") or os.path.exists(os.path.expanduser("~/.hermes/google_token.json")))

app = FastAPI(title="MINJI Tools")


# =====================================================================
# PRODUCTS DATABASE
# =====================================================================
PRODUCTS = [
    {
        "id": 1, "name": "Sandal Lanoes Coklat", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Lanoes flat slide sandals",
            "DESKRIPSI_PRODUK": "dark chocolate brown glossy patent leather flat slide mule sandals with wide squared toe, one thick wide cross strap, gold rectangular buckle hardware on side of strap, white contrast stitching along ALL edges, dark brown glossy leather insole with cursive 'Lanoes' script embossed, thin flat rubber sole",
            "CARA_PEGANG": "One hand grips one sandal from below supporting sole, other hand holds second sandal cradling the sides — both sandals side by side facing camera, gold buckle visible",
            "DETAIL_UTAMA": "gold buckle hardware, white contrast stitching, glossy patent leather texture, and the embossed Lanoes cursive script on insole",
        }
    },
    {
        "id": 2, "name": "Heels Apry Collection Pink", "category": "Heels", "is_heels": True, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Apry Collection block heel mule",
            "DESKRIPSI_PRODUK": "dusty blush pink / dusty rose pink block heel mule sandals with woven/knit textured fabric toe strap, smooth pink leather ribbon bow with two large rounded loops and tight center knot (no dangling ends), smooth pink leather binding along all strap edges, square open toe, chunky low block heel matching dusty pink, cream beige leather insole with 'Apry Collection' embossed",
            "CARA_PEGANG": "One hand holding block heel from behind, other hand supporting toe area from below — both sandals side by side, bow detail clearly visible",
            "DETAIL_UTAMA": "the woven texture of the toe strap, the loopy ribbon bow with its tight center knot, and the smooth pink leather binding along edges",
        }
    },
    {
        "id": 3, "name": "Sandal Coklat Lanoes (Big Buckle)", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Lanoes flat slide sandals (versi buckle besar)",
            "DESKRIPSI_PRODUK": "deep dark chocolate brown glossy leather flat slide mule sandals with wide squared rounded toe, one wide cross strap plus thinner parallel strap, gold rectangular buckle on cross strap, white contrast stitching all edges, dark brown insole with cursive Lanoes script",
            "CARA_PEGANG": "Both hands from below, one sandal each, palms up",
            "DETAIL_UTAMA": "the large gold rectangular buckle, parallel strap design, glossy leather finish, and white contrast stitching",
        }
    },
    {
        "id": 4, "name": "Tas Hitam Structured", "category": "Tas", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Black structured tote shoulder bag",
            "DESKRIPSI_PRODUK": "matte black pebbled/textured leather structured rectangular tote shoulder bag, wider at top, two long flat shoulder straps, gold buckle hardware on each strap side, white contrast stitching all panel seams and edges, decorative curved stitching at bottom corners, vertical center seam on front panel",
            "CARA_PEGANG": "One hand grips top strap naturally, other hand supports bottom of bag from below",
            "DETAIL_UTAMA": "the pebbled leather texture, gold buckle hardware on straps, white contrast stitching along panel seams, and the curved decorative stitching at bottom corners",
        }
    },
    {
        "id": 5, "name": "Tas Cream Crescent (Apry)", "category": "Tas", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Cream crescent hobo shoulder bag",
            "DESKRIPSI_PRODUK": "cream / ivory off-white smooth leather crescent half-moon shaped hobo shoulder bag, single top handle strap, gold chain charm with ball pendants on left side, gold buckle on right side of strap, center seam stitching on leather body, zip closure at top",
            "CARA_PEGANG": "One hand grips top handle strap, other hand supports bottom of bag from below",
            "DETAIL_UTAMA": "the crescent half-moon shape, gold chain charm with ball pendants, center seam stitching, and smooth cream leather finish",
        }
    },
    {
        "id": 6, "name": "Tas Hitam Woven Hobo (Ankalis)", "category": "Tas", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Black woven intrecciato hobo shoulder bag",
            "DESKRIPSI_PRODUK": "matte black interlaced woven leather intrecciato hobo shoulder bag, trapezoid crescent shape wider at bottom, single braided/twisted shoulder strap, no hardware, intrecciato woven pattern entire body, vertical center seam on front panel",
            "CARA_PEGANG": "One hand grips top braided shoulder strap naturally, other hand supports bottom of bag from below",
            "DETAIL_UTAMA": "the intrecciato woven leather pattern, braided twisted shoulder strap, and vertical center seam",
        }
    },
    {
        "id": 7, "name": "Sandal Lanoes Black Rhinestone", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Lanoes flat slide sandals (rhinestone version)",
            "DESKRIPSI_PRODUK": "matte black footbed flat slide mule sandals with open square toe, multiple thin cross straps fully encrusted with silver rhinestone and crystal, black insole with gold italic 'LANOES' text, flat black rubber sole, no price sticker",
            "CARA_PEGANG": "One hand holds one sandal from below supporting sole, other hand holds second sandal cradling sides — both sandals side by side, rhinestone straps visible from front",
            "DETAIL_UTAMA": "the silver rhinestone and crystal encrusted cross straps, the sparkle and reflection of stones, and gold LANOES text on black insole",
        }
    },
    {
        "id": 8, "name": "Tas Coklat + Smiley Charm (Q'la)", "category": "Tas", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Brown shoulder tote bag with smiley charm",
            "DESKRIPSI_PRODUK": "medium warm brown / cognac smooth leather with slight distressed finish structured rectangular tote shoulder bag, wider at top, two long flat matching brown shoulder straps, gold rectangular name plate on front panel center, white fluffy plush smiley face charm with dangling rope legs and white ball ends attached via gold ring on left side of strap, visible edge stitching along all panels, small side zipper pull",
            "CARA_PEGANG": "One hand grips top shoulder straps naturally, other hand supports bottom of bag from below",
            "DETAIL_UTAMA": "the gold rectangular name plate, the white fluffy smiley face charm with rope legs, and the warm cognac leather with slight distressed finish",
        }
    },
    {
        "id": 9, "name": "Sandal Epitychia Cream H-Cutout", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Epitychia flat mule slides",
            "DESKRIPSI_PRODUK": "cream/warm beige smooth leather flat mule slides with closed toe cap featuring H-cutout slots (Hermès-style), horizontal cross strap across vamp with small tab loop, rose gold circular buckle on side of strap, dark chocolate brown leather insole with 'epitychia' lowercase script embossed, flat dark brown rubber sole",
            "CARA_PEGANG": "One hand holds one sandal from below supporting sole, other hand holds second sandal cradling sides — both sandals side by side, rose gold buckle clearly visible",
            "DETAIL_UTAMA": "the H-cutout slots on the toe cap, rose gold circular buckle, and the embossed epitychia script on chocolate brown insole",
        }
    },
    {
        "id": 10, "name": "Tas Cream Patent Mini Handbag", "category": "Tas", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Cream patent mini rectangular handbag / crossbody",
            "DESKRIPSI_PRODUK": "cream/ivory glossy patent leather mini rectangular boxy handbag, short flat top handle with gold stud attachment, long detachable flat crossbody strap with gold buckle adjuster, gold twist-lock turnlock clasp at center flap, full front flap with piping trim, all hardware gold, mini/small size",
            "CARA_PEGANG": "One hand grips short top handle, other hand supports bottom of bag from below",
            "DETAIL_UTAMA": "the glossy patent leather finish, gold twist-lock turnlock clasp, piping trim on flap, and the gold buckle adjuster on crossbody strap",
        }
    },
    {
        "id": 11, "name": "Tas White & Brown Mini Dome Bowling (Q'la)", "category": "Tas", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "White & dark brown mini dome bowling bag",
            "DESKRIPSI_PRODUK": "white/cream body with dark chocolate brown trim and handles mini dome half-moon bowling bag, two short rolled dark brown top handles, detachable flat dark brown crossbody strap with gold hardware, gold ring connectors, studs, name plate, zipper pull, dark brown 4-petal flower charm with gold center stud hanging via gold ring from left handle, dark brown leather tab/patch pointed shape at handle base, gold rectangular blank name plate at bottom center front, zip top closure",
            "CARA_PEGANG": "One hand grips both short top handles together, other hand supports bottom of bag from below",
            "DETAIL_UTAMA": "the dark brown 4-petal flower charm, gold name plate, white and brown color contrast, and dome bowling shape",
        }
    },
    {
        "id": 12, "name": "Sandal Alidita Denim Bow", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Alidita flat slide sandals denim bow",
            "DESKRIPSI_PRODUK": "navy blue denim upper flat slide sandals with glossy black sole and trim, wide denim fabric cross strap, black glossy ribbon bow tied at center strap, open square toe, black insole with gold italic 'Alidita' script, glossy black flat sole with white contrast stitching",
            "CARA_PEGANG": "One hand holds one sandal from below supporting sole, other hand holds second sandal cradling sides — both sandals side by side, denim strap and bow visible",
            "DETAIL_UTAMA": "the navy blue denim fabric strap, black glossy ribbon bow at center, and gold Alidita script on black insole",
        }
    },
    {
        "id": 13, "name": "Sandal Ra Store Tweed Buckle", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Ra Store tweed flat slide sandals",
            "DESKRIPSI_PRODUK": "multicolor tweed upper (cream/beige/pink/gold) flat slide sandals with dark burgundy trim, wide tweed/bouclé fabric toe cap with horizontal dark burgundy cross strap, small silver gunmetal buckle at center cross strap, dark burgundy leather insole with gold italic 'Ra Store' script, flat dark burgundy rubber sole, no price sticker",
            "CARA_PEGANG": "One hand holds one sandal from below supporting sole, other hand holds second sandal cradling sides — both sandals side by side, tweed upper and buckle visible",
            "DETAIL_UTAMA": "the multicolor tweed bouclé fabric, dark burgundy leather trim, silver gunmetal buckle, and gold Ra Store script on insole",
        }
    },
    {
        "id": 14, "name": "Sandal Zhiika Black Tweed Double Strap", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Zhiika flat slide sandals double tweed strap",
            "DESKRIPSI_PRODUK": "black and white tweed upper flat slide sandals with black leather trim and sole, two parallel horizontal straps both in black/white tweed bouclé, black smooth leather piping and binding on all strap sides, open square toe, black insole with 'ZHIIKA' embossed, flat black rubber sole",
            "CARA_PEGANG": "One hand holds one sandal from below supporting sole, other hand holds second sandal cradling sides — both sandals side by side, double tweed straps visible",
            "DETAIL_UTAMA": "the two parallel black and white tweed straps, black leather piping along edges, and ZHIIKA embossed on black insole",
        }
    },
    {
        "id": 15, "name": "Sandal Chelltec Cream & Black Woven", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Chelltec flat slide sandals woven",
            "DESKRIPSI_PRODUK": "cream/off-white leather and black woven overlay flat slide sandals with wide single strap featuring geometric basket-weave grid pattern — cream leather strips crossed with black leather strips, open square toe, cream/ivory insole with gold 'CHELLTEC' text embossed, thin flat dark rubber sole",
            "CARA_PEGANG": "One hand holds one sandal from below supporting sole, other hand holds second sandal cradling sides — both sandals side by side, woven pattern visible from front",
            "DETAIL_UTAMA": "the geometric basket-weave grid pattern with cream and black leather strips, and gold CHELLTEC text on cream insole",
        }
    },
    {
        "id": 16, "name": "Heels Fradhea Tan Patent Cross Strap", "category": "Heels", "is_heels": True, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Fradhea pointed toe low block heel mules",
            "DESKRIPSI_PRODUK": "warm tan/camel glossy patent leather pointed toe low block heel mules with two cross straps — one wide at toe and one thin above, small gold rhinestone/crystal square buckle at strap intersection, low chunky block heel matching tan with black rubber heel tip, tan patent leather insole with 'FRADHEA' embossed, thin black rubber outsole, white contrast stitching along all strap edges",
            "CARA_PEGANG": "One hand holds one shoe from behind gripping block heel, other hand holds second shoe supporting toe area from below — both shoes side by side, cross straps and gold crystal facing camera",
            "DETAIL_UTAMA": "the gold rhinestone crystal buckle at strap intersection, glossy tan patent leather finish, and white contrast stitching",
        }
    },
    {
        "id": 17, "name": "Heels MHstore Burgundy Knot Strap", "category": "Heels", "is_heels": True, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "MHstore open toe low block heel mules burgundy",
            "DESKRIPSI_PRODUK": "deep burgundy/wine red high-gloss patent leather open toe low block heel mules with multiple thin spaghetti straps gathering into knot at center toe with small toe post thong, open square toe, low chunky block heel matching burgundy patent with black rubber tip, burgundy patent insole with gold italic 'MHstore' script, black rubber outsole",
            "CARA_PEGANG": "One hand holds one shoe from behind gripping block heel, other hand holds second shoe supporting toe area from below — both shoes side by side, knot strap detail facing camera",
            "DETAIL_UTAMA": "the spaghetti straps gathered into center knot, deep burgundy high-gloss patent finish, and gold MHstore script on insole",
        }
    },
    {
        "id": 18, "name": "Sandal Cream Puffy Bow Flat", "category": "Sandal", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Flat slide mules cream puffy bow",
            "DESKRIPSI_PRODUK": "cream/off-white puffy padded voluminous upper flat slide mules with dark chocolate brown insole and bow, wide puffy/padded cream leather strap, dark brown thin leather ribbon bow tied at center strap with white contrast stitching on bow, open square toe, dark chocolate brown leather insole with brand name embossed, thick cream/white EVA flatform sole with slight platform",
            "CARA_PEGANG": "One hand holds one sandal from below supporting sole, other hand holds second sandal cradling sides — both sandals side by side, puffy bow visible from front",
            "DETAIL_UTAMA": "the puffy padded voluminous cream strap, dark brown leather ribbon bow with white stitching, and the flatform EVA sole",
        }
    },
    {
        "id": 19, "name": "Heels Killa77 Black Strappy Knot", "category": "Heels", "is_heels": True, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Killa77 open toe low block heel mules black",
            "DESKRIPSI_PRODUK": "glossy black patent leather open toe low block heel mules with nude/blush pink insole, multiple very thin delicate spaghetti straps with knot at center and thin toe post thong, open square toe, low chunky block heel matching black patent with black rubber tip, nude/blush pink leather insole with gold 'KILLA77' text, black rubber outsole",
            "CARA_PEGANG": "One hand holds one shoe from behind gripping block heel, other hand holds second shoe supporting toe area from below — both shoes side by side, strappy knot detail facing camera",
            "DETAIL_UTAMA": "the delicate thin spaghetti straps, center knot detail, glossy black patent finish, and gold KILLA77 text on nude pink insole",
        }
    },
    {
        "id": 20, "name": "Sepatu Debinca Dark Brown Suede Mary Jane", "category": "Sepatu", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Dark brown suede Mary Jane ballet flats",
            "DESKRIPSI_PRODUK": "dark chocolate brown suede/velvet upper ballet flat Mary Jane shoes with rounded square toe, tan/camel smooth leather single thin Mary Jane strap with small gold bar/clip buckle, dark brown insole with quilted diamond stitch pattern and brand embossed, tan/camel leather piping along all edges, flat dark brown rubber sole",
            "CARA_PEGANG": "One hand holds one shoe from behind supporting heel, other hand holds second shoe supporting toe area from below — both shoes side by side, Mary Jane strap and suede upper facing camera",
            "DETAIL_UTAMA": "the dark brown suede texture, tan leather Mary Jane strap with gold buckle, quilted diamond stitch insole, and tan leather piping edges",
        }
    },
    {
        "id": 21, "name": "Sepatu Fradhea Dusty Pink Satin Mary Jane", "category": "Sepatu", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Fradhea ballet flat Mary Jane shoes dusty pink",
            "DESKRIPSI_PRODUK": "dusty pink/mauve/greige satin-finish leather ballet flat Mary Jane shoes with rounded toe, smooth satin-finish leather upper, single Mary Jane strap matching color with small silver/chrome rectangular buckle, small matching satin bow at center toe with tiny gold pin charm detail at each bow end, beige/tan leather insole with 'FRADHEA' embossed, thin flat dark rubber sole",
            "CARA_PEGANG": "One hand holds one shoe from behind supporting heel, other hand holds second shoe supporting toe area from below — both shoes side by side, bow and strap facing camera",
            "DETAIL_UTAMA": "the satin-finish dusty pink leather, small matching bow with gold pin charm, silver rectangular buckle, and FRADHEA embossed on beige insole",
        }
    },
    {
        "id": 22, "name": "Heels Karlun Dark Chocolate Metallic Strappy", "category": "Heels", "is_heels": True, "sweater": "White",
        "vars": {
            "NAMA_PRODUK": "Karlun strappy mules dark chocolate metallic",
            "DESKRIPSI_PRODUK": "dark chocolate brown metallic/mirror finish strappy mules with multiple thin delicate spaghetti cross straps and toe post thong, short wide block heel ~3cm (SANGAT PENDEK — stubby, as tall as stack of 3 coins) same dark chocolate metallic, slight layered platform rubber outsole, dark chocolate metallic insole with 'karlun' lowercase embossed",
            "CARA_PEGANG": "One hand holds one shoe from below supporting sole, other hand holds second shoe cradling sides — both shoes side by side, cross straps visible from front",
            "DETAIL_UTAMA": "the metallic mirror finish, delicate spaghetti cross straps, and the very short stubby block heel (as tall as stack of 3 coins)",
        }
    },
    {
        "id": 23, "name": "Tas Baby Blue Mini Bowling (Wildan Store)", "category": "Tas", "is_heels": False, "sweater": "Blue",
        "vars": {
            "NAMA_PRODUK": "Baby blue mini bowling/dome barrel bag",
            "DESKRIPSI_PRODUK": "baby blue/ice blue soft smooth leather mini bowling dome barrel bag, two short rolled top handles matching baby blue, detachable flat crossbody strap with gold hardware on sides, gold zipper at top, all gold hardware including zipper pull, ring connectors, and feet studs underneath, baby blue heart-shaped leather charm with silver deer/stag emblem hanging via gold ring from left zipper pull, decorative teardrop/horseshoe stitched patch on right front, visible edge stitching all panels, mini size",
            "CARA_PEGANG": "One hand grips both short top handles together, other hand supports bottom of bag from below",
            "DETAIL_UTAMA": "the baby blue heart charm with silver deer emblem, gold hardware, teardrop decorative patch, and the dome bowling barrel shape",
        }
    },
]


# =====================================================================
# PROMPT TEMPLATES
# =====================================================================

def gen_photo_prompt(v, sweater):
    return f"""Image 1 = product reference, Image 2 = background reference

I am providing TWO reference images. Image 2 is the BACKGROUND — keep it 100% identical, do not change anything about it. Image 1 is the product to place into the scene. Do not replace, recreate, or modify the background floor, lighting, shadows, wall, or color tone in any way whatsoever. Only add the hands and {v['NAMA_PRODUK']} naturally into the existing background scene.

Into this EXACT background, add: two real human hands with fair warm-toned Southeast Asian skin, short nude pink nails, wearing {sweater} ribbed knit sweater sleeves — {v['CARA_PEGANG']} — {v['DESKRIPSI_PRODUK']}. Do not alter the shape, size, texture, or any detail of the product in any way. Lighting, shadow, and skin tone of hands must blend seamlessly with the existing warm golden background light. Looks like a real photo taken in that exact room, not AI-generated. TikTok affiliate style. 9:16 vertical. No text, no watermark."""


def gen_video_scene1(v, sweater):
    return f"""Image 1 = product reference, Image 2 = background reference

Animate or generate this as a natural 8-second video. Image 2 is the BACKGROUND — keep it 100% identical. Image 1 is the product.

A young woman's both hands with fair warm-toned Southeast Asian skin, short nude pink nails, wearing {sweater} ribbed knit sweater sleeves — slowly lifting {v['DESKRIPSI_PRODUK']} into frame from below naturally. {v['CARA_PEGANG']}. Movement is slow, gentle, slightly swaying — like casually revealing a new purchase to camera. Background EXACTLY as Image 2 — do not change floor, lighting, shadows, wall in any way. Lighting and shadows blend naturally with warm golden room light. Slightly handheld feel, soft natural bokeh, warm golden daylight. Casual TikTok affiliate haul mood. Not HD, not studio-lit. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


def gen_video_scene2(v, sweater):
    return f"""Continuing from previous shot — same {v['NAMA_PRODUK']}, same fair warm-toned hands, nude pink nails, same {sweater} ribbed knit sweater sleeves, same warm oak wood floor with golden sunlight patches — do not change background. Camera slowly drifts close-up across {v['DETAIL_UTAMA']}. Movement dreamy and slow. One hand holds steady, other hand rotates slightly for detail view. Soft bokeh, warm golden daylight, slight film grain. Not HD. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


def gen_animate_prompt(v, sweater):
    return f"""Image 1 = reference image to animate

Animate this exact image into a natural 8-second video. Keep all elements identical — do not change the hands, product, sweater, or background in any way. Add only subtle natural movement: hands gently shift weight slightly as if breathing, product sways very slightly, warm golden sunlight patches shimmer softly. Camera has a very slight handheld drift — slow, gentle, barely noticeable. Casual TikTok affiliate fashion haul video — warm and candid. Not HD, not studio-lit. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


def gen_heels_scene1(v, sweater):
    return f"""Image 1 = reference image to animate

Animate this exact image into a natural 8-second video. Keep ALL elements 100% identical — hands, shoes, sweater, background, heel. The block heel in this image is SHORT AND WIDE — maintain this exact proportion every single frame, do not change.

Add only: hands sway gently side to side, shoes move naturally with hands. Warm golden sunlight shimmer on floor. Slight handheld drift. Casual TikTok haul mood. Not HD. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


def gen_heels_scene2(v, sweater):
    return f"""Continuing from previous shot — SAME distance, SAME angle, SAME frame. Do NOT zoom, do NOT move camera.

Only movement: hands tilt shoes very slightly left then right — small gentle wiggle only. Heel stays SHORT AND WIDE identical to Scene 1 — do not elongate. Background static. Sunlight shimmer continues. Not HD. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


PROMPT_TYPES = {
    "photo": {"label": "📸 Foto", "desc": "Prompt foto untuk Gemini", "fn": gen_photo_prompt, "heels_only": False},
    "video_reveal": {"label": "🎬 Video Scene 1 — Reveal", "desc": "Scene 1: angkat produk ke frame", "fn": gen_video_scene1, "heels_only": False},
    "video_detail": {"label": "🎬 Video Scene 2 — Detail", "desc": "Scene 2: close-up detail (extend clip)", "fn": gen_video_scene2, "heels_only": False},
    "animate": {"label": "✨ Animate dari Foto", "desc": "Animasi dari foto yang sudah ada", "fn": gen_animate_prompt, "heels_only": False},
    "heels_scene1": {"label": "👠 Heels Scene 1 — Reveal", "desc": "Khusus heels: reveal (heel tetap pendek)", "fn": gen_heels_scene1, "heels_only": True},
    "heels_scene2": {"label": "👠 Heels Scene 2 — Detail", "desc": "Khusus heels: detail (zero zoom, wiggle only)", "fn": gen_heels_scene2, "heels_only": True},
}


# =====================================================================
# TELEGRAM AUTH
# =====================================================================
def validate_init_data(init_data: str, max_age: int = 86400) -> dict:
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except Exception:
        raise HTTPException(400, "Bad initData")

    recv_hash = parsed.pop("hash", None)
    if not recv_hash:
        raise HTTPException(401, "No hash")

    data_check = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, recv_hash):
        raise HTTPException(401, "Invalid signature")

    auth_date = int(parsed.get("auth_date", 0))
    if max_age and (time.time() - auth_date) > max_age:
        raise HTTPException(401, "initData expired")

    user = json.loads(parsed.get("user", "{}"))
    if ALLOWED_USERS and str(user.get("id")) not in ALLOWED_USERS:
        raise HTTPException(403, "Not authorized")
    return user


# =====================================================================
# GOOGLE SHEETS
# =====================================================================
def get_sheets_service():
    if not SHEETS_ENABLED:
        return None
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    return build("sheets", "v4", credentials=creds)


def append_rows(rows: list):
    svc = get_sheets_service()
    if not svc:
        raise HTTPException(503, "Google Sheets not configured on this server")
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{SHEET_TAB}!A:H",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


def build_row(produk, merk, warna, kategori, link):
    tanggal = datetime.now().strftime("%d/%m/%Y")
    return [
        tanggal, produk.strip(), merk.strip(), warna.strip(),
        kategori.strip(), "Belum", "", link.strip(),
    ]


# =====================================================================
# MODELS
# =====================================================================
class Entry(BaseModel):
    initData: str
    link_tokopedia: str
    produk: str
    warna: str = ""
    merk: str = ""
    kategori: str = ""


class BulkItem(BaseModel):
    link_tokopedia: str
    produk: str
    warna: str = ""
    merk: str = ""
    kategori: str = ""


class BulkEntry(BaseModel):
    initData: str
    items: list[BulkItem]


class AuthOnly(BaseModel):
    initData: str


class PromptRequest(BaseModel):
    product_id: int
    prompt_type: str
    sweater: str = ""


# =====================================================================
# ROUTES: Pages
# =====================================================================
@app.get("/", response_class=HTMLResponse)
def index():
    try:
        with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>MINJI Tools</h1><p>index.html not found. Check deployment.</p>", status_code=500)


# =====================================================================
# ROUTES: Affiliate
# =====================================================================
@app.post("/submit")
async def submit(entry: Entry):
    user = validate_init_data(entry.initData) if BOT_TOKEN else {"first_name": "user"}
    if not entry.link_tokopedia.strip() or not entry.produk.strip():
        raise HTTPException(422, "Link Tokopedia & Produk wajib diisi")

    row = build_row(entry.produk, entry.merk, entry.warna, entry.kategori, entry.link_tokopedia)
    try:
        append_rows([row])
    except Exception as e:
        raise HTTPException(500, f"Gagal nulis ke sheet: {e}")
    return JSONResponse({"ok": True, "produk": entry.produk, "by": user.get("first_name", "")})


@app.post("/submit-bulk")
async def submit_bulk(entry: BulkEntry):
    user = validate_init_data(entry.initData) if BOT_TOKEN else {"first_name": "user"}
    rows = []
    skipped = 0
    for it in entry.items:
        if not it.link_tokopedia.strip() or not it.produk.strip():
            skipped += 1
            continue
        rows.append(build_row(it.produk, it.merk, it.warna, it.kategori, it.link_tokopedia))
    if not rows:
        raise HTTPException(422, "Ga ada baris valid")
    try:
        append_rows(rows)
    except Exception as e:
        raise HTTPException(500, f"Gagal nulis ke sheet: {e}")
    return JSONResponse({"ok": True, "added": len(rows), "skipped": skipped, "by": user.get("first_name", "")})


@app.post("/stats")
async def stats(entry: AuthOnly):
    if BOT_TOKEN:
        validate_init_data(entry.initData)

    if not SHEETS_ENABLED:
        return JSONResponse({
            "ok": True, "total": 0, "sudah": 0, "belum": 0,
            "kategori": [], "recent": [],
            "note": "Google Sheets not configured — showing demo data"
        })

    try:
        svc = get_sheets_service()
        r = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"{SHEET_TAB}!A:H"
        ).execute()
        vals = r.get("values", [])
    except Exception as e:
        raise HTTPException(500, f"Gagal baca sheet: {e}")

    data = vals[1:] if len(vals) > 1 else []
    total = len(data)
    sudah = belum = 0
    kategori = {}
    for row in data:
        status = (row[5] if len(row) > 5 else "").strip().lower()
        if "sudah" in status or "✅" in status:
            sudah += 1
        else:
            belum += 1
        kat = (row[4] if len(row) > 4 else "").strip() or "Lainnya"
        kategori[kat] = kategori.get(kat, 0) + 1

    top_kat = sorted(kategori.items(), key=lambda x: -x[1])[:6]
    recent = []
    for row in reversed(data[-5:]):
        recent.append({
            "tanggal": row[0] if len(row) > 0 else "",
            "produk": row[1] if len(row) > 1 else "",
            "kategori": row[4] if len(row) > 4 else "",
            "status": row[5] if len(row) > 5 else "",
        })
    return JSONResponse({
        "ok": True, "total": total, "sudah": sudah, "belum": belum,
        "kategori": top_kat, "recent": recent,
    })


# =====================================================================
# ROUTES: Prompt Generator
# =====================================================================
@app.get("/products")
def get_products():
    """Return product list (no auth needed — it's a static catalog)."""
    items = []
    for p in PRODUCTS:
        items.append({
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "is_heels": p["is_heels"],
            "sweater": p["sweater"],
        })
    return {"products": items}


@app.get("/prompt-types")
def get_prompt_types():
    """Return available prompt types."""
    types = []
    for key, val in PROMPT_TYPES.items():
        types.append({"key": key, "label": val["label"], "desc": val["desc"], "heels_only": val["heels_only"]})
    return {"types": types}


@app.post("/generate-prompt")
def generate_prompt(req: PromptRequest):
    """Generate a filled prompt for a product + type."""
    product = next((p for p in PRODUCTS if p["id"] == req.product_id), None)
    if not product:
        raise HTTPException(404, "Produk tidak ditemukan")

    prompt_type = PROMPT_TYPES.get(req.prompt_type)
    if not prompt_type:
        raise HTTPException(400, f"Tipe prompt '{req.prompt_type}' tidak valid")

    if prompt_type["heels_only"] and not product["is_heels"]:
        raise HTTPException(400, "Tipe prompt heels hanya untuk produk heels")

    sweater = req.sweater.strip() or product["sweater"]
    prompt_text = prompt_type["fn"](product["vars"], sweater)

    return {
        "ok": True,
        "product": product["name"],
        "prompt_type": req.prompt_type,
        "prompt_label": prompt_type["label"],
        "sweater": sweater,
        "prompt": prompt_text,
    }


@app.get("/health")
def health():
    return {"ok": True, "app": "MINJI Tools"}
