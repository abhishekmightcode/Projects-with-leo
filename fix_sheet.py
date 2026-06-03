import json, urllib.request, urllib.parse

TOKEN = "/home/aiops/.openclaw/workspace/google-credentials/token.json"
SHEET = "1HWmgUfy4Wr6hz2FVLLPf2OmLx352fYghVFNUjBMKcUM"
with open(TOKEN) as f:
    t = json.load(f)
data = urllib.parse.urlencode({"client_id":t["client_id"],"client_secret":t["client_secret"],"refresh_token":t["refresh_token"],"grant_type":"refresh_token"}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, headers={"Content-Type":"application/x-www-form-urlencoded"})
with urllib.request.urlopen(req) as r:
    t["access_token"] = json.loads(r.read())["access_token"]
with open(TOKEN, "w") as f:
    json.dump(t, f, indent=2)

req = urllib.request.Request(f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET}/values/Sheet1", headers={"Authorization":f"Bearer {t['access_token']}"})
with urllib.request.urlopen(req) as r:
    rows = json.loads(r.read()).get("values", [])

# Count unique types
types = {}
for row in rows[1:]:
    if len(row)>=2 and row[1].strip():
        t2 = row[1].strip()
        types[t2] = types.get(t2, 0) + 1

# Unique colleges by name
names = set()
for row in rows[1:]:
    if row and row[0].strip():
        names.add(row[0].strip())

print(f"Unique colleges: {len(names)}")
print(f"\nTypes: {json.dumps(dict(sorted(types.items(), key=lambda x:-x[1])), indent=2)}")

# All regions
regions = set()
for row in rows[1:]:
    if len(row)>=3 and row[2].strip():
        regions.add(row[2].strip())
print(f"\nAll regions ({len(regions)}):")
for r in sorted(regions):
    print(f"  {r}")
PYEOF