#!/usr/bin/env python3
"""
FORGE OS Daily Brief Generator - GITHUB ACTIONS VERSION
No interactive prompts. Reads Welltory/Sleep from data.json.
Fetches weather and calendar automatically.
Saves index.html for GitHub Pages.
Pushes 7-day calendar to JSONBin for Evening Debrief.
"""

import os
import json
import caldav
import vobject
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta, timezone


import datetime as _dt

JLPT_WORDS = [
    {"word": "刹那 (Setsuna)", "level": "N1", "meaning": "A fleeting moment; the infinitesimal instant.", "example": "人生は刹那の連続だ", "translation": "Life is a succession of fleeting moments."},
    {"word": "余韻 (Yoin)", "level": "N1", "meaning": "Lingering reverberation; an afterglow of feeling.", "example": "音楽の余韻に浸る", "translation": "To be immersed in the lingering notes of music."},
    {"word": "葛藤 (Kattou)", "level": "N1", "meaning": "Inner conflict; mental struggle.", "example": "葛藤を乗り越えた", "translation": "He overcame his inner conflict."},
    {"word": "侘寂 (Wabi-sabi)", "level": "N1", "meaning": "Beauty in imperfection and impermanence.", "example": "古い茶碗に侘寂を感じる", "translation": "I feel wabi-sabi in the old tea bowl."},
    {"word": "幽玄 (Yuugen)", "level": "N1", "meaning": "Profound, mysterious sense of the universe.", "example": "能楽には幽玄の美がある", "translation": "Noh theater has the beauty of yuugen."},
    {"word": "物の哀れ (Mono no aware)", "level": "N1", "meaning": "Bittersweet awareness of impermanence.", "example": "桜の散る様に物の哀れを感じる", "translation": "I feel it in falling cherry blossoms."},
    {"word": "矜持 (Kyouji)", "level": "N1", "meaning": "Pride; self-respect; sense of dignity.", "example": "プロとしての矜持を持つ", "translation": "To have pride as a professional."},
    {"word": "僥倖 (Gyoukou)", "level": "N1", "meaning": "Unexpected good fortune; windfall luck.", "example": "それは僥倖だった", "translation": "That was a stroke of unexpected luck."},
    {"word": "懸念 (Kenen)", "level": "N2", "meaning": "Concern; worry; apprehension.", "example": "健康への懸念がある", "translation": "There is concern about health."},
    {"word": "顕著 (Kenchyo)", "level": "N2", "meaning": "Remarkable; conspicuous; notable.", "example": "顕著な改善が見られた", "translation": "A remarkable improvement was observed."},
    {"word": "体裁 (Teisai)", "level": "N2", "meaning": "Outward appearance; keeping up appearances.", "example": "体裁を気にしすぎる", "translation": "To care too much about appearances."},
    {"word": "逡巡 (Shunjun)", "level": "N2", "meaning": "Hesitation; wavering indecision.", "example": "逡巡せずに決断した", "translation": "He decided without hesitation."},
    {"word": "慮る (Omonpakaru)", "level": "N1", "meaning": "To give careful consideration.", "example": "相手の立場を慮る", "translation": "To consider the other person's position."},
    {"word": "凛然 (Rinzen)", "level": "N1", "meaning": "Dignified and resolute; commanding.", "example": "凛然とした態度", "translation": "A dignified and resolute attitude."},
]

ART_ENTRIES = [
    {"title": "Hokusai — The Great Wave off Kanagawa", "url": "https://artsandculture.google.com/search?q=hokusai+great+wave"},
    {"title": "Kusama Yayoi — Infinity Mirror Room", "url": "https://artsandculture.google.com/search?q=kusama+infinity+mirror"},
    {"title": "Basquiat — Untitled (1982)", "url": "https://artsandculture.google.com/search?q=basquiat+untitled+1982"},
    {"title": "Rothko — No. 61 (Rust and Blue)", "url": "https://artsandculture.google.com/search?q=rothko+rust+blue"},
    {"title": "Francis Bacon — Three Studies for Figures", "url": "https://artsandculture.google.com/search?q=francis+bacon+three+studies"},
    {"title": "Egon Schiele — Self-Portrait (1912)", "url": "https://artsandculture.google.com/search?q=egon+schiele+self+portrait"},
    {"title": "Hiroshi Sugimoto — Seascapes", "url": "https://artsandculture.google.com/search?q=hiroshi+sugimoto+seascapes"},
    {"title": "Goya — Saturn Devouring His Son", "url": "https://artsandculture.google.com/search?q=goya+saturn+devouring"},
    {"title": "Caravaggio — Judith Beheading Holofernes", "url": "https://artsandculture.google.com/search?q=caravaggio+judith"},
    {"title": "Turner — The Fighting Temeraire", "url": "https://artsandculture.google.com/search?q=turner+fighting+temeraire"},
    {"title": "Frida Kahlo — The Two Fridas", "url": "https://artsandculture.google.com/search?q=frida+kahlo+two+fridas"},
    {"title": "William Blake — Ancient of Days", "url": "https://artsandculture.google.com/search?q=william+blake+ancient+of+days"},
    {"title": "Jenny Saville — Propped", "url": "https://artsandculture.google.com/search?q=jenny+saville+propped"},
    {"title": "Monet — Water Lilies Series", "url": "https://artsandculture.google.com/search?q=monet+water+lilies"},
]

