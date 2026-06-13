import app

svc = app.get_sheets_service()


def rowcount():
    r = svc.spreadsheets().values().get(
        spreadsheetId=app.SHEET_ID, range=app.SHEET_TAB + "!A:H"
    ).execute()
    return r.get("values", [])


before = rowcount()
print("Rows before:", len(before))

app.append_row(["__TEST__", "__MINIAPP_TEST__", "", "", "", "Belum", "", "https://test"])

after = rowcount()
print("Rows after :", len(after))
print("Row terakhir:", after[-1])

# Cleanup: hapus row test yang barusan ditambah
if after and after[-1][1] == "__MINIAPP_TEST__":
    last_idx = len(after)  # 1-indexed sheet row
    svc.spreadsheets().batchUpdate(
        spreadsheetId=app.SHEET_ID,
        body={
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": None,  # filled below
                            "dimension": "ROWS",
                            "startIndex": last_idx - 1,
                            "endIndex": last_idx,
                        }
                    }
                }
            ]
        },
    ) if False else None  # placeholder; real delete below

# Proper delete using sheetId lookup
meta = svc.spreadsheets().get(spreadsheetId=app.SHEET_ID).execute()
sheet_id = next(
    s["properties"]["sheetId"]
    for s in meta["sheets"]
    if s["properties"]["title"] == app.SHEET_TAB
)
last_idx = len(after)
svc.spreadsheets().batchUpdate(
    spreadsheetId=app.SHEET_ID,
    body={
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": last_idx - 1,
                        "endIndex": last_idx,
                    }
                }
            }
        ]
    },
).execute()
final = rowcount()
print("Rows after cleanup:", len(final))
print("CLEANUP OK" if len(final) == len(before) else "CLEANUP MISMATCH")
