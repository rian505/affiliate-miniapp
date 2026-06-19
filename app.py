#!/usr/bin/env python3
"""MINJI Tools — Affiliate Bulk Sheets + Prompt Generator."""
import os
import json
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

# ---- Config ----
SHEET_ID = os.environ.get("AFFILIATE_SHEET_ID", "18hYBq3q4osQ2h3FgFB2LysCQDA6gsYGAnMKgzWGT4L0")
SHEET_TAB = "Produk Affiliate"
TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", os.path.expanduser("~/.hermes/google_token.json"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHEETS_ENABLED = os.path.exists(os.path.expanduser("~/.hermes/google_token.json"))

app = FastAPI(title="MINJI Tools")


# =====================================================================
# GOOGLE SHEETS
# =====================================================================
def get_sheets_service():
    if not SHEETS_ENABLED:
        return None
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    return build("sheets", "v4", credentials=creds)


def append_rows(rows: list):
    svc = get_sheets_service()
    if not svc:
        raise HTTPException(503, "Google Sheets not configured")
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{SHEET_TAB}!A:H",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# =====================================================================
# PROMPT GENERATION — clean English master prompts (no placeholders)
# AI model (Gemini / Google Flow) reads the image and fills in product details.
# =====================================================================
PHOTO_PROMPT = """Image 1 = product reference, Image 2 = background reference

I am providing TWO reference images. Image 2 is the BACKGROUND — keep it 100% identical, do not change anything about it. Image 1 is the product to place into the scene. Do not replace, recreate, or modify the background floor, lighting, shadows, wall, or color tone in any way whatsoever. Only add the hands and the product naturally into the existing background scene.

Into this EXACT background, add: two real human hands with fair warm-toned Southeast Asian skin, short nude pink nails, wearing blue ribbed knit sweater sleeves — naturally holding the product. Do not alter the shape, size, texture, or any detail of the product in any way. Lighting, shadow, and skin tone of hands must blend seamlessly with the existing warm golden background light. Looks like a real photo taken in that exact room, not AI-generated. TikTok affiliate style. 9:16 vertical. No text, no watermark."""


VIDEO_SCENE1_PROMPT = """Image 1 = product reference, Image 2 = background reference

Animate or generate this as a natural 8-second video. Image 2 is the BACKGROUND — keep it 100% identical. Image 1 is the product.

A young woman's both hands with fair warm-toned Southeast Asian skin, short nude pink nails, wearing blue ribbed knit sweater sleeves — slowly lifting the product into frame from below naturally. Movement is slow, gentle, slightly swaying — like casually revealing a new purchase to camera. Background EXACTLY as Image 2 — do not change floor, lighting, shadows, wall in any way. Lighting and shadows blend naturally with warm golden room light. Slightly handheld feel, soft natural bokeh, warm golden daylight. Casual TikTok affiliate haul mood. Not HD, not studio-lit. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


VIDEO_SCENE2_PROMPT = """Continuing from previous shot — same product, same fair warm-toned hands, nude pink nails, same blue ribbed knit sweater sleeves, same warm oak wood floor with golden sunlight patches — do not change background. Camera slowly drifts close-up across the product details. Movement dreamy and slow. One hand holds steady, other hand rotates slightly for detail view. Soft bokeh, warm golden daylight, slight film grain. Not HD. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


# =====================================================================
# ROUTES
# =====================================================================
@app.get("/", response_class=HTMLResponse)
def index():
    try:
        with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>MINJI Tools</h1><p>index.html not found</p>", status_code=500)


