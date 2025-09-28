import requests
import time
from datetime import datetime, timedelta, timezone

# --- KONFIGURASI ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1421895028497842257/HiZSmlDs1Mp6y3h4IgvgjnzvSI_iIcuWhuv9KWejw_-v9a3vH5tUqhRcN-3r8YJ8V3xE"
DISCORD_USER_ID = 403841497981517825
CHECK_INTERVAL = 60  # cek setiap 60 detik

# --- WIB TIMEZONE ---
WIB = timezone(timedelta(hours=7))

def get_wib_time():
    return datetime.now(WIB).strftime("%d-%m-%Y %H:%M:%S")

# --- GROUP VIP ---
VIP_GROUPS = {
    "VIP 1": ["asakurashin108", "nagumoyoichi108", "dukunberanak108"],
    "VIP 2": ["buaqitajambu108", "buaqitaleci108", "buaqitaapel108"],
    "VIP 3": ["peternakikan108", "sepuhsecret108", "dewakipas108"],
    "VIP 4": ["sipalingkeren108", "sipalingcupu108", "sipalinghoki108"],
    "VIP 5": ["estehbotol108", "estehgelas108", "estehgalon108"],
    "VIP 6": ["akubaconbaik108", "kamubaconbaik108", "sayabaconbaik108"],
    "VIP 7": ["sidewajago01", "sidewajago02"],
    "VIP 8": ["everythinguare108", "satuharilagi108", "jammakansiang108"],
    "VIP 9": ["skinforsaken108", "skinkuronami108", "skinblubub108"],
    "VIP 10": ["mauikanecret108", "mauikanmythic108", "mauikanlejen108"]
}

# --- CONVERT USERNAME KE USERID ---
def get_user_ids(usernames: list[str]):
    url = "https://users.roblox.com/v1/usernames/users"
    try:
        res = requests.post(url, json={"usernames": usernames}, timeout=10)
        res.raise_for_status()
        data = res.json()
        return {u["name"]: u["id"] for u in data.get("data", [])}
    except Exception as e:
        print(f"[ERROR] Gagal ambil UserId: {e}")
        return {}

# --- CEK STATUS ---
def get_online_status(user_ids: list[int]):
    url = "https://presence.roblox.com/v1/presence/users"
    try:
        res = requests.post(url, json={"userIds": user_ids}, timeout=10)
        res.raise_for_status()
        return res.json().get("userPresences", [])
    except Exception as e:
        print(f"[ERROR] Gagal cek status: {e}")
        return []

# --- KIRIM DISCORD EMBED ---
def send_embed_status(group_lines: dict, summary: dict):
    fields = []
    for group_name, lines in group_lines.items():
        fields.append({
            "name": group_name,
            "value": "\n".join(lines) if lines else "-",
            "inline": False
        })

    # tambahkan kesimpulan + waktu WIB
    summary_text = (
        f"✅ ONLINE: {summary['online']}\n"
        f"🐟 IN FISH IT: {summary['ingame']}\n"
        f"🛠️ IN STUDIO: {summary['studio']}\n"
        f"❌ OFFLINE: {summary['offline']}\n"
        f"⏰ Waktu (WIB): {get_wib_time()}"
    )

    fields.append({
        "name": "Kesimpulan",
        "value": summary_text,
        "inline": False
    })

    embed = {
        "title": "📊 Roblox Online Status",
        "color": 0x00ffcc,
        "fields": fields,
        "footer": {"text": "Update otomatis setiap 1 menit"}
    }

    payload = {"embeds": [embed]}
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] Gagal kirim Discord: {e}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    all_usernames = [u for group in VIP_GROUPS.values() for u in group]
    user_map_ids = get_user_ids(all_usernames)

    if not user_map_ids:
        print("Tidak bisa ambil UserId, cek username.")
        exit()

    print(f"Monitoring: {user_map_ids}")

    while True:
        presences = get_online_status(list(user_map_ids.values()))
        presence_map = {p["userId"]: p for p in presences}

        group_lines = {}
        summary = {"online": 0, "ingame": 0, "studio": 0, "offline": 0}

        for group_name, usernames in VIP_GROUPS.items():
            lines = []
            for username in usernames:
                uid = user_map_ids.get(username)
                if not uid:
                    continue
                presence = presence_map.get(uid, {})
                presence_type = presence.get("userPresenceType", 0)
                last_location = presence.get("lastLocation", "")
                place_id = presence.get("placeId", None)

                status_text = {
                    0: "OFFLINE ❌",
                    1: "ONLINE ✅",
                    2: "IN FISH IT!🐟",
                    3: "IN STUDIO 🛠️"
                }.get(presence_type, "UNKNOWN ❓")

                if presence_type == 2 and place_id:
                    status_text += f" → {last_location} (PlaceId: {place_id})"

                if presence_type == 0:
                    summary["offline"] += 1
                elif presence_type == 1:
                    summary["online"] += 1
                elif presence_type == 2:
                    summary["ingame"] += 1
                elif presence_type == 3:
                    summary["studio"] += 1

                if presence_type == 0 and DISCORD_USER_ID:
                    lines.append(f"**{username}**: {status_text} <@{DISCORD_USER_ID}>")
                else:
                    lines.append(f"**{username}**: {status_text}")

            group_lines[group_name] = lines

        send_embed_status(group_lines, summary)

        print("=== STATUS UPDATE ===")
        for g, ls in group_lines.items():
            print(f"[{g}]")
            print("\n".join(ls))
        print("Kesimpulan:", summary, "Waktu:", get_wib_time())
        print("=====================")

        time.sleep(CHECK_INTERVAL)