MUSIC_ENTRIES = [
    {"title": "Dissection — Storm of the Light's Bane (1995)", "spotify": "https://open.spotify.com/search/dissection%20storm%20of%20the%20lights%20bane", "youtube": "https://music.youtube.com/search?q=dissection+storm+lights+bane"},
    {"title": "Sarcofago — I.N.R.I. (1987)", "spotify": "https://open.spotify.com/search/sarcofago%20inri", "youtube": "https://music.youtube.com/search?q=sarcofago+inri"},
    {"title": "Emperor — In the Nightside Eclipse (1994)", "spotify": "https://open.spotify.com/search/emperor%20nightside%20eclipse", "youtube": "https://music.youtube.com/search?q=emperor+nightside+eclipse"},
    {"title": "Carcass — Heartwork (1993)", "spotify": "https://open.spotify.com/search/carcass%20heartwork", "youtube": "https://music.youtube.com/search?q=carcass+heartwork"},
    {"title": "Pantera — Vulgar Display of Power (1992)", "spotify": "https://open.spotify.com/search/pantera%20vulgar%20display", "youtube": "https://music.youtube.com/search?q=pantera+vulgar+display"},
    {"title": "Entombed — Left Hand Path (1990)", "spotify": "https://open.spotify.com/search/entombed%20left%20hand%20path", "youtube": "https://music.youtube.com/search?q=entombed+left+hand+path"},
    {"title": "Immortal — Pure Holocaust (1993)", "spotify": "https://open.spotify.com/search/immortal%20pure%20holocaust", "youtube": "https://music.youtube.com/search?q=immortal+pure+holocaust"},
    {"title": "Type O Negative — Bloody Kisses (1993)", "spotify": "https://open.spotify.com/search/type%20o%20negative%20bloody%20kisses", "youtube": "https://music.youtube.com/search?q=type+o+negative+bloody+kisses"},
    {"title": "Saor — Guardians (2016)", "spotify": "https://open.spotify.com/search/saor%20guardians", "youtube": "https://music.youtube.com/search?q=saor+guardians"},
    {"title": "Motorhead — Ace of Spades (1980)", "spotify": "https://open.spotify.com/search/motorhead%20ace%20of%20spades", "youtube": "https://music.youtube.com/search?q=motorhead+ace+of+spades"},
    {"title": "Slayer — Reign in Blood (1986)", "spotify": "https://open.spotify.com/search/slayer%20reign%20in%20blood", "youtube": "https://music.youtube.com/search?q=slayer+reign+in+blood"},
    {"title": "Behemoth — The Satanist (2014)", "spotify": "https://open.spotify.com/search/behemoth%20the%20satanist", "youtube": "https://music.youtube.com/search?q=behemoth+the+satanist"},
    {"title": "Danzig — Lucifuge (1990)", "spotify": "https://open.spotify.com/search/danzig%20lucifuge", "youtube": "https://music.youtube.com/search?q=danzig+lucifuge"},
    {"title": "Machine Head — Burn My Eyes (1994)", "spotify": "https://open.spotify.com/search/machine%20head%20burn%20my%20eyes", "youtube": "https://music.youtube.com/search?q=machine+head+burn+my+eyes"},
]

CHARACTER_QUOTES = [
    {"name": "Hannibal Smith", "quote": "I love it when a plan comes together.", "show": "The A-Team", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/d/da/Hannibal_Smith.jpg/220px-Hannibal_Smith.jpg"},
    {"name": "Zack Morris", "quote": "The more rules they make, the more ways I find to get around them.", "show": "Saved by the Bell", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0f/Zack_Morris.jpg/220px-Zack_Morris.jpg"},
    {"name": "Eddie Haskell", "quote": "Gee Beaver, I would love to help, but something just came up.", "show": "Leave it to Beaver", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/3/32/Eddie_Haskell.jpg/220px-Eddie_Haskell.jpg"},
    {"name": "Al Bundy", "quote": "I had it all once. Now I am married with children.", "show": "Married... with Children", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Al_Bundy.jpg/220px-Al_Bundy.jpg"},
    {"name": "Hannibal Smith", "quote": "The best thing about being underestimated is the look on their face when you win.", "show": "The A-Team", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/d/da/Hannibal_Smith.jpg/220px-Hannibal_Smith.jpg"},
    {"name": "Al Bundy", "quote": "Women. You cannot live with them, period.", "show": "Married... with Children", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Al_Bundy.jpg/220px-Al_Bundy.jpg"},
    {"name": "Zack Morris", "quote": "Time out. Let me think about this.", "show": "Saved by the Bell", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0f/Zack_Morris.jpg/220px-Zack_Morris.jpg"},
    {"name": "Hannibal Smith", "quote": "In war, the most dangerous weapon is the element of surprise.", "show": "The A-Team", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/d/da/Hannibal_Smith.jpg/220px-Hannibal_Smith.jpg"},
    {"name": "Eddie Haskell", "quote": "That is a very lovely dress, Mrs. Cleaver.", "show": "Leave it to Beaver", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/3/32/Eddie_Haskell.jpg/220px-Eddie_Haskell.jpg"},
    {"name": "Al Bundy", "quote": "Every day above ground is a good day. Every day in this house is debatable.", "show": "Married... with Children", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Al_Bundy.jpg/220px-Al_Bundy.jpg"},
    {"name": "Hannibal Smith", "quote": "You know, sometimes the best disguise is no disguise at all.", "show": "The A-Team", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/d/da/Hannibal_Smith.jpg/220px-Hannibal_Smith.jpg"},
    {"name": "Zack Morris", "quote": "When life gives you lemons, sell them.", "show": "Saved by the Bell", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0f/Zack_Morris.jpg/220px-Zack_Morris.jpg"},
    {"name": "Eddie Haskell", "quote": "I was merely trying to be helpful, sir.", "show": "Leave it to Beaver", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/3/32/Eddie_Haskell.jpg/220px-Eddie_Haskell.jpg"},
    {"name": "Al Bundy", "quote": "A man can take just so much. Then he snaps.", "show": "Married... with Children", "image": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Al_Bundy.jpg/220px-Al_Bundy.jpg"},
]


STOIC_QUOTES = [
    {"text": "You have power over your mind, not outside events. Realize this, and you will find strength.", "source": "Marcus Aurelius, Meditations"},
    {"text": "The impediment to action advances action. What stands in the way becomes the way.", "source": "Marcus Aurelius, Meditations"},
    {"text": "Waste no more time arguing what a good man should be. Be one.", "source": "Marcus Aurelius, Meditations"},
    {"text": "If it is not right, do not do it. If it is not true, do not say it.", "source": "Marcus Aurelius, Meditations"},
    {"text": "The best revenge is to be unlike him who performed the injury.", "source": "Marcus Aurelius, Meditations"},
    {"text": "He who knows when he can fight and when he cannot will be victorious.", "source": "Sun Tzu, The Art of War"},
    {"text": "Supreme excellence consists in breaking the enemy's resistance without fighting.", "source": "Sun Tzu, The Art of War"},
    {"text": "In the midst of chaos, there is also opportunity.", "source": "Sun Tzu, The Art of War"},
    {"text": "Do not seek to follow in the footsteps of the wise. Seek what they sought.", "source": "Matsuo Basho"},
    {"text": "There is nothing outside of yourself that can ever enable you to get better, stronger, richer, quicker, or smarter. Everything is within.", "source": "Miyamoto Musashi, The Book of Five Rings"},
    {"text": "Today is victory over yourself of yesterday. Tomorrow is victory over lesser men.", "source": "Miyamoto Musashi"},
    {"text": "Think lightly of yourself and deeply of the world.", "source": "Miyamoto Musashi"},
    {"text": "The man who moves a mountain begins by carrying away small stones.", "source": "Confucius"},
    {"text": "He who has a why to live can bear almost any how.", "source": "Friedrich Nietzsche"},
    {"text": "That which does not kill us makes us stronger.", "source": "Friedrich Nietzsche"},
    {"text": "Whoever fights monsters should see to it that in the process he does not become a monster.", "source": "Friedrich Nietzsche"},
    {"text": "The only way to deal with an unfree world is to become so absolutely free that your very existence is an act of rebellion.", "source": "Albert Camus"},
    {"text": "You must be the change you wish to see in the world.", "source": "Mahatma Gandhi"},
    {"text": "It does not matter how slowly you go as long as you do not stop.", "source": "Confucius"},
    {"text": "Stillness is what creates love. Movement is what creates life. To be still and still moving — that is everything.", "source": "Do Hyun Choe"},
    {"text": "Absorb what is useful, discard what is not, add what is uniquely your own.", "source": "Bruce Lee"},
    {"text": "I fear not the man who has practiced 10,000 kicks once, but I fear the man who has practiced one kick 10,000 times.", "source": "Bruce Lee"},
    {"text": "The more I know, the more I realize I know nothing.", "source": "Socrates"},
    {"text": "An unexamined life is not worth living.", "source": "Socrates"},
    {"text": "We suffer more in imagination than in reality.", "source": "Seneca"},
    {"text": "It is not that I am brave, it is just that I am right.", "source": "David Hackworth"},
    {"text": "Victorious warriors win first and then go to war. Defeated warriors go to war first and then seek to win.", "source": "Sun Tzu"},
    {"text": "The most courageous act is still to think for yourself. Aloud.", "source": "Coco Chanel"},
]

def get_daily_index(list_len):
    return _dt.date.today().timetuple().tm_yday % list_len

RICHMOND_COORDS = (49.1895, -123.1724)
ICLOUD_EMAIL = os.environ.get("ICLOUD_EMAIL", "yoseanreid@icloud.com")
ICLOUD_PASSWORD = os.environ.get("ICLOUD_PASSWORD", "")
JSONBIN_MASTER_KEY = "$2a$10$rs9Sak4dqIbcRvK1M.wAnOkEz1PsUKu.DqrastjCx2npbrJYr3r/2"
JSONBIN_CAL_BIN = "6a277510da38895dfe9d6de0"

def load_user_data():
    """Load Welltory + Sleep data from data.json."""
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {
            "welltory": {"stress": 50, "energy": 50, "health": 50},
            "sleep": {"score": 85, "duration": "7h 0m", "hr_range": "50–70"}
        }

def get_weather():
    """Fetch weather for Richmond, BC."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={RICHMOND_COORDS[0]}&longitude={RICHMOND_COORDS[1]}&current=temperature_2m,weather_code&temperature_unit=celsius&timezone=America/Vancouver"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            temp = data.get("current", {}).get("temperature_2m", "N/A")
            code = data.get("current", {}).get("weather_code", 0)
            desc = {0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Foggy",51:"Light drizzle",61:"Slight rain",80:"Rain showers",95:"Thunderstorm"}.get(code, "Cloudy")
            return f"{desc}, {temp}°C"
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"Weather fetch failed: {e}")
        return "Weather unavailable"

def fetch_events_for_range(calendars, start, end):
    """Fetch and format events for a given date range."""
    all_events = []
    for calendar in calendars:
        try:
            events = calendar.date_search(start=start, end=end, expand=True)
            for event in events:
                try:
                    vevent = event.vobject_instance.vevent
                    summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "Event"
                    dtstart = vevent.dtstart.value
                    if hasattr(dtstart, 'hour'):
                        all_events.append((str(dtstart), f"{summary} @ {dtstart.strftime('%a %b %d, %I:%M %p')}"))
                    else:
                        all_events.append((str(dtstart), f"{summary} — {dtstart.strftime('%a %b %d')} (All Day)"))
                except:
                    continue
        except:
            continue
    all_events.sort(key=lambda x: x[0])
    return [e[1] for e in all_events]

def fetch_events_structured(calendars, start, end):
    """Fetch events as structured list for JSONBin storage."""
    all_events = []
    for calendar in calendars:
        try:
            events = calendar.date_search(start=start, end=end, expand=True)
            for event in events:
                try:
                    vevent = event.vobject_instance.vevent
                    summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "Event"
                    dtstart = vevent.dtstart.value
                    if hasattr(dtstart, 'hour'):
                        all_events.append({
                            "sort_key": str(dtstart),
                            "date": dtstart.strftime('%a %b %d'),
                            "time": dtstart.strftime('%I:%M %p'),
                            "title": summary
                        })
                    else:
                        all_events.append({
                            "sort_key": str(dtstart),
                            "date": dtstart.strftime('%a %b %d'),
                            "time": "All day",
                            "title": summary
                        })
                except:
                    continue
        except:
            continue
    all_events.sort(key=lambda x: x["sort_key"])
    # Remove sort_key from final output
    return [{"date": e["date"], "time": e["time"], "title": e["title"]} for e in all_events]

def get_calendar_events():
    """Fetch today, week, and 7-day structured events from iCloud via CalDAV."""
    if not ICLOUD_PASSWORD:
        return {"today": "No iCloud password configured.", "week": "", "month": "", "week_structured": []}
    
    try:
        client = caldav.DAVClient(
            url="https://caldav.icloud.com",
            username=ICLOUD_EMAIL,
            password=ICLOUD_PASSWORD
        )
        
        principal = client.principal()
        calendars = principal.calendars()
        
        today = date.today()
        tz = timezone.utc

        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=tz)
        today_end = datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(tzinfo=tz)
        week_end = datetime.combine(today + timedelta(days=7), datetime.min.time()).replace(tzinfo=tz)
        month_end = datetime.combine(today + timedelta(days=30), datetime.min.time()).replace(tzinfo=tz)

        today_events = fetch_events_for_range(calendars, today_start, today_end)
        week_events = fetch_events_for_range(calendars, today_start, week_end)
        month_events = fetch_events_for_range(calendars, today_start, month_end)
        week_structured = fetch_events_structured(calendars, today_start, week_end)

        print(f"✓ Today: {len(today_events)} | Week: {len(week_events)} | Month: {len(month_events)} events")

        return {
            "today": "\n".join(today_events) if today_events else "No events today.",
            "week": "\n".join(week_events) if week_events else "No events this week.",
            "month": "\n".join(month_events) if month_events else "No events this month.",
            "week_structured": week_structured
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"Calendar fetch failed: {e}")
        return {"today": "Calendar unavailable.", "week": "", "month": "", "week_structured": []}

def push_calendar_to_jsonbin(week_structured):
    """Embed calendar data into data.json for Evening Debrief."""
    try:
        try:
            with open("data.json", "r") as f:
                data = json.load(f)
        except:
            data = {}
        data["calendar"] = week_structured
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"✓ Calendar embedded in data.json ({len(week_structured)} events)")
    except Exception as e:
        print(f"⚠️ Calendar embed failed: {e}")

def get_character_quote(day_of_week):
    return CHARACTER_QUOTES[get_daily_index(len(CHARACTER_QUOTES))]


def generate_html(welltory, sleep, weather, calendar_events, week_structured=None):
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    day_of_week = now.weekday()

    stress_status = "Elevated" if welltory["stress"] >= 60 else "Moderate" if welltory["stress"] >= 40 else "Low"
    energy_status = "High" if welltory["energy"] >= 60 else "Moderate" if welltory["energy"] >= 40 else "Limited"
    health_status = "Optimal" if welltory["health"] >= 60 else "Vulnerable" if welltory["health"] >= 30 else "At Risk"

    if welltory["stress"] >= 70 or welltory["energy"] <= 40:
        mode = "RECOVERY DAY PROTOCOL ACTIVE"
        mode_advice = f"Health at risk. Stress {welltory['stress']}% (elevated). Energy {welltory['energy']}% (limited). No strain. No decisions. Rest only."
    elif welltory["stress"] >= 50:
        mode = "CHILL FLOW ACTIVE"
        mode_advice = "Moderate pace. Defer big decisions. Protect energy."
    else:
        mode = "NORMAL PROTOCOL ACTIVE"
        mode_advice = "Execute as planned. Stay sharp."

    char = get_character_quote(day_of_week)

    cal_json = json.dumps(week_structured or [])
    cal_today = calendar_events.get("today", "No events today.")
    stoic = STOIC_QUOTES[get_daily_index(len(STOIC_QUOTES))]
    stoic_quote = stoic["text"]; stoic_source = stoic["source"]
    jlpt = JLPT_WORDS[get_daily_index(len(JLPT_WORDS))]
    jlpt_word = jlpt["word"]; jlpt_level = jlpt["level"]; jlpt_meaning = jlpt["meaning"]
    jlpt_example = jlpt["example"]; jlpt_translation = jlpt["translation"]
    art = ART_ENTRIES[get_daily_index(len(ART_ENTRIES))]
    art_title = art["title"]; art_url = art["url"]
    music = MUSIC_ENTRIES[get_daily_index(len(MUSIC_ENTRIES))]
    music_title = music["title"]; music_spotify = music["spotify"]; music_youtube = music["youtube"]
    cal_week = calendar_events.get("week", "No events this week.")
    cal_month = calendar_events.get("month", "No events this month.")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <title>FORGE OS · Morning Brief</title>
  <style>
    :root {{
      --text-light: #1a1a1a;
      --text-bright: #0d0d0d;
      --muted: #4a4a4a;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ -webkit-text-size-adjust: 100%; }}
    body {{ 
      background: linear-gradient(135deg, #d84315 0%, #ff9800 50%, #ffc107 100%);
      color: var(--text-light);
      font-family: -apple-system, 'Segoe UI', Tahoma, sans-serif;
      min-height: 100vh;
      padding: 20px;
    }}
    .shell {{ max-width: 95vw; margin: 0 auto; }}
    @media screen and (orientation: landscape) {{
      .shell {{ max-width: 98vw; }}
      .advice-grid {{ grid-template-columns: 1fr 1fr 1fr; }}
      body {{ padding: 12px; }}
    }}
    .topbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 4px solid var(--text-bright); }}
    .forge-label {{ font-size: 26px; letter-spacing: 0.3em; color: var(--text-bright); font-weight: 700; text-transform: uppercase; }}
    .forge-sub {{ font-size: 18px; color: var(--muted); margin-top: 6px; }}
    .date-block {{ text-align: right; }}
    .date-main {{ font-size: 28px; color: var(--text-bright); font-weight: 700; }}
    .date-time {{ font-size: 16px; color: var(--muted); margin-top: 4px; }}
    .card {{ background: rgba(255,255,255,0.15); border: 3px solid var(--text-bright); border-radius: 12px; padding: 18px; margin-bottom: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }}
    .card-header {{ font-size: 16px; letter-spacing: 0.2em; color: var(--text-bright); text-transform: uppercase; margin-bottom: 14px; font-weight: 700; display: flex; align-items: center; gap: 10px; }}
    .card-icon {{ font-size: 32px; }}
    .stat-row {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 14px; }}
    .stat-block {{ background: rgba(255,255,255,0.2); border: 2px solid var(--text-bright); border-radius: 8px; padding: 14px 10px; text-align: center; }}
    .stat-val {{ font-size: 32px; font-weight: 700; line-height: 1; color: var(--text-bright); }}
    .stat-label {{ font-size: 13px; letter-spacing: 0.12em; color: var(--muted); text-transform: uppercase; margin-top: 6px; }}
    .stat-sub {{ font-size: 13px; margin-top: 4px; font-weight: 600; }}
    .motd-box {{ background: rgba(255,255,255,0.15); border: 3px solid var(--text-bright); border-radius: 12px; padding: 16px; margin-bottom: 14px; }}
    .motd-text {{ font-size: 22px; color: var(--text-bright); line-height: 1.8; font-style: italic; font-weight: 500; }}
    .motd-source {{ font-size: 16px; color: var(--text-light); margin-top: 8px; font-weight: 600; }}
    .character-quote-box {{ background: rgba(255,255,255,0.15); border: 3px solid var(--text-bright); border-radius: 12px; padding: 16px; margin-bottom: 14px; display: grid; grid-template-columns: 100px 1fr; gap: 16px; align-items: center; }}
    .character-image {{ width: 100px; height: 100px; border-radius: 8px; border: 2px solid var(--text-bright); object-fit: cover; }}
    .character-quote {{ font-size: 17px; color: var(--text-bright); font-style: italic; font-weight: 500; margin-bottom: 8px; }}
    .character-name {{ font-size: 13px; color: var(--text-light); font-weight: 600; }}
    .alert-banner {{ background: rgba(255,50,50,0.3); border: 3px solid var(--text-bright); border-radius: 8px; padding: 14px; font-size: 15px; color: var(--text-bright); margin-bottom: 14px; line-height: 1.7; font-weight: 600; }}
    .input-banner {{ background: rgba(255,255,255,0.2); border: 3px solid var(--text-bright); border-radius: 8px; padding: 14px; font-size: 15px; color: var(--text-bright); margin-bottom: 14px; line-height: 1.7; font-weight: 600; text-align: center; }}
    .input-banner a {{ color: var(--text-bright); font-size: 17px; }}
    .mini-card {{ background: rgba(255,255,255,0.12); border: 2px solid var(--text-bright); border-radius: 8px; padding: 12px; margin-bottom: 10px; }}
    .mini-title {{ font-size: 15px; color: var(--text-bright); font-weight: 700; margin-bottom: 6px; }}
    .mini-detail {{ font-size: 13px; color: var(--text-light); line-height: 1.6; }}
    .paramount-goal {{ background: rgba(255,255,255,0.2); border: 2px solid var(--text-bright); border-radius: 8px; padding: 14px; margin-bottom: 10px; font-size: 14px; color: var(--text-light); line-height: 1.7; font-weight: 600; }}
    .paramount-num {{ font-size: 15px; color: var(--text-bright); font-weight: 700; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
    .goal-controls {{ display: flex; gap: 8px; align-items: center; }}
    .goal-btn {{ background: rgba(255,255,255,0.4); border: 2px solid var(--text-bright); border-radius: 6px; padding: 8px 16px; font-weight: 700; font-size: 20px; color: var(--text-bright); cursor: pointer; touch-action: manipulation; min-width: 44px; min-height: 44px; display: flex; align-items: center; justify-content: center; }}
    .goal-btn:active {{ background: rgba(255,255,255,0.7); }}
    .goal-counter {{ background: rgba(255,255,255,0.3); border: 2px solid var(--text-bright); border-radius: 6px; padding: 6px 14px; font-weight: 700; font-size: 16px; min-width: 40px; text-align: center; color: var(--text-bright); }}
    .advice-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .advice-item {{ background: rgba(255,255,255,0.1); border: 2px solid var(--text-bright); border-radius: 8px; padding: 12px; }}
    .advice-label {{ font-size: 12px; font-weight: 700; color: var(--text-bright); text-transform: uppercase; margin-bottom: 6px; }}
    .advice-text {{ font-size: 13px; color: var(--text-light); line-height: 1.5; }}
    .footer {{ text-align: center; margin-top: 20px; font-size: 11px; color: var(--muted); letter-spacing: 0.15em; padding-bottom: 30px; }}
    a {{ color: var(--text-bright); text-decoration: none; font-weight: 700; border-bottom: 2px solid var(--text-bright); }}
    .expandable {{ cursor: pointer; }}
    .expandable-content {{ display: none; font-size: 14px; color: var(--text-light); line-height: 1.7; margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 4px; }}
  </style>
</head>
<body>
<div class="shell">

  <div class="topbar">
    <div>
      <div class="forge-label">🌴 FORGE OS 🌴</div>
      <div class="forge-sub">Morning Brief</div>
    </div>
    <div class="date-block">
      <div class="date-main">{day_name}</div>
      <div style="font-size:11px; color:var(--muted);">{date_str}</div>
      <div class="date-time" id="live-clock">{time_str}</div>
    </div>
  </div>

  <div class="input-banner">
    📊 Update today's HRV + Sleep data → <a href="https://theseanman.github.io/forge-daily-brief/input.html">Open Input Form →</a>
  </div>

  <div class="motd-box">
    <div class="motd-text">"{stoic_quote}"</div>
    <div class="motd-source">— {stoic_source}</div>
  </div>

  <div class="character-quote-box">
    <img class="character-image" src="{char['image']}" alt="{char['name']}" onerror="this.style.display='none'">
    <div>
      <div class="character-quote">"{char['quote']}"</div>
      <div class="character-name">— {char['name']}, {char['show']}</div>
    </div>
  </div>

  <div class="alert-banner">🚨 {mode} {mode_advice}</div>

  <div class="card">
    <div class="card-header"><span class="card-icon">❤️🌴</span><span>Welltory HRV</span></div>
    <div class="stat-row">
      <div class="stat-block"><div class="stat-val">{welltory['stress']}%</div><div class="stat-label">Stress</div><div class="stat-sub">{stress_status}</div></div>
      <div class="stat-block"><div class="stat-val">{welltory['energy']}%</div><div class="stat-label">Energy</div><div class="stat-sub">{energy_status}</div></div>
      <div class="stat-block"><div class="stat-val">{welltory['health']}%</div><div class="stat-label">Health</div><div class="stat-sub">{health_status}</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">😴🌴</span><span>Sleep Report</span></div>
    <div class="stat-row">
      <div class="stat-block"><div class="stat-val">{sleep['score']}%</div><div class="stat-label">Score</div></div>
      <div class="stat-block"><div class="stat-val">{sleep['duration']}</div><div class="stat-label">Duration</div></div>
      <div class="stat-block"><div class="stat-val">{sleep['hr_range']}</div><div class="stat-label">HR Range</div></div>
    </div>
  </div>

  <div class="card" style="background: linear-gradient(135deg, rgba(255,215,0,0.25), rgba(255,140,0,0.15)); border: 3px double var(--text-bright);">
    <div class="card-header"><span class="card-icon">🎯🌴</span><span>Five Paramount Goals</span></div>
    <div class="paramount-goal">
      <div class="paramount-num"><span>1️⃣ PAUSE BEFORE ANSWERING</span>
        <div class="goal-controls">
          <button class="goal-btn" onclick="decrementGoal(0)">−</button>
          <span class="goal-counter" id="goal-0-counter">0</span>
          <button class="goal-btn" onclick="incrementGoal(0)">+</button>
        </div>
      </div>
      Brief pause before any response. Conscious deliberation first.
    </div>
    <div class="paramount-goal">
      <div class="paramount-num"><span>2️⃣ CAL AI BEFORE MEALS</span>
        <div class="goal-controls">
          <button class="goal-btn" onclick="decrementGoal(1)">−</button>
          <span class="goal-counter" id="goal-1-counter">0</span>
          <button class="goal-btn" onclick="incrementGoal(1)">+</button>
        </div>
      </div>
      Log nutrition in Cal AI before eating. Every meal. Non-negotiable.
    </div>
    <div class="paramount-goal">
      <div class="paramount-num"><span>3️⃣ SLOW MOVEMENTS & SPEECH</span>
        <div class="goal-controls">
          <button class="goal-btn" onclick="decrementGoal(2)">−</button>
          <span class="goal-counter" id="goal-2-counter">0</span>
          <button class="goal-btn" onclick="incrementGoal(2)">+</button>
        </div>
      </div>
      Deliberate, slower pace in all physical and verbal communication.
    </div>
    <div class="paramount-goal">
      <div class="paramount-num"><span>4️⃣ OPPORTUNITY SCANNING</span>
        <div class="goal-controls">
          <button class="goal-btn" onclick="decrementGoal(3)">−</button>
          <span class="goal-counter" id="goal-3-counter">0</span>
          <button class="goal-btn" onclick="incrementGoal(3)">+</button>
        </div>
      </div>
      Every setback: "What opportunity does this situation present me with?"
    </div>
    <div class="paramount-goal">
      <div class="paramount-num"><span>5️⃣ NO NARRATIVES</span>
        <div class="goal-controls">
          <button class="goal-btn" onclick="decrementGoal(4)">−</button>
          <span class="goal-counter" id="goal-4-counter">0</span>
          <button class="goal-btn" onclick="incrementGoal(4)">+</button>
        </div>
      </div>
      Shut down internal narratives the moment they begin. Facts only.
    </div>
    <div class="mini-detail" style="margin-top:12px; font-size:12px; color:var(--muted);">💡 Tap +/− to track. Counters reset at midnight.</div>
  </div>

  <div class="card" style="background: linear-gradient(135deg, rgba(100,150,200,0.2), rgba(70,120,170,0.1)); border: 3px solid var(--text-bright);">
    <div class="card-header"><span class="card-icon">🎭🌴</span><span>Identityless Protocol</span></div>
    <div class="mini-card expandable" onclick="toggleSection(this)">
      <div class="mini-title">🌀 Tap to expand</div>
      <div class="expandable-content">
        <strong>GROUNDLESSNESS TOLERANCE:</strong><br>
        • No-Frame Actions: Act without identity narratives. Just do it.<br>
        • "I Don't Know" as Full Stop: Sit in uncertainty 30–60 seconds.<br>
        • "No Story. Just This": Cut narrative, focus on sensory data.<br><br>
        <strong>INTERNAL AUDIENCE REMOVAL:</strong><br>
        • Catching "Camera On": Detect self-observation, label it, don't judge.<br>
        • Shift to Raw Perception: Anchor in ONE sensory channel.<br>
        • Unwitnessed Existence: 2–5 min activities with zero self-reference.
      </div>
    </div>
  </div>

  <div class="card" style="background: linear-gradient(135deg, rgba(150,100,200,0.2), rgba(120,70,170,0.1)); border: 3px solid var(--text-bright);">
    <div class="card-header"><span class="card-icon">⏰🌴</span><span>Future Self Protocol</span></div>
    <div class="mini-card expandable" onclick="toggleSection(this)">
      <div class="mini-title">📋 Tap to expand</div>
      <div class="expandable-content">
        <strong>MORNING:</strong> Posture Reset → Fractal Scan → Identity Merge → EV Selection → Atmospheric Bruiser Lock-In<br><br>
        <strong>MIDDAY:</strong> Re-anchor → SBOS scan → Remove friction → Enforce boundary → Execute micro-win<br><br>
        <strong>EVENING:</strong> What aligned? What violated? What friction needs removal? What system needs upgrading?
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">🌤️🌴</span><span>Richmond Weather</span></div>
    <div class="mini-card"><div class="mini-detail">{weather}</div></div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">📅🌴</span><span>Today — {date_str}</span></div>
    <div class="mini-card"><div class="mini-detail"><pre style="font-size:13px; color:var(--text-light); white-space:pre-wrap; word-wrap:break-word; font-family:-apple-system,sans-serif;">{cal_today}</pre></div></div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">📆🌴</span><span>This Week (Next 7 Days)</span></div>
    <div class="mini-card"><div class="mini-detail"><pre style="font-size:13px; color:var(--text-light); white-space:pre-wrap; word-wrap:break-word; font-family:-apple-system,sans-serif;">{cal_week}</pre></div></div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">🗓️🌴</span><span>This Month (Next 30 Days)</span></div>
    <div class="mini-card expandable" onclick="toggleSection(this)">
      <div class="mini-title">Tap to expand</div>
      <div class="expandable-content"><pre style="font-size:13px; color:var(--text-light); white-space:pre-wrap; word-wrap:break-word; font-family:-apple-system,sans-serif;">{cal_month}</pre></div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">💡🌴</span><span>Quick Actionable Wisdom</span></div>
    <div class="advice-grid">
      <div class="advice-item"><div class="advice-label">🥋 Self-Defense</div><div class="advice-text">Stance is survival. Feet shoulder-width, weight distributed, knees soft. Stability beats speed.</div></div>
      <div class="advice-item"><div class="advice-label">👨‍👧‍👦 Parenting</div><div class="advice-text">Listen more than talk. Your daughters don't need perfect—they need present.</div></div>
      <div class="advice-item"><div class="advice-label">👨 Fatherhood</div><div class="advice-text">Model recovery. Show them that rest and saying "not today" is strength.</div></div>
      <div class="advice-item"><div class="advice-label">🧠 Mindset</div><div class="advice-text">When the narrative starts: "Story activated." Drop it. Three words. Reset.</div></div>
      <div class="advice-item"><div class="advice-label">⏳ Longevity</div><div class="advice-text">3–4L water + electrolytes. Your immune system's operating capital. Log in Cal AI.</div></div>
      <div class="advice-item"><div class="advice-label">⚡ Life Hack</div><div class="advice-text">Batch texts/emails. Check noon and 5 PM only. Attention is finite.</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">🇯🇵🌴</span><span>Japanese Word of the Day</span></div>
    <div class="mini-card">
      <div class="mini-title">今日の言葉: {jlpt_word} — JLPT {jlpt_level}</div>
      <div class="mini-detail">
        {jlpt_meaning}<br>
        {jlpt_example} = "{jlpt_translation}"
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">🎨🌴</span><span>Art & Music</span></div>
    <div class="mini-card">
      <div class="mini-title">🎨 {art_title}</div>
      <div class="mini-detail">
        <a href="{art_url}" target="_blank">Google Arts & Culture →</a>
      </div>
    </div>
    <div class="mini-card">
      <div class="mini-title">🎵 {music_title}</div>
      <div class="mini-detail">
        <a href="{music_spotify}" target="_blank">Spotify →</a> &nbsp;
        <a href="{music_youtube}" target="_blank">YouTube Music →</a>
      </div>
    </div>
  </div>


  <div class="card">
    <div class="card-header"><span class="card-icon">🎸🌴</span><span>Upcoming Metal Shows</span></div>
    <div class="mini-card">
      <div class="mini-title">🎸 JUNE 14 · Napalm Death + Primitive Man</div>
      <div class="mini-detail">The Pearl, Vancouver · Death metal legends</div>
    </div>
    <div class="mini-card">
      <div class="mini-title">🎸 JUNE 25 · Anvil + Midnite Hellion</div>
      <div class="mini-detail">El Corazon, Seattle</div>
    </div>
    <div class="mini-card">
      <div class="mini-title">🎸 JUNE 27 · Anvil + Midnite Hellion</div>
      <div class="mini-detail">Astoria, Vancouver</div>
    </div>
    <div class="mini-card">
      <div class="mini-title">🎸 JULY 8 · Jinjer + Entheos + Crystal Lake</div>
      <div class="mini-detail">Commodore Ballroom, Vancouver</div>
    </div>
  </div>

  <div class="footer">🌴 FORGE OS · {date_str.upper()} · {time_str} · theseanman.github.io/forge-daily-brief</div>

</div>

<script>
var counts = [0,0,0,0,0];
function loadCounts() {{
  var today = new Date().toDateString();
  try {{
    if (localStorage.getItem('forge-date') === today) {{
      for (var i = 0; i < 5; i++) {{
        var v = localStorage.getItem('g' + i);
        if (v) counts[i] = parseInt(v);
      }}
    }} else {{
      for (var i = 0; i < 5; i++) localStorage.removeItem('g' + i);
      localStorage.setItem('forge-date', today);
    }}
  }} catch(e) {{}}
  for (var i = 0; i < 5; i++) {{
    var el = document.getElementById('goal-' + i + '-counter');
    if (el) el.textContent = counts[i];
  }}
}}
function incrementGoal(i) {{
  counts[i]++;
  try {{ localStorage.setItem('g' + i, counts[i]); }} catch(e) {{}}
  document.getElementById('goal-' + i + '-counter').textContent = counts[i];
}}
function decrementGoal(i) {{
  if (counts[i] > 0) counts[i]--;
  try {{ localStorage.setItem('g' + i, counts[i]); }} catch(e) {{}}
  document.getElementById('goal-' + i + '-counter').textContent = counts[i];
}}
function toggleSection(el) {{
  var c = el.querySelector('.expandable-content');
  if (c) c.style.display = c.style.display === 'block' ? 'none' : 'block';
}}
function tick() {{
  var el = document.getElementById('live-clock');
  if (el) {{
    var now = new Date();
    el.textContent = now.toLocaleTimeString('en-US', {{hour:'2-digit',minute:'2-digit'}});
  }}
}}
window.FORGE_CALENDAR = {cal_json};
window.onload = function() {{ loadCounts(); setInterval(tick, 1000); }};
</script>
</body>
</html>"""
    return html

def main():
    print("🌴 FORGE OS GitHub Actions Brief Generator")
    
    user_data = load_user_data()
    welltory = user_data.get("welltory", {"stress": 50, "energy": 50, "health": 50})
    sleep = user_data.get("sleep", {"score": 85, "duration": "7h 0m", "hr_range": "50–70"})
    
    print(f"✓ Loaded user data: Stress {welltory['stress']}%, Energy {welltory['energy']}%, Health {welltory['health']}%")
    
    weather = get_weather()
    calendar = get_calendar_events()
    
    # Push 7-day calendar to JSONBin for Evening Debrief
    if calendar.get("week_structured"):
        push_calendar_to_jsonbin(calendar["week_structured"])
    
    html = generate_html(welltory, sleep, weather, calendar, calendar.get("week_structured", []))
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ index.html generated successfully")

if __name__ == "__main__":
    main()