@app.post("/")
async def api_handler(request: Request):
    """Main API endpoint — handles all actions from frontend."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    action = body.get("action", "")

    # ── ACTION: submit-bulk ──
    if action == "submit-bulk":
        items = body.get("items", [])
        if not items:
            return JSONResponse({"ok": False, "detail": "No items provided"})

        rows = []
        for item in items:
            tanggal = datetime.now().strftime("%d/%m/%Y")
            row = [
                tanggal,
                item.get("produk", "-"),
                item.get("merk", ""),
                item.get("warna", ""),
                item.get("kategori", ""),
                item.get("status", "Belum"),
                item.get("link_drive", ""),
                item.get("link_tokopedia", ""),
            ]
            rows.append(row)

        try:
            append_rows(rows)
            return JSONResponse({"ok": True, "added": len(rows), "skipped": 0})
        except Exception as e:
            return JSONResponse({"ok": False, "detail": str(e)})

    # ── ACTION: generate-prompt ──
    elif action == "generate-prompt":
        mode = body.get("mode", "foto")
        if mode == "foto":
            return JSONResponse({"ok": True, "mode": "foto", "prompt": PHOTO_PROMPT})
        else:
            return JSONResponse({"ok": True, "mode": "video", "scene1": VIDEO_SCENE1_PROMPT, "scene2": VIDEO_SCENE2_PROMPT})

    # ── ACTION: stats ──
    elif action == "stats":
        if not SHEETS_ENABLED:
            return JSONResponse({"ok": True, "total": 0, "sudah": 0, "belum": 0, "kategori": [], "recent": []})
        try:
            svc = get_sheets_service()
            r = svc.spreadsheets().values().get(
                spreadsheetId=SHEET_ID, range=f"{SHEET_TAB}!A:H"
            ).execute()
            vals = r.get("values", [])
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
            return JSONResponse({"ok": True, "total": total, "sudah": sudah, "belum": belum, "kategori": top_kat, "recent": recent})
        except Exception as e:
            return JSONResponse({"ok": False, "detail": str(e)})

    else:
        return JSONResponse({"ok": False, "detail": f"Unknown action: {action}"})


@app.get("/health")
def health():
    return {"ok": True, "app": "MINJI Tools"}


@app.get("/api/products")
def get_products():
    """Fetch all products from Google Sheets (gviz JSON — supports hyperlinks + checkbox)."""
    import re
    import httpx
    SHEET_GVIZ = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?sheet={SHEET_TAB}"
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            r = client.get(SHEET_GVIZ)
            r.raise_for_status()
        # gviz wraps JSON in google.visualization.Query.setResponse(...);
        m = re.search(r'setResponse\((.*)\);?\s*$', r.text, re.DOTALL)
        if not m:
            return JSONResponse({"ok": False, "detail": "Failed to parse gviz response"})
        data = json.loads(m.group(1))
        rows = data.get("table", {}).get("rows", [])
        products = []
        count = 0
        for row in rows:
            cells = row.get("c", [])
            def cell(i):
                c = cells[i] if i < len(cells) and cells[i] else None
                return (c.get("v") or "") if c else ""
            nama = str(cell(1)).strip()
            if not nama:
                continue
            count += 1
            # Parse gviz date format: Date(2026,3,6) → 04/06/2026 (month is 0-indexed)
            raw_date = str(cell(0)).strip()
            tanggal = raw_date
            if raw_date.startswith("Date("):
                try:
                    parts = raw_date[5:-1].split(",")
                    y, m, d = int(parts[0]), int(parts[1]) + 1, int(parts[2])
                    tanggal = f"{d:02d}/{m:02d}/{y}"
                except Exception:
                    pass
            # Edit checkbox: column no longer exists, default False (frontend uses localStorage)
            is_edited = False
            products.append({
                "no": count,
                "tanggal": tanggal,
                "produk": nama,
                "merk": str(cell(2)).strip(),
                "warna": str(cell(3)).strip(),
                "kategori": str(cell(4)).strip(),
                "status": str(cell(5)).strip(),
                "link_drive": str(cell(6)).strip() if str(cell(6)).startswith("http") else "",
                "edited": is_edited,
                "link_tokopedia": str(cell(7)).strip() if str(cell(7)).startswith("http") else "",
            })
        return JSONResponse({"ok": True, "count": len(products), "products": products})
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)})


@app.post("/sheets")
async def sheets_proxy(request: Request):
    """Proxy requests to Apps Script to avoid CORS issues."""
    import httpx
    APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzLVRazxD8tdkKkpIfph-iJYuwmV-_lAC2PnYCq85M-PBYoItzQh7qnQq-yGr1NJYuAdw/exec"
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            r = await client.post(
                APPS_SCRIPT_URL,
                content=json.dumps(body),
                headers={"Content-Type": "text/plain"},
            )
            # Try to parse as JSON, fallback to error message
            try:
                data = r.json()
                return JSONResponse(status_code=200, content=data)
            except Exception:
                # Apps Script returned HTML instead of JSON
                text = r.text
                # Check for real errors (validation, permission)
                if "validation" in text.lower() or "melanggar" in text.lower():
                    import re
                    msg = re.findall(r'<div[^>]*>(.*?)</div>', text)
                    detail = msg[-1] if msg else "Data validation error in Google Sheets"
                    return JSONResponse(status_code=200, content={"ok": False, "detail": detail})
                # Apps Script wrote data but returned HTML (Page Not Found etc)
                # Treat as success — data was written
                if body.get("action") == "submit-bulk":
                    items = body.get("items", [])
                    return JSONResponse(status_code=200, content={"ok": True, "added": len(items)})
                return JSONResponse(status_code=200, content={"ok": False, "detail": "Apps Script error: " + text[:200]})
        except Exception as e:
            return JSONResponse(status_code=500, content={"ok": False, "detail": str(e)})


@app.post("/generate-prompt")
async def generate_prompt_endpoint(request: Request):
    """Generate prompt — returns clean English master prompt (no placeholders)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    mode = body.get("mode", "foto")

    if mode == "foto":
        return JSONResponse({"ok": True, "mode": "foto", "prompt": PHOTO_PROMPT})
    else:
        return JSONResponse({"ok": True, "mode": "video", "scene1": VIDEO_SCENE1_PROMPT, "scene2": VIDEO_SCENE2_PROMPT})
