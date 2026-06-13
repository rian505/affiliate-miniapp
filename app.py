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
# PROMPT GENERATION — from master prompt templates
# =====================================================================
def gen_photo_prompt(nama, warna, pegang, sweater, detail):
    """Generate Gemini photo prompt from user input."""
    deskripsi = f"{warna} {nama}"
    if detail:
        deskripsi += f" with {detail}"

    return f"""Image 1 = product reference, Image 2 = background reference

I am providing TWO reference images. Image 2 is the BACKGROUND — keep it 100% identical, do not change anything about it. Image 1 is the product to place into the scene. Do not replace, recreate, or modify the background floor, lighting, shadows, wall, or color tone in any way whatsoever. Only add the hands and {nama} naturally into the existing background scene.

Into this EXACT background, add: two real human hands with fair warm-toned Southeast Asian skin, short nude pink nails, wearing {sweater} ribbed knit sweater sleeves — {pegang} — {deskripsi}. Do not alter the shape, size, texture, or any detail of the product in any way. Lighting, shadow, and skin tone of hands must blend seamlessly with the existing warm golden background light. Looks like a real photo taken in that exact room, not AI-generated. TikTok affiliate style. 9:16 vertical. No text, no watermark."""


def gen_scene1_prompt(nama, warna, pegang, sweater, detail):
    """Generate Google Flow Scene 1 — Reveal prompt."""
    deskripsi = f"{warna} {nama}"
    if detail:
        deskripsi += f" with {detail}"

    return f"""Image 1 = product reference, Image 2 = background reference

Animate or generate this as a natural 8-second video. Image 2 is the BACKGROUND — keep it 100% identical. Image 1 is the product.

A young woman's both hands with fair warm-toned Southeast Asian skin, short nude pink nails, wearing {sweater} ribbed knit sweater sleeves — slowly lifting {deskripsi} into frame from below naturally. {pegang}. Movement is slow, gentle, slightly swaying — like casually revealing a new purchase to camera. Background EXACTLY as Image 2 — do not change floor, lighting, shadows, wall in any way. Lighting and shadows blend naturally with warm golden room light. Slightly handheld feel, soft natural bokeh, warm golden daylight. Casual TikTok affiliate haul mood. Not HD, not studio-lit. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


def gen_scene2_prompt(nama, warna, sweater, detail):
    """Generate Google Flow Scene 2 — Detail Close Up prompt."""
    detail_text = detail if detail else f"the texture, color, and finish of the {nama}"

    return f"""Continuing from previous shot — same {nama}, same fair warm-toned hands, nude pink nails, same {sweater} ribbed knit sweater sleeves, same warm oak wood floor with golden sunlight patches — do not change background. Camera slowly drifts close-up across {detail_text}. Movement dreamy and slow. One hand holds steady, other hand rotates slightly for detail view. Soft bokeh, warm golden daylight, slight film grain. Not HD. No text, no voiceover, no watermark. 9:16 vertical. 8 seconds."""


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
        nama = body.get("nama", "").strip()
        warna = body.get("warna", "").strip()
        pegang = body.get("pegang", "").strip()
        sweater = body.get("sweater", "blue").strip()
        detail = body.get("detail", "").strip()

        if not nama:
            return JSONResponse({"ok": False, "detail": "Nama produk wajib diisi"})

        if mode == "foto":
            prompt = gen_photo_prompt(nama, warna, pegang, sweater, detail)
            return JSONResponse({"ok": True, "mode": "foto", "prompt": prompt})
        else:
            scene1 = gen_scene1_prompt(nama, warna, pegang, sweater, detail)
            scene2 = gen_scene2_prompt(nama, warna, sweater, detail)
            return JSONResponse({"ok": True, "mode": "video", "scene1": scene1, "scene2": scene2})

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
                # Apps Script returned HTML error
                text = r.text
                if "validation" in text.lower() or "melanggar" in text.lower():
                    import re
                    msg = re.findall(r'<div[^>]*>(.*?)</div>', text)
                    detail = msg[-1] if msg else "Data validation error in Google Sheets"
                    return JSONResponse(status_code=200, content={"ok": False, "detail": detail})
                return JSONResponse(status_code=200, content={"ok": False, "detail": "Apps Script error: " + text[:200]})
        except Exception as e:
            return JSONResponse(status_code=500, content={"ok": False, "detail": str(e)})


@app.post("/generate-prompt")
async def generate_prompt_endpoint(request: Request):
    """Generate prompt from user input."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    mode = body.get("mode", "foto")
    nama = body.get("nama", "").strip()
    warna = body.get("warna", "").strip()
    pegang = body.get("pegang", "").strip()
    sweater = body.get("sweater", "blue").strip()
    detail = body.get("detail", "").strip()

    if not nama:
        return JSONResponse({"ok": False, "detail": "Nama produk wajib diisi"})

    if mode == "foto":
        prompt = gen_photo_prompt(nama, warna, pegang, sweater, detail)
        return JSONResponse({"ok": True, "mode": "foto", "prompt": prompt})
    else:
        scene1 = gen_scene1_prompt(nama, warna, pegang, sweater, detail)
        scene2 = gen_scene2_prompt(nama, warna, sweater, detail)
        return JSONResponse({"ok": True, "mode": "video", "scene1": scene1, "scene2": scene2})
