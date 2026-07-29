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
import zoneinfo

# ── Timezone fix: all datetime.now() calls use Pacific time ──────────────────
PACIFIC = zoneinfo.ZoneInfo("America/Vancouver")

def now_pt():
    """Return current datetime in Pacific time."""
    return _dt.datetime.now(PACIFIC)

def today_pt():
    """Return current date in Pacific time."""
    return _dt.datetime.now(PACIFIC).date()


EPOCH = _dt.date(2026, 1, 1)


def _day_count():
    """Days since a fixed epoch. Advances continuously instead of resetting each Jan 1."""
    return (_dt.date.today() - EPOCH).days


def get_daily_index(list_len):
    if not list_len:
        return 0
    return _day_count() % list_len


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT POOLS — loaded from content/*.json so they can be edited without
# touching this file. A malformed file must never take the brief down: it falls
# back to a minimal built-in set and records a loud error for the banner.
# ══════════════════════════════════════════════════════════════════════════════
CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
POOL_ERRORS = []

_FALLBACKS = {
    "japanese": [{"word": "\u7cbe\u9032 (Shoujin)", "level": "N1",
                  "meaning": "Devoted, disciplined application.",
                  "example": "\u65e5\u3005\u7cbe\u9032\u3092\u91cd\u306d\u308b",
                  "translation": "To apply oneself diligently, day after day."}],
    "colonel": [{"line": "A plan doesn\u2019t come together because it\u2019s clever. "
                         "It comes together because somebody kept showing up.", "tag": "Execution"}],
    "models": [{"name": "Inversion", "origin": "Carl Jacobi",
                "what": "Ask what would guarantee failure, then avoid that.",
                "examples": [], "focus": "Name the three fastest ways to ruin today \u2014 and don\u2019t do those."}],
    "strategy": [{"name": "Distribution Beats Production", "category": "Leverage",
                  "what": "Getting the work to people matters more than making more of it.",
                  "examples": [], "focus": "Name one thing you made this month that nobody saw."}],
}


def load_pool(name):
    """Load content/<name>.json -> list of entries. Never raises."""
    path = os.path.join(CONTENT_DIR, name + ".json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        entries = data.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError("no entries array")
        return entries
    except Exception as e:
        msg = f"{name}.json failed to load: {type(e).__name__}: {e}"
        print("POOL ERROR: " + msg)
        POOL_ERRORS.append(msg)
        return _FALLBACKS.get(name, [{}])


def load_facts():
    """Load content/sports_facts.json. Never raises."""
    path = os.path.join(CONTENT_DIR, "sports_facts.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        msg = f"sports_facts.json failed to load: {type(e).__name__}: {e}"
        print("POOL ERROR: " + msg)
        POOL_ERRORS.append(msg)
        return {"_meta": {"warn_days": 21, "stale_days": 45}, "teams": [], "fighters": []}


def fact_age_badge(verified_on, meta):
    """Return (days_old, css_class, label) for a verified_on date string."""
    try:
        d = _dt.datetime.strptime(verified_on, "%Y-%m-%d").date()
    except Exception:
        return (9999, "fact-stale", "unverified")
    age = (_dt.date.today() - d).days
    warn = meta.get("warn_days", 21)
    stale = meta.get("stale_days", 45)
    if age >= stale:
        return (age, "fact-stale", f"{age}d old \u2014 CHECK THIS")
    if age >= warn:
        return (age, "fact-warn", f"{age}d old")
    return (age, "fact-fresh", f"{age}d")


JLPT_WORDS = load_pool("japanese")



COLONEL_LINES = load_pool("colonel")
MENTAL_MODELS = load_pool("models")
STRATEGIES = load_pool("strategy")
SPORTS_FACTS = load_facts()


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
            "sleep": {"score": 85, "duration": "7h 0m", "hr_range": "50–70"},
            "body_comp": {"weight": None, "body_fat": None, "muscle_mass": None, "bmi": None, "visceral_fat": None}
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


CALENDAR_ERRORS = []

SUBSCRIBED_ICS_URLS = [
    ("Physio Steveston", "https://physiosteveston.janeapp.com/ical/kl9n5cYxfi2zzYub3Mw7/appointments.ics"),
    ("Doctor", "https://p147-caldav.icloud.com/published/2/MjA4NzgzMDU5MjA4NzgzMKp8OzvkKcO0VBjXnAPWsZ3_SOkZblhgb63Ap9fXTp8mTVpP7f2Zhhi6oPiqkT8_u9GgW7cNm2tkWygB88NaKao"),
    ("UFC Events", "https://raw.githubusercontent.com/clarencechaan/ufc-cal/ics/UFC.ics"),
    ("Austria Vancouver", "https://austriavancouverclub.ca/?post_type=tribe_events&ical=1&eventDisplay=list"),
    ("Ringette", "https://api3.rampinteractive.com/teamapp/Calendar/GetCalendar/America-Vancouver/3178874,3178962/0"),
    ("Doctor 2", "https://p147-caldav.icloud.com/published/2/MjA4NzgzMDU5MjA4NzgzMKp8OzvkKcO0VBjXnAPWsZ3QfUpZTMmqDhS1RS2Q4Unql2HwH_zVrF_S7pswdX5EkPscxgI5CxoYg1ulgXc7ME0"),
    ("Richmond Blundell Physio", "https://richmondblundellphysio.janeapp.com/ical/yphai5OwEVtmTOppT6Fx/appointments.ics"),
    ("ONE Championship", "https://calendar.onefc.com/ONE-Championship-events.ics"),
    ("Brighouse School", "https://brighouse.sd38.bc.ca/calendar-feed.ics"),
]

def fetch_ics_events(start_dt, end_dt):
    import urllib.request
    import re as _re
    import zoneinfo as _zi
    from datetime import datetime, timezone as _tz
    PT = _zi.ZoneInfo("America/Vancouver")
    all_events = []

    for feed_name, url in SUBSCRIBED_ICS_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read().decode("utf-8", errors="ignore")

            blocks = raw.split("BEGIN:VEVENT")
            for block in blocks[1:]:
                try:
                    summary = feed_name
                    for line in block.splitlines():
                        if line.startswith("SUMMARY:"):
                            summary = line[8:].strip()
                            break

                    dtstart_raw = ""
                    for line in block.splitlines():
                        if line.startswith("DTSTART"):
                            dtstart_raw = line.split(":", 1)[-1].strip()
                            break

                    if not dtstart_raw:
                        continue

                    if _re.match(r"^\d{8}$", dtstart_raw):
                        dt = datetime.strptime(dtstart_raw, "%Y%m%d").date()
                        dt_sort = datetime.combine(dt, datetime.min.time()).replace(tzinfo=PT)
                        label = f"{summary} -- {dt.strftime('%a %b %d')} (All Day) [{feed_name}]"
                    elif dtstart_raw.endswith("Z"):
                        dt_sort = datetime.strptime(dtstart_raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=_tz.utc).astimezone(PT)
                        label = f"{summary} @ {dt_sort.strftime('%a %b %d, %I:%M %p')} [{feed_name}]"
                    elif "T" in dtstart_raw and len(dtstart_raw) >= 15:
                        dt_sort = datetime.strptime(dtstart_raw[:15], "%Y%m%dT%H%M%S").replace(tzinfo=PT)
                        label = f"{summary} @ {dt_sort.strftime('%a %b %d, %I:%M %p')} [{feed_name}]"
                    else:
                        continue

                    if start_dt <= dt_sort < end_dt:
                        all_events.append((dt_sort.isoformat(), label))

                except Exception:
                    continue

        except Exception as e:
            print(f"ICS fetch failed ({feed_name}): {e}")
            continue

    all_events.sort(key=lambda x: x[0])
    return [e[1] for e in all_events]

def fetch_ics_structured(start_dt, end_dt):
    """Same feeds as fetch_ics_events, but returns {date,time,title} dicts so
    subscribed calendars reach data.json and the day planner, not just the
    text lists on the brief."""
    import urllib.request
    import re as _re
    import zoneinfo as _zi
    from datetime import datetime, timezone as _tz
    PT = _zi.ZoneInfo("America/Vancouver")
    out = []

    for feed_name, url in SUBSCRIBED_ICS_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read().decode("utf-8", errors="ignore")
        except Exception as e:
            CALENDAR_ERRORS.append(f"{feed_name}: {type(e).__name__} {e}")
            print(f"ICS fetch failed ({feed_name}): {e}")
            continue

        # unfold RFC5545 line continuations before parsing
        raw = raw.replace("\r\n", "\n").replace("\n ", "").replace("\n\t", "")
        found = 0
        for block in raw.split("BEGIN:VEVENT")[1:]:
            try:
                summary = feed_name
                dtstart_raw = ""
                for line in block.splitlines():
                    if line.startswith("SUMMARY") and not summary_set(summary, feed_name):
                        pass
                    if line.startswith("SUMMARY"):
                        summary = line.split(":", 1)[-1].strip()
                    elif line.startswith("DTSTART") and not dtstart_raw:
                        dtstart_raw = line.split(":", 1)[-1].strip()
                if not dtstart_raw:
                    continue

                if _re.match(r"^\d{8}$", dtstart_raw):
                    d = datetime.strptime(dtstart_raw, "%Y%m%d").date()
                    dt_sort = datetime.combine(d, datetime.min.time()).replace(tzinfo=PT)
                    time_label = "All day"
                elif dtstart_raw.endswith("Z"):
                    dt_sort = datetime.strptime(dtstart_raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=_tz.utc).astimezone(PT)
                    time_label = dt_sort.strftime("%I:%M %p")
                elif "T" in dtstart_raw and len(dtstart_raw) >= 15:
                    dt_sort = datetime.strptime(dtstart_raw[:15], "%Y%m%dT%H%M%S").replace(tzinfo=PT)
                    time_label = dt_sort.strftime("%I:%M %p")
                else:
                    continue

                if start_dt <= dt_sort < end_dt:
                    out.append({
                        "date": dt_sort.strftime("%a %b %d"),
                        "time": time_label,
                        "title": summary,
                        "_sort": dt_sort.isoformat(),
                    })
                    found += 1
            except Exception:
                continue
        print(f"  ICS {feed_name}: {found} events in range")

    return out


def summary_set(current, feed_name):
    return current != feed_name


def dedupe_events(events):
    """Same event arriving from both iCloud and a subscribed feed should appear
    once. Match on date + time + a normalised title."""
    seen = set()
    out = []
    for e in events:
        title = (e.get("title") or "").strip().lower()
        title = " ".join(title.split())
        key = (e.get("date"), e.get("time"), title)
        if key in seen:
            continue
        # also treat one title being a prefix of another as the same event
        dup = False
        for d0, t0, ti0 in seen:
            if d0 == e.get("date") and t0 == e.get("time") and title and ti0:
                if title.startswith(ti0) or ti0.startswith(title):
                    dup = True
                    break
        if dup:
            continue
        seen.add(key)
        out.append(e)
    return out


def get_calendar_events():
    """Fetch today, week, and 7-day structured events from iCloud via CalDAV."""
    if not ICLOUD_PASSWORD:
        CALENDAR_ERRORS.append("iCloud CalDAV: ICLOUD_PASSWORD secret is not set")
        return {"today": "\u26A0 Calendar unavailable \u2014 ICLOUD_PASSWORD is not set", "week": "", "month": "", "week_structured": []}
    
    try:
        client = caldav.DAVClient(
            url="https://caldav.icloud.com",
            username=ICLOUD_EMAIL,
            password=ICLOUD_PASSWORD
        )
        
        principal = client.principal()
        calendars = principal.calendars()
        
        today = today_pt()  # FIX: use Pacific time, not UTC
        tz = timezone.utc

        # Use Pacific timezone for today boundaries so evening PT events aren't cut off
        pt = zoneinfo.ZoneInfo("America/Vancouver")
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=pt)
        today_end = datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(tzinfo=pt)
        week_end = datetime.combine(today + timedelta(days=7), datetime.min.time()).replace(tzinfo=tz)
        month_end = datetime.combine(today + timedelta(days=30), datetime.min.time()).replace(tzinfo=tz)

        today_events = fetch_events_for_range(calendars, today_start, today_end)
        week_events = fetch_events_for_range(calendars, today_start, week_end)
        month_events = fetch_events_for_range(calendars, today_start, month_end)
        week_structured = fetch_events_structured(calendars, today_start, week_end)

        # Fetch subscribed ICS calendars and merge
        ics_today = fetch_ics_events(today_start, today_end)
        ics_week = fetch_ics_events(today_start, week_end)
        ics_month = fetch_ics_events(today_start, month_end)
        today_events = today_events + ics_today
        week_events = week_events + ics_week
        month_events = month_events + ics_month

        # THE FIX: subscribed feeds must reach data.json and the day planner too,
        # not just the text lists above.
        ics_structured = fetch_ics_structured(today_start, week_end)
        before = len(week_structured)
        week_structured = week_structured + ics_structured
        week_structured = dedupe_events(week_structured)
        week_structured.sort(key=lambda e: (e.get("_sort") or ""))
        for e in week_structured:
            e.pop("_sort", None)
        print(f"\u2713 Structured calendar: {before} iCloud + {len(ics_structured)} subscribed "
              f"\u2192 {len(week_structured)} after dedupe")

        print(f"✓ Today: {len(today_events)} | Week: {len(week_events)} | Month: {len(month_events)} events (ICS: {len(ics_today)} today)")

        return {
            "today": "\n".join(today_events) if today_events else "No events today.",
            "week": "\n".join(week_events) if week_events else "No events this week.",
            "month": "\n".join(month_events) if month_events else "No events this month.",
            "week_structured": week_structured
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        msg = f"{type(e).__name__}: {e}"
        print(f"Calendar fetch failed: {msg}")
        CALENDAR_ERRORS.append(f"iCloud CalDAV: {msg}")
        return {"today": f"\u26A0 Calendar unavailable \u2014 {msg}", "week": "", "month": "", "week_structured": []}

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

def get_colonel_line(day_of_week=None):
    return COLONEL_LINES[get_daily_index(len(COLONEL_LINES))]


def get_mental_model():
    return MENTAL_MODELS[get_daily_index(len(MENTAL_MODELS))]


def get_strategy():
    # offset so the model and the strategy are not always the same pair
    idx = (_day_count() + 7) % len(STRATEGIES) if STRATEGIES else 0
    return STRATEGIES[idx]



WISDOM_POOLS = {
    "self_defense": [
        "Stance is survival. Feet shoulder-width, weight distributed, knees soft. Stability beats speed.",
        "Distance is your friend. Create space before creating options. Never let aggression close the gap for free.",
        "Don't block — redirect. Use their force, not yours. The smaller person wins on efficiency.",
        "Eyes on the chest, not the hands. The torso telegraphs before the limbs move.",
        "Strike through the target, not at it. Commitment is the difference between a bruise and a stop.",
        "Verbal de-escalation is a weapon. Most fights are won before the first physical contact.",
        "Your strongest weapon is your awareness. Danger avoided beats danger handled.",
        "Train the thing you're worst at. Competence in weakness becomes your surprise.",
        "After contact: disengage, create distance, assess. Don't stay in the pocket.",
        "Breathing controls panic. Exhale on exertion. Three slow breaths resets the adrenal response.",
        "Wrist grabs are releases, not fights. Rotate toward their thumb — it's always the weakest link.",
        "Low kicks are underrated. Knees and shins don't train the way hands do. Target them.",
        "Your loudest tool is your voice. It startles, commands space, and invites witnesses.",
        "Control the head, control the body. Every restraint and escape starts there.",
        "Train slow to perform fast. Muscle memory built at speed is sloppy muscle memory.",
        "Never turn your back. Exit backward or sideways. Disengagement is not defeat.",
        "The goal isn't to win — it's to get home. Everything is in service of that.",
        "Choke defences first. It's the most likely attack and the most panicked response.",
        "Soft targets: eyes, throat, knees, instep. You don't need power — you need precision.",
        "Rest stance looks relaxed. Hands slightly raised, weight on back foot. Ready without telegraphing.",
    ],
    "parenting": [
        "Listen more than talk. Your daughters don't need perfect — they need present.",
        "They remember how you handled your mistakes more than the mistakes themselves.",
        "Say their name before you say the thing. It opens the channel.",
        "Your reaction to their failure sets their relationship with failure for life.",
        "Get on their level physically when talking. Eye contact changes everything.",
        "Don't rescue them from discomfort — sit with them in it. That's the skill.",
        "Narrate your thinking out loud. They learn how to think by watching you do it.",
        "Repair fast. A 10-minute rupture with a 2-minute repair is a net positive.",
        "Ask what happened before you ask why. Why triggers defensiveness. What opens it.",
        "Celebrate the effort, not the result. Outcome praise builds fragility.",
        "Your calm is their nervous system regulator. Co-regulation before self-regulation.",
        "Show them you change your mind when given good evidence. That's the most powerful lesson.",
        "Notice the small things. The small things are the big things at their scale.",
        "Don't over-explain. Say the thing once, clearly. Repetition teaches them to tune you out.",
        "Create rituals. Predictability is safety. Safety is where growth happens.",
        "Let them be bored. Boredom is the birthplace of creativity and self-reliance.",
        "Apologize to them like you'd apologize to an adult. They feel the difference.",
        "What you model about stress is what they'll carry into their own pressure moments.",
        "Let them overhear you say something good about them to someone else.",
        "The relationship is the discipline. Strong bond, minimal friction. Invest accordingly.",
    ],
    "fatherhood": [
        "Model recovery. Show them that rest and saying 'not today' is strength.",
        "They don't need a hero — they need a man who keeps showing up.",
        "Your presence at the ordinary moments is the extraordinary gift.",
        "Teach them to lose without collapse. Play games you occasionally let them win — and some you don't.",
        "Work ethic is caught, not taught. Let them see you grind and rest in healthy proportion.",
        "Name your emotions out loud. 'I'm frustrated right now' is parenting gold.",
        "A father who reads makes readers. It's not what you say about books — it's what you do with them.",
        "Their relationship with men starts with you. Build it consciously.",
        "Ask them questions you don't know the answer to. Show them curiosity isn't weakness.",
        "The car is a sacred space. Side-by-side conversation opens things that face-to-face won't.",
        "Know their world well enough to ask a real question. Not 'how was school' — something specific.",
        "Laughter is load-bearing. A family that laughs together has a reserve for the hard times.",
        "Let them see you fail and try again. Perseverance modelled is perseverance transmitted.",
        "Don't outsource your hard conversations to their mother. Own your half of the relationship.",
        "Show up to the things that matter to them, not just the things that matter to you.",
        "Physical affection has no expiry date. Keep it going through adolescence.",
        "What you spend Saturday morning doing is the answer to 'what does Dad value'.",
        "Teach them money is a tool, not a score. How you talk about it shapes their whole relationship.",
        "Your daughters are watching how you treat women. The lesson is always live.",
        "Be the person they run toward with good news. That means being safe with the bad news.",
    ],
    "mindset": [
        "When the narrative starts: 'Story activated.' Drop it. Three words. Reset.",
        "Discomfort is data. Ask what it's signalling before reacting to it.",
        "The gap between stimulus and response is where your character lives. Widen it.",
        "You don't rise to the level of your goals — you fall to the level of your systems.",
        "Confidence is a post-action state, not a pre-condition. Do first. Feel it after.",
        "Comparison is a rigged game. You're seeing their highlight reel against your blooper reel.",
        "Identity drives behaviour. Ask: 'What would the Quiet Strategist do here?'",
        "Most anxiety is future-projection. Bring it back to: what is actually true right now?",
        "The hard conversation you're avoiding is the ceiling on your progress.",
        "Inaction has a cost. Weigh the risk of doing against the certainty of staying stuck.",
        "Your beliefs about your limits are more limiting than your actual limits.",
        "Boredom is the body asking for a harder problem. Listen to it.",
        "Emotion as information, not instruction. Feel it. Don't obey it.",
        "What you rehearse in your mind, you perform under pressure. Choose your rehearsals.",
        "Done is the engine of done better. Perfectionism is procrastination with a story.",
        "The Operator executes. The Architect designs. Don't confuse which role the moment needs.",
        "Resistance is the compass. The thing you're avoiding is usually the thing.",
        "Slow is smooth. Smooth is fast. Urgency produces sloppiness. Pace produces leverage.",
        "You can't think your way out of something you behaved your way into. Act first.",
        "No story. Just this. Sensory data. Present moment. The rest is fiction.",
    ],
    "longevity": [
        "3–4L water + electrolytes. Your immune system's operating capital. Log in Cal AI.",
        "Sleep is the master variable. Everything else is noise when sleep is broken.",
        "Zone 2 cardio: nasal breathing, conversational pace, 45–60 min. Non-negotiable base.",
        "Protein first at every meal. 0.7–1g per pound of bodyweight. Everything else fills in around it.",
        "Sunlight within 30 min of waking. Sets your cortisol curve and sleep pressure for the day.",
        "HRV is your readiness report. When it drops, recovery — not grinding — is the right call.",
        "Mobility is the tax on strength. Five minutes daily beats 60 minutes weekly.",
        "The posterior tibial needs eccentric loading, not rest. Single-leg calf raises on a step.",
        "Grip strength at 40+ is a longevity biomarker. Dead hangs, farmer carries, every week.",
        "Time-restricted eating: 8–10 hour window. Your metabolic machinery needs the off-cycle.",
        "Fibre is the unloved hero. 30–40g daily feeds the microbiome that regulates everything.",
        "Cold exposure: face only in cold water for 30 seconds resets the vagal tone fast.",
        "VO2 max is your life expectancy predictor. Improve it one hard cardio session per week.",
        "Social connection is a health metric. Isolation has the same mortality risk as smoking.",
        "Inflammatory foods age you visibly. Seed oils, ultra-processed, high sugar — identify and reduce.",
        "Posture is a longevity habit. Forward head = compressed nerves, accelerated disc wear.",
        "Alcohol math: even moderate use disrupts deep sleep architecture. Track the trade-off.",
        "Leg strength in your 50s and 60s is built in your 40s. Keep the legs strong now.",
        "Stress without recovery is the mechanism of accelerated aging. Recovery is not optional.",
        "Annual bloodwork: fasting glucose, HbA1c, testosterone, Vitamin D, CRP. Know your numbers.",
    ],
    "life_hack": [
        "Batch texts/emails. Check noon and 5 PM only. Attention is finite.",
        "Decision fatigue is real. Automate the low-stakes choices so you're sharp for the high ones.",
        "Two-minute rule: if it takes less than two minutes, do it now. The list is killing you.",
        "Write the next action, not the project. 'Finish report' stalls. 'Open file, write intro' moves.",
        "The phone in another room doubles deep work quality. Proximity is temptation.",
        "Weekly review on Sunday evening. 20 minutes to plan clears the week's mental overhead.",
        "Never leave a room empty-handed. Always be optimising the environment.",
        "Friction removal is leverage. Make the good behaviour the path of least resistance.",
        "Preparation is a multiplier. 10 minutes of prep the night before saves 40 minutes of morning chaos.",
        "Name the mood before acting on it. 'I'm in a reactive state' changes what you do next.",
        "High-value work in the first 90 minutes. That's your peak cortisol window. Don't waste it on email.",
        "One hard thing before the thing you actually want to do. Momentum is sequential.",
        "Capture everything externally. Your brain is for processing, not storage.",
        "The calendar is a commitment device. If it's not scheduled, it's a wish.",
        "Reduce optionality on the things that don't matter. Save choices for the things that do.",
        "Say no to the good so you can say yes to the great. The word 'no' is a time machine.",
        "Default to async. Meetings are a last resort, not a first response.",
        "End each work block with a note of where you stopped and the next step. Re-entry costs you 15 min without it.",
        "Temptation bundling: pair the thing you avoid with the thing you enjoy. Podcast only during walks.",
        "Review your five paramount goals before bed. Primes the subconscious for the next day.",
    ],
}

def get_wisdom(day_of_year):
    """Return one tip per category, rotating by day of year."""
    result = {}
    for key, pool in WISDOM_POOLS.items():
        result[key] = pool[day_of_year % len(pool)]
    return result


# ============================================================
# THREE-MODE PHILOSOPHY TRIAD
# Warrior = 3 fixed anchors (first person), one highlighted per day (rotating)
# Identityless = rotating pool of 20 (bare/egoless — intentionally NO first person)
# Strictness = rotating pool of 20 (first person)
# ============================================================

WARRIOR_ANCHORS = [
    "I hold fast. The discomfort doesn't decide — I do. I anchor to who I am, not to how I feel.",
    "Hard is the point. Where will I show my strength today?",
    "I stand tall. Shoulders back. Breath slow. The posture is my decision.",
]

IDENTITYLESS_POOL = [
    "No story. Just this. Drop the narrator — sensory data only, what is actually in front of you.",
    "Camera off. Catch the self-observation, name it, return to raw perception.",
    "Sit in 'I don't know' for sixty seconds without resolving it. Groundlessness is not danger.",
    "Act with no frame. No 'as a man who…', no 'someone like me.' Just the next clean action.",
    "Two minutes of unwitnessed existence: zero self-reference, only sensation and motion.",
    "There is no audience. The watching self is a fiction — let the act happen without a witness.",
    "Drop the verdict. Things are not good or bad right now. They simply are.",
    "Notice the urge to narrate the moment. Don't. Let it pass unspoken.",
    "Whose problem is this? Nobody's. It is just a condition to be handled. Handle it.",
    "Release the outcome. The doing is complete in itself. The result is not yours to hold.",
    "No identity to defend here. Nothing to protect means nothing to fear.",
    "Become the task, not the one doing the task. Disappear into the action.",
    "Strip the adjective. Not 'a hard run' — a run. Not 'an annoying email' — an email.",
    "Let the thought arrive and leave without claiming it. You are not your thinking.",
    "No past self to honor, no future self to impress. Only this breath, this motion.",
    "When praised or criticized, neither lands — there is no fixed self for it to stick to.",
    "Quiet the inner commentary. The silence underneath it was always there.",
    "Stop managing the impression. There is no one to manage it for.",
    "Pure perception: the cold, the weight, the breath. The labels are optional. Drop them.",
    "Nothing to become. Nothing to prove. Just the next thing, done plainly.",
]

STRICTNESS_POOL = [
    "I execute the block regardless of state. Mood does not get a veto.",
    "I decide cleanly and act within five seconds of clarity. Deliberation past that is avoidance.",
    "Minimum viable day still counts: one Forge task, one training block, one presence ritual.",
    "I never miss two days running. The 3-day rule is the floor, not the goal.",
    "I move slowly, speak precisely, enforce the boundary instantly. No leakage.",
    "I do the thing I scheduled, at the time I scheduled it. The calendar is a contract.",
    "I remove one friction point before I start. Make the right action the easy one.",
    "I finish what I open. No half-closed loops carried into tomorrow.",
    "I start before I feel ready. Readiness is a story; the start is the only proof.",
    "One hard thing first, every day, before the thing I want. Momentum is sequential.",
    "I keep my word to myself the way I'd keep it to someone I respect.",
    "I do not negotiate with the snooze, the scroll, or the 'just five minutes.' The answer is no.",
    "I protect the first ninety minutes. Peak window, hardest task, no email.",
    "I show up at the same time regardless of how I slept or what happened yesterday.",
    "I log the nutrition, the training, the metric — even when it's inconvenient. Especially then.",
    "I enforce the boundary in the moment, not after rehearsing it ten times in my head.",
    "I do the rep that nobody will see. Discipline is what holds when no one is watching.",
    "I close the day with the next step written down. Re-entry tomorrow costs nothing then.",
    "I cut the optional to protect the essential. Saying no is how I say yes to what matters.",
    "I operate on the plan, not the impulse. The plan was made by the clearer version of me.",
]


def get_triad(day_of_year):
    """Daily three-mode triad. Warrior: all 3 anchors, one highlighted (rotating).
    Identityless + Strictness: one rotating line each."""
    highlight_idx = day_of_year % len(WARRIOR_ANCHORS)
    warrior = [{"text": l, "highlight": (i == highlight_idx)}
               for i, l in enumerate(WARRIOR_ANCHORS)]
    return {
        "warrior": warrior,
        "identityless": IDENTITYLESS_POOL[day_of_year % len(IDENTITYLESS_POOL)],
        "strictness": STRICTNESS_POOL[day_of_year % len(STRICTNESS_POOL)],
    }


def render_triad(day_of_year):
    """Build the SUNFURY-styled triad card HTML for the given day."""
    triad = get_triad(day_of_year)
    warrior_lines = ""
    for w in triad["warrior"]:
        cls = "triad-anchor triad-anchor-hi" if w["highlight"] else "triad-anchor"
        warrior_lines += f'<div class="{cls}">{w["text"]}</div>'
    return f'''  <div class="card">
    <div class="card-header"><span class="card-icon">&#x2694;&#xFE0F;&#x1F334;</span><span>Three Modes — Daily Triad</span></div>
    <div class="triad-mode">
      <div class="triad-label">&#x2694;&#xFE0F; Warrior — Hold the Line</div>
      {warrior_lines}
    </div>
    <div class="triad-mode">
      <div class="triad-label">&#x1F3AD; Identityless — Drop the Self</div>
      <div class="triad-text">{triad["identityless"]}</div>
    </div>
    <div class="triad-mode">
      <div class="triad-label">&#x2696;&#xFE0F; Strictness — Execute</div>
      <div class="triad-text">{triad["strictness"]}</div>
    </div>
  </div>'''


def render_summer_protocol():
    """Build the Summer Protocol reference card — 7 drills, always visible.
    Pause/Trigger Breath, Opportunity Question and Slow Down were merged into
    the Five Paramount Goals card (July 24, 2026) where they carry tap counters."""
    drills = [
        ("\U0001F50D Camera Off",
         "In every conversation, find one genuine thing about the other person you didn\u2019t know. That\u2019s your only job.",
         "Cue: every conversation"),
        ("\U0001F9CD Posture Reset",
         "Every time you stand up: shoulders down, chest open, head level. Just the reset.",
         "Cue: every time you stand"),
        ("\U0001F91D I\u2019m Fine Either Way",
         "Before the first tense interaction, say it silently and mean it. You\u2019d like it to go well; you don\u2019t need it to.",
         "Cue: before tension \u00b7 binary: yes/no"),
        ("\U0001F4AC The Second Question",
         "When someone answers you, don\u2019t pivot to yourself. Ask one follow-up that goes deeper into what they said.",
         "Cue: every conversation"),
        ("\U0001F6D1 Boundary Rep",
         "State one preference or decline one small thing. No qualifier, no apology. Let the silence sit.",
         "Cue: once daily \u00b7 binary: yes/no"),
        ("\u2694\uFE0F Warrior Promise",
         "Name the one hard thing you\u2019re avoiding. Do it first, before the easy stuff.",
         "Cue: morning \u00b7 binary: yes/no"),
        ("\u2764\uFE0F Warmth Rep",
         "Give one specific, sincere appreciation to someone. Not \u2018you\u2019re great\u2019 \u2014 something true and particular.",
         "Cue: once daily"),
    ]
    rows = ""
    for name, instruction, trigger in drills:
        rows += f'''<div class="proto-drill">
      <div class="proto-name">{name}</div>
      <div class="proto-inst">{instruction}</div>
      <div class="proto-trigger">{trigger}</div>
    </div>\n    '''
    return f'''  <div class="card">
    <div class="card-header"><span class="card-icon">&#x1F525;&#x1F334;</span><span>Summer Protocol \u2014 Today\u2019s Reps</span></div>
    <div class="proto-intro">Train where it\u2019s easy. Groove the reflex. It shows up when it matters.<br><span style="font-size:11px; opacity:0.75;">Pause, Slow Down and the Opportunity Question now live in the Five Paramount Goals card above, with counters.</span></div>
    {rows}</div>'''


def get_sports_updates():
    """Comprehensive sports intel: API for MLB/NHL/NFL, hardcoded for CFL/Soccer/Rugby/NLL."""
    import urllib.request, json
    from datetime import date, datetime, timedelta
    import zoneinfo
    PT = zoneinfo.ZoneInfo("America/Vancouver")

    def espn_get(url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print(f"ESPN fetch failed ({url}): {e}")
            return None

    def extract_score(raw):
        if raw is None: return "?"
        if isinstance(raw, dict): return str(raw.get("displayValue", raw.get("value", "?")))
        return str(raw)

    def to_pt(dt_str):
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.astimezone(PT)

    def parse_game(date_str, time_str):
        """Parse a game date/time string into a date object. date_str: 'YYYY-MM-DD', time_str: 'H:MM PM PT'"""
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p PT").replace(tzinfo=PT)
        except:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=PT)
            except:
                return None

    today = datetime.now(PT).date()
    lines = []

    # ══════════════════════════════════════════════════════════════════════════
    # BC LIONS 2026 SCHEDULE (hardcoded — ESPN CFL API broken for 2026)
    # All times PT. Source: CFL.ca / sportshistori.com
    # ══════════════════════════════════════════════════════════════════════════
    BC_LIONS = [
        # (date, time_pt, home_away, opponent, location)
        ("2026-06-13", "2:00 PM", "@", "Saskatchewan Roughriders", "Mosaic Stadium"),
        ("2026-06-19", "2:30 PM", "@", "Hamilton Tiger-Cats", "Tim Hortons Field"),
        ("2026-06-27", "4:00 PM", "vs", "Calgary Stampeders", "Apple Bowl, Kelowna"),
        ("2026-07-04", "4:00 PM", "vs", "Edmonton Elks", "Apple Bowl, Kelowna"),
        ("2026-07-25", "4:00 PM", "vs", "Toronto Argonauts", "BC Place, Vancouver"),
        ("2026-08-08", "4:00 PM", "vs", "Hamilton Tiger-Cats", "BC Place, Vancouver"),
        ("2026-08-23", "4:00 PM", "vs", "Saskatchewan Roughriders", "BC Place, Vancouver"),
        ("2026-09-12", "4:00 PM", "vs", "Montreal Alouettes", "BC Place, Vancouver"),
        ("2026-09-25", "4:00 PM", "vs", "Saskatchewan Roughriders", "BC Place, Vancouver"),
        ("2026-10-09", "4:00 PM", "vs", "Ottawa Redblacks", "BC Place, Vancouver"),
        ("2026-10-23", "4:00 PM", "vs", "Winnipeg Blue Bombers", "BC Place, Vancouver"),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # ALL CFL WEEK 2 GAMES TODAY (hardcoded — ESPN API broken)
    # Source: CFL.ca Week 2 schedule
    # ══════════════════════════════════════════════════════════════════════════
    CFL_SCHEDULE = [
        # (date, time_pt, away, home)
        ("2026-06-04", "4:00 PM", "Montreal Alouettes", "Hamilton Tiger-Cats"),
        ("2026-06-05", "4:30 PM", "Winnipeg Blue Bombers", "Calgary Stampeders"),
        ("2026-06-06", "4:00 PM", "Ottawa Redblacks", "Edmonton Elks"),
        ("2026-06-11", "5:30 PM", "Hamilton Tiger-Cats", "Winnipeg Blue Bombers"),
        ("2026-06-12", "2:00 PM", "Toronto Argonauts", "Montreal Alouettes"),
        ("2026-06-13", "2:00 PM", "BC Lions", "Saskatchewan Roughriders"),
        ("2026-06-19", "2:30 PM", "BC Lions", "Hamilton Tiger-Cats"),
        ("2026-06-19", "4:00 PM", "Ottawa Redblacks", "Toronto Argonauts"),
        ("2026-06-20", "4:00 PM", "Calgary Stampeders", "Edmonton Elks"),
        ("2026-06-20", "5:30 PM", "Saskatchewan Roughriders", "Winnipeg Blue Bombers"),
        ("2026-06-25", "4:00 PM", "Hamilton Tiger-Cats", "Ottawa Redblacks"),
        ("2026-06-26", "2:00 PM", "Montreal Alouettes", "Toronto Argonauts"),
        ("2026-06-27", "4:00 PM", "Calgary Stampeders", "BC Lions"),  # Kelowna
        ("2026-06-27", "5:30 PM", "Edmonton Elks", "Saskatchewan Roughriders"),
        ("2026-07-01", "1:00 PM", "Winnipeg Blue Bombers", "Ottawa Redblacks"),
        ("2026-07-04", "4:00 PM", "Edmonton Elks", "BC Lions"),  # Kelowna
        ("2026-07-04", "5:00 PM", "Saskatchewan Roughriders", "Calgary Stampeders"),
        ("2026-07-10", "4:00 PM", "Toronto Argonauts", "Hamilton Tiger-Cats"),
        ("2026-07-10", "5:30 PM", "Ottawa Redblacks", "Montreal Alouettes"),
        ("2026-07-11", "4:30 PM", "Winnipeg Blue Bombers", "Edmonton Elks"),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # CANADA SOCCER — FIFA WORLD CUP 2026
    # Source: FIFA / Canada Soccer official. All times PT.
    # ══════════════════════════════════════════════════════════════════════════
    CANADA_SOCCER = [
        ("2026-06-12", "12:00 PM", "Canada", "Bosnia and Herzegovina", "BMO Field, Toronto"),
        ("2026-06-18", "3:00 PM", "Canada", "Qatar", "BC Place, Vancouver"),
        ("2026-06-24", "TBD", "Canada", "Switzerland", "TBD"),
        # Round of 32 onwards — TBD based on group results
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # CANADA RUGBY — WORLD RUGBY NATIONS CUP 2026
    # Source: Rugby Canada. All times PT.
    # ══════════════════════════════════════════════════════════════════════════
    CANADA_RUGBY = [
        ("2026-07-04", "4:00 PM", "Canada", "Spain", "Clarke Stadium, Edmonton"),
        ("2026-07-11", "1:45 PM", "Canada", "Portugal", "Clarke Stadium, Edmonton"),
        ("2026-07-18", "1:45 PM", "Canada", "Zimbabwe", "Princess Auto Stadium, Winnipeg"),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SCOTLAND — FIFA WORLD CUP 2026
    # Source: FIFA / Scotland FA. All times PT.
    # ══════════════════════════════════════════════════════════════════════════
    SCOTLAND_WC = [
        ("2026-06-13", "6:00 PM", "Scotland", "Haiti", "Gillette Stadium, Boston (Foxborough)"),
        ("2026-06-19", "3:00 PM", "Scotland", "Morocco", "Gillette Stadium, Boston (Foxborough)"),
        ("2026-06-24", "3:00 PM", "Scotland", "Brazil", "Miami Stadium, Miami Gardens"),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # BUILD OUTPUT
    # ══════════════════════════════════════════════════════════════════════════

    # ── CFL Games Today ───────────────────────────────────────────────────────
    todays_cfl = [(a, h, t) for d, t, a, h in CFL_SCHEDULE if d == str(today)]
    if todays_cfl:
        lines.append("🏈 CFL TODAY:")
        for away, home, time_pt in todays_cfl:
            lines.append(f"  {away} @ {home} — {time_pt}")

    # ── BC Lions ──────────────────────────────────────────────────────────────
    lions_today = [(ha, opp, loc, t) for d, t, ha, opp, loc in BC_LIONS if d == str(today)]
    lions_next = next(((d, t, ha, opp, loc) for d, t, ha, opp, loc in BC_LIONS
                       if datetime.strptime(d, "%Y-%m-%d").date() > today), None)
    if lions_today:
        for ha, opp, loc, t in lions_today:
            lines.append(f"🦁 BC LIONS TODAY: {ha} {opp} — {t} | {loc}")
    elif lions_next:
        d, t, ha, opp, loc = lions_next
        dt = datetime.strptime(d, "%Y-%m-%d")
        lines.append(f"🦁 BC Lions next: {ha} {opp} — {dt.strftime('%a %b %d')} {t}")
    else:
        lines.append("🦁 BC Lions — Season complete")

    # ── Blue Jays ─────────────────────────────────────────────────────────────
    try:
        data = espn_get("https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/14/schedule?season=2026")
        if data:
            events = data.get("events", [])
            recent = next((e for e in reversed(events) if e.get("competitions") and
                           to_pt(e["date"]).date() < today), None)
            upcoming = next((e for e in events if e.get("competitions") and
                             to_pt(e["date"]).date() >= today), None)
            if recent:
                comp = recent["competitions"][0]
                teams = {t["team"]["abbreviation"]: t for t in comp["competitors"]}
                jays = teams.get("TOR", {})
                opp_abbr = [k for k in teams if k != "TOR"]
                opp = teams.get(opp_abbr[0], {}) if opp_abbr else {}
                jays_score = extract_score(jays.get("score"))
                opp_score = extract_score(opp.get("score"))
                result_str = "✅ W" if jays.get("winner") else "❌ L"
                game_date = to_pt(recent["date"]).strftime("%b %d")
                lines.append(f"⚾ Blue Jays {result_str} {jays_score}–{opp_score} vs {opp.get('team',{}).get('abbreviation','?')} ({game_date})")
            if upcoming:
                comp = upcoming["competitions"][0]
                opp = next((t for t in comp["competitors"] if t["team"]["abbreviation"] != "TOR"), {})
                home_away = "vs" if next((t for t in comp["competitors"] if t["team"]["abbreviation"]=="TOR"),{}).get("homeAway")=="home" else "@"
                dt_pt = to_pt(upcoming["date"])
                if dt_pt.date() == today:
                    lines.append(f"⚾ Blue Jays TODAY: {home_away} {opp.get('team',{}).get('displayName','?')} — {dt_pt.strftime('%-I:%M %p PT')}")
                else:
                    lines.append(f"⚾ Blue Jays next: {home_away} {opp.get('team',{}).get('displayName','?')} — {dt_pt.strftime('%a %b %d %-I:%M %p PT')}")
    except Exception as e:
        print(f"Jays error: {e}")

    # ── Vancouver Canadians (MiLB) ────────────────────────────────────────────
    try:
        data = None
        try:
            req = urllib.request.Request(
                "https://bdfed.stitch.mlbinfra.com/bdfed/transform-milb-schedule?stitch_env=prod&season=2026&teamId=578&sportId=12&gameType=R&startDate=2026-06-01&endDate=2026-08-31&hydrate=team,linescore",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
        except Exception:
            data = None
        if data:
            dates = data.get("dates", [])
            for game_date_obj in dates:
                game_date_str = game_date_obj.get("date", "")
                try:
                    gd = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                except:
                    continue
                if gd == today:
                    for g in game_date_obj.get("games", []):
                        away = g.get("teams", {}).get("away", {}).get("team", {}).get("name", "?")
                        home = g.get("teams", {}).get("home", {}).get("team", {}).get("name", "?")
                        game_time = g.get("gameDate", "")
                        if game_time:
                            try:
                                gt = datetime.fromisoformat(game_time.replace("Z", "+00:00")).astimezone(PT)
                                lines.append(f"⚾ C's TODAY: {away} @ {home} — {gt.strftime('%-I:%M %p PT')}")
                            except:
                                lines.append(f"⚾ C's TODAY: {away} @ {home}")
                    break
                elif gd > today:
                    for g in game_date_obj.get("games", []):
                        away = g.get("teams", {}).get("away", {}).get("team", {}).get("name", "?")
                        home = g.get("teams", {}).get("home", {}).get("team", {}).get("name", "?")
                        game_time = g.get("gameDate", "")
                        if game_time:
                            try:
                                gt = datetime.fromisoformat(game_time.replace("Z", "+00:00")).astimezone(PT)
                                lines.append(f"⚾ C's next: {away} @ {home} — {gt.strftime('%a %b %d %-I:%M %p PT')}")
                            except:
                                lines.append(f"⚾ C's next: {away} @ {home} — {game_date_str}")
                    break
    except Exception as e:
        print(f"Canadians error: {e}")
        lines.append("⚾ Vancouver Canadians — schedule unavailable")

    # ── Canada Soccer World Cup ───────────────────────────────────────────────
    soccer_today = [(t, opp, venue) for d, t, _, opp, venue in CANADA_SOCCER if d == str(today)]
    soccer_next = next(((d, t, _, opp, venue) for d, t, _, opp, venue in CANADA_SOCCER
                        if datetime.strptime(d, "%Y-%m-%d").date() >= today), None)
    if soccer_today:
        for t, opp, venue in soccer_today:
            lines.append(f"⚽ CANADA SOCCER TODAY (World Cup): vs {opp} — {t} | {venue}")
    elif soccer_next:
        d, t, _, opp, venue = soccer_next
        dt = datetime.strptime(d, "%Y-%m-%d")
        days_away = (dt.date() - today).days
        if days_away <= 7:
            lines.append(f"⚽ Canada Soccer (WC): vs {opp} — {dt.strftime('%a %b %d')} {t} | {venue}")

    # ── Scotland World Cup ───────────────────────────────────────────────────
    scotland_today = [(t, opp, venue) for d, t, _, opp, venue in SCOTLAND_WC if d == str(today)]
    scotland_next = next(((d, t, opp, venue) for d, t, _, opp, venue in SCOTLAND_WC
                          if datetime.strptime(d, "%Y-%m-%d").date() >= today), None)
    if scotland_today:
        for t, opp, venue in scotland_today:
            lines.append(f"[SCO] SCOTLAND TODAY (World Cup): vs {opp} -- {t} | {venue}")
    elif scotland_next:
        d, t, opp, venue = scotland_next
        dt = datetime.strptime(d, "%Y-%m-%d")
        days_away = (dt.date() - today).days
        if days_away <= 10:
            lines.append(f"[SCO] Scotland (WC): vs {opp} -- {dt.strftime('%a %b %d')} {t} | {venue}")

    # ── Canada Rugby ─────────────────────────────────────────────────────────
    rugby_today = [(t, opp, venue) for d, t, _, opp, venue in CANADA_RUGBY if d == str(today)]
    rugby_next = next(((d, t, opp, venue) for d, t, _, opp, venue in CANADA_RUGBY
                       if datetime.strptime(d, "%Y-%m-%d").date() >= today), None)
    if rugby_today:
        for t, opp, venue in rugby_today:
            lines.append(f"🏉 CANADA RUGBY TODAY: vs {opp} — {t} | {venue}")
    elif rugby_next:
        d, t, opp, venue = rugby_next
        dt = datetime.strptime(d, "%Y-%m-%d")
        days_away = (dt.date() - today).days
        if days_away <= 14:
            lines.append(f"🏉 Canada Rugby next: vs {opp} — {dt.strftime('%a %b %d')} {t}")

    # ── Canucks ───────────────────────────────────────────────────────────────
    try:
        data = espn_get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/23/schedule?season=2027")
        if data:
            events = data.get("events", [])
            upcoming = next((e for e in events if to_pt(e["date"]).date() >= today), None)
            if upcoming:
                comp = upcoming["competitions"][0]
                opp = next((t for t in comp["competitors"] if t["team"]["abbreviation"] != "VAN"), {})
                lines.append(f"🏒 Canucks next: vs {opp.get('team',{}).get('displayName','?')} — {to_pt(upcoming['date']).strftime('%a %b %d')}")
            else:
                lines.append("🏒 Canucks — Offseason (next season Oct 2026)")
        else:
            lines.append("🏒 Canucks — Offseason (next season Oct 2026)")
    except Exception as e:
        lines.append("🏒 Canucks — Offseason (next season Oct 2026)")

    # ── Manually-maintained facts, with visible staleness ─────────────────────
    _meta = SPORTS_FACTS.get("_meta", {})
    for t in SPORTS_FACTS.get("teams", []):
        if t.get("key") == "canucks":
            continue  # Canucks handled by the live block above
        age, cls, label = fact_age_badge(t.get("verified_on", ""), _meta)
        lines.append(f'{t.get("icon","")} {t.get("label","")} — {t.get("status","")} '
                     f'<span class="fact-age {cls}">{label}</span>')

    # ── UFC Fighter Tracking ──────────────────────────────────────────────────
    lines.append("\n🥊 UFC Fighter Watch:")
    for f in SPORTS_FACTS.get("fighters", []):
        age, cls, label = fact_age_badge(f.get("verified_on", ""), _meta)
        lines.append(f'  {f.get("name","")}: {f.get("last","")} | Next: {f.get("next","")} '
                     f'<span class="fact-age {cls}">{label}</span>')

    # ── UFC ───────────────────────────────────────────────────────────────────
    try:
        data = espn_get("https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard")
        if data:
            events = data.get("events", [])
            future_events = [e for e in events if to_pt(e["date"]).date() >= today_pt()]
            if future_events:
                e = future_events[0]
                dt_pt = to_pt(e["date"])
                if dt_pt.date() == today_pt():
                    lines.append(f"🥊 UFC TODAY: {e.get('name','Event')}")
                else:
                    lines.append(f"🥊 UFC next: {e.get('name','Event')} — {dt_pt.strftime('%a %b %d')}")
    except Exception as e:
        print(f"UFC error: {e}")

    if not lines:
        return "No sports data available."
    return "\n".join(lines)



CLOUDFLARE_WORKER_URL = "https://forge-input.yoseanreid.workers.dev"

def fetch_reminders():
    """Fetch Active This Week reminders via Cloudflare Worker proxy."""
    try:
        req = urllib.request.Request(
            f"{CLOUDFLARE_WORKER_URL}/reminders",
            headers={"User-Agent": "FORGE-Actions"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        # Data is a dict with a "week" key containing newline-separated reminders
        week_text = data.get("week", "")
        if not week_text:
            return []
        items = [line.strip() for line in week_text.strip().split("\n") if line.strip()]
        # Return first 5 most recent (last in list = most recently added)
        return items[-5:] if len(items) > 5 else items
    except Exception as e:
        print(f"Reminders fetch failed: {e}")
        return []


BETTING_INTEL_URL = "https://theseanman.github.io/forge-daily-brief/betting_intel.json"

def fetch_betting_intel():
    """Fetch today's EV signals from betting_intel.json on gh-pages."""
    try:
        req = urllib.request.Request(
            BETTING_INTEL_URL,
            headers={"User-Agent": "FORGE-Actions"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())

        signals = data.get("ev_signals", [])
        generated = data.get("generated_at", "")

        # Filter: EV between 4% and 30% (above 30% is likely bad data)
        filtered = [
            s for s in signals
            if s.get("ev") and 4 <= s["ev"] <= 30
        ]

        # Sort by EV descending, take top 5
        filtered.sort(key=lambda x: x.get("ev", 0), reverse=True)
        return filtered[:5], generated

    except Exception as e:
        print(f"Betting intel fetch failed: {e}")
        return [], ""

HANNIBAL_IMG = "https://upload.wikimedia.org/wikipedia/en/thumb/d/da/Hannibal_Smith.jpg/220px-Hannibal_Smith.jpg"

def generate_sitrep(welltory, sleep, calendar_events, weather, reminders=None):
    """Rule-based FORGE SITREP. Reads data, outputs a terse commander briefing."""
    stress = welltory.get("stress", 50)
    energy = welltory.get("energy", 50)
    health = welltory.get("health", 50)
    sleep_score = sleep.get("score", 80)
    sleep_dur = sleep.get("duration", "7h 0m")
    today_events = calendar_events.get("today", "")
    now = now_pt()
    hour = now.hour
    day_name = now.strftime("%A")

    lines = []

    # ── READINESS ASSESSMENT ──────────────────────────────────────────────────
    if energy <= 35 or stress >= 75:
        readiness = "RED"
        readiness_line = (
            f"Body is in the red. Energy at {energy}%, stress at {stress}%. "
            "This is a conservation day — one priority only. Do not negotiate with the fatigue, work around it."
        )
    elif energy <= 50 or stress >= 60:
        readiness = "AMBER"
        readiness_line = (
            f"Running at reduced capacity. Energy {energy}%, stress {stress}%. "
            "Protect the morning window. Defer anything that can wait."
        )
    elif sleep_score < 70:
        readiness = "AMBER"
        readiness_line = (
            f"Sleep score low at {sleep_score}% ({sleep_dur}). "
            "HRV numbers are holding but don't push hard today. One focused block, then ease off."
        )
    else:
        readiness = "GREEN"
        readiness_line = (
            f"Systems nominal. Energy {energy}%, stress {stress}%, sleep {sleep_score}%. "
            "Execute as planned. You have the bandwidth today — use it."
        )

    lines.append(readiness_line)

    # ── CALENDAR INTEL ────────────────────────────────────────────────────────
    event_list = [e.strip() for e in today_events.strip().split("\n") if e.strip() and e.strip() != "No events today."]
    if event_list:
        if len(event_list) == 1:
            lines.append(f"One commitment on the board today: {event_list[0]}. Everything else is yours.")
        elif len(event_list) == 2:
            lines.append(f"Two commitments today: {event_list[0]} and {event_list[1]}. Work the gaps between them.")
        else:
            lines.append(
                f"You have {len(event_list)} commitments today. First up: {event_list[0]}. "
                f"Last: {event_list[-1]}. Identify your one deep work block and protect it."
            )
    else:
        lines.append("Calendar is clear today. Rare. Use it deliberately — blank days disappear fast.")

    # ── STRATEGIC DIRECTION ───────────────────────────────────────────────────
    if readiness == "RED":
        lines.append(
            "Strategy: survive and recover. Single task. No big decisions. "
            "The Operator protects the Architect today."
        )
    elif readiness == "AMBER":
        lines.append(
            "Strategy: one meaningful output before noon. After that, maintenance mode. "
            "Ask 'what is the single move that matters most today' — then only do that."
        )
    else:
        if day_name in ("Monday", "Tuesday", "Wednesday"):
            lines.append(
                "Strategy: deep work first. "
                "High cortisol window is now. Shut the noise, open the hardest thing, execute."
            )
        elif day_name == "Thursday":
            lines.append(
                "Strategy: close open loops. "
                "Thursday is a finisher day — identify what needs to be done before Friday and do it."
            )
        elif day_name == "Friday":
            lines.append(
                "Strategy: complete and document. "
                "Finish what you started this week. Set Monday up before you close out."
            )
        else:
            lines.append(
                "Strategy: recharge with intention. "
                "Rest is not absence of work — it is preparation for it. Do one meaningful personal thing today."
            )

    # ── ACTIVE REMINDERS ─────────────────────────────────────────────────────
    if reminders:
        reminder_count = len(reminders)
        top = reminders[-1]  # most recently added
        lines.append(f"Active reminders: {reminder_count} items. Top of stack: {top[:80]}{'...' if len(top) > 80 else ''}")

    # ── MINDSET CUE ──────────────────────────────────────────────────────────
    if stress >= 60:
        lines.append("No narrative. Just this. What is the next physical action? Do that.")
    elif energy <= 45:
        lines.append("Pace, not intensity. Slow is smooth. Smooth is output.")
    else:
        lines.append("The Quiet Strategist operates from here. One step ahead. Always.")

    return " ".join(lines)

def generate_html(welltory, sleep, weather, calendar_events, week_structured=None, body_comp=None):
    now = now_pt()
    day_name = now.strftime("%A")
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    day_of_week = now.weekday()
    day_of_year = now.timetuple().tm_yday
    wisdom = get_wisdom(day_of_year)
    triad_block = render_triad(day_of_year)
    protocol_block = render_summer_protocol()
    sports_text = get_sports_updates()
    reminders = fetch_reminders()
    sitrep_text = generate_sitrep(welltory, sleep, calendar_events, weather, reminders)

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

    colonel = get_colonel_line()
    model = get_mental_model()
    strat = get_strategy()

    def _examples_html(entry):
        ex = entry.get("examples") or []
        if not ex:
            return ""
        rows = "".join(f'<div class="depth-ex">{e}</div>' for e in ex)
        return f'<div class="depth-ex-wrap"><div class="depth-ex-head">In practice</div>{rows}</div>'

    model_examples_html = _examples_html(model)
    strat_examples_html = _examples_html(strat)
    if POOL_ERRORS:
        _rows = "".join(f"<div>&#9888; {e}</div>" for e in POOL_ERRORS)
        pool_error_html = f'<div class="pool-error">CONTENT POOLS FAILED TO LOAD &mdash; showing fallbacks{_rows}</div>'
    else:
        pool_error_html = ""
    if CALENDAR_ERRORS:
        _crows = "".join(f"<div>&#9888; {e}</div>" for e in CALENDAR_ERRORS)
        pool_error_html += f'<div class="pool-error">CALENDAR FEED PROBLEM &mdash; some events may be missing{_crows}</div>' 

    cal_json = json.dumps(week_structured or [])
    cal_today = calendar_events.get("today", "No events today.")
    if body_comp is None:
        body_comp = {}
    bc_weight      = body_comp.get("weight")
    bc_fat         = body_comp.get("body_fat")
    bc_muscle      = body_comp.get("muscle_mass")
    bc_bmi         = body_comp.get("bmi")
    bc_visceral    = body_comp.get("visceral_fat")
    bc_has_data    = any(v is not None for v in [bc_weight, bc_fat, bc_muscle, bc_bmi, bc_visceral])
    wisdom_self_defense = wisdom["self_defense"]
    wisdom_parenting = wisdom["parenting"]
    wisdom_fatherhood = wisdom["fatherhood"]
    wisdom_mindset = wisdom["mindset"]
    wisdom_longevity = wisdom["longevity"]
    wisdom_life_hack = wisdom["life_hack"]
    sports_section = sports_text
    sitrep_text = sitrep_text  # passed to HTML template
    # Fetch betting intel
    betting_signals, betting_generated = fetch_betting_intel()
    # Filter to next 48h only
    betting_signals_today = [s for s in betting_signals if s.get("hours_until", 999) <= 48]
    if betting_signals_today:
        sbos_rows = ''
        for sig in betting_signals_today:
            sport = sig.get('sport', '')
            matchup = sig.get('matchup', '')
            signal = sig.get('signal', '')
            ev = sig.get('ev', 0)
            hours = sig.get('hours_until', 0)
            hours_str = f"{hours:.0f}h away" if hours > 1 else "Starting soon"
            sbos_rows += f'<div class="mini-card"><div class="mini-title">[{sport}] {matchup}</div><div class="mini-detail" style="font-size:13px;">&#x26A1; {signal} &nbsp;&#183;&nbsp; {hours_str}</div></div>'
        sbos_signals_html = f'<div class="mini-card" style="background:rgba(255,200,0,0.2);"><div class="mini-title">&#x26A1; Top EV Signals (Next 48h)</div></div>{sbos_rows}'
    else:
        sbos_signals_html = '<div class="mini-card"><div class="mini-detail">No EV signals in next 48h. Check Telegram for CFL alerts.</div></div>'

    stoic = STOIC_QUOTES[get_daily_index(len(STOIC_QUOTES))]
    stoic_quote = stoic["text"]; stoic_source = stoic["source"]
    jlpt = JLPT_WORDS[get_daily_index(len(JLPT_WORDS))]
    jlpt_word = jlpt["word"]; jlpt_level = jlpt["level"]; jlpt_meaning = jlpt["meaning"]
    jlpt_example = jlpt["example"]; jlpt_translation = jlpt["translation"]
    cal_week = calendar_events.get("week", "No events this week.")
    cal_month = calendar_events.get("month", "No events this month.")

    # Build body comp content
    if bc_has_data:
        bc_rows = ""
        if bc_weight   is not None: bc_rows += f'<div class="stat-block"><div class="stat-val">{bc_weight}</div><div class="stat-label">Weight (lbs)</div></div>'
        if bc_fat      is not None: bc_rows += f'<div class="stat-block"><div class="stat-val">{bc_fat}%</div><div class="stat-label">Body Fat</div></div>'
        if bc_muscle   is not None: bc_rows += f'<div class="stat-block"><div class="stat-val">{bc_muscle}</div><div class="stat-label">Muscle (lbs)</div></div>'
        if bc_bmi      is not None: bc_rows += f'<div class="stat-block"><div class="stat-val">{bc_bmi}</div><div class="stat-label">BMI</div></div>'
        if bc_visceral is not None: bc_rows += f'<div class="stat-block"><div class="stat-val">{bc_visceral}</div><div class="stat-label">Visceral Fat</div></div>'
        body_comp_content = f'<div class="stat-row" style="grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));">{bc_rows}</div>'
    else:
        body_comp_content = '<div class="mini-card"><div class="mini-detail">No body comp data yet. <a href="input.html">Enter via input form →</a></div></div>'


    from datetime import date as _date
    METAL_SHOWS = [
        ("2026-06-25", "Anvil + Midnite Hellion", "El Corazon, Seattle"),
        ("2026-06-27", "Anvil + Midnite Hellion", "Astoria, Vancouver"),
        ("2026-07-08", "Jinjer + Entheos + Crystal Lake", "Commodore Ballroom, Vancouver"),
    ]
    _today_d = _date.today()
    _upcoming = [(d,t,v) for d,t,v in METAL_SHOWS if _date.fromisoformat(d) >= _today_d]
    def _fsd(iso):
        return _date.fromisoformat(iso).strftime("%B %-d").upper()
    if _upcoming:
        _cards = []
        for d,t,v in _upcoming:
            _cards.append(f'<div class="mini-card"><div class="mini-title">🎸 {_fsd(d)} · {t}</div><div class="mini-detail">{v}</div></div>')
        concert_cards_html = '  <div class="card"><div class="card-header"><span class="card-icon">🎸🌴</span><span>Upcoming Metal Shows</span></div>\n    ' + "\n    ".join(_cards) + '\n  </div>'
    else:
        concert_cards_html = '  <div class="card"><div class="card-header"><span class="card-icon">🎸🌴</span><span>Upcoming Metal Shows</span></div><div class="mini-card"><div class="mini-detail">No upcoming shows.</div></div></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
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
    /* ── Forge redesign: focus prompt, depth panel, staleness, collapse ── */
    .focus-prompt {{ font-size: 21px; line-height: 1.5; font-weight: 700; color: var(--text-bright);
                     background: rgba(255,255,255,0.16); border-left: 5px solid var(--text-bright);
                     border-radius: 10px; padding: 16px 18px; margin-bottom: 12px; }}
    .strat-cat {{ display: inline-block; font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
                  background: rgba(255,255,255,0.25); border-radius: 5px; padding: 3px 9px;
                  margin-bottom: 10px; font-weight: 700; }}
    .depth-toggle {{ display: flex; justify-content: space-between; align-items: center; cursor: pointer;
                     touch-action: manipulation; font-size: 12px; letter-spacing: 0.1em; font-weight: 700;
                     text-transform: uppercase; color: var(--text-light); padding: 10px 2px;
                     border-top: 1px solid rgba(255,255,255,0.25); }}
    .depth-chevron {{ transition: transform 0.2s; font-size: 15px; }}
    .depth-toggle.open .depth-chevron {{ transform: rotate(180deg); }}
    .depth-body {{ display: none; padding-top: 4px; }}
    .depth-body.open {{ display: block; }}
    .depth-origin {{ font-size: 11px; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 8px; }}
    .depth-what {{ font-size: 14px; line-height: 1.65; margin-bottom: 12px; }}
    .depth-ex-wrap {{ margin-top: 6px; }}
    .depth-ex-head {{ font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
                      color: var(--muted); margin-bottom: 6px; font-weight: 700; }}
    .depth-ex {{ font-size: 13px; line-height: 1.6; padding: 8px 0 8px 12px;
                 border-left: 2px solid rgba(255,255,255,0.3); margin-bottom: 6px; }}
    .fact-age {{ font-size: 10px; letter-spacing: 0.08em; padding: 2px 7px; border-radius: 4px;
                 margin-left: 6px; font-weight: 700; }}
    .fact-fresh {{ background: rgba(255,255,255,0.18); color: var(--muted); }}
    .fact-warn {{ background: rgba(230,160,20,0.35); color: #4a2c00; }}
    .fact-stale {{ background: rgba(200,30,30,0.55); color: #fff; }}
    .pool-error {{ background: #8a1010; color: #fff; border-radius: 10px; padding: 12px 14px;
                   margin-bottom: 14px; font-size: 13px; font-weight: 700; line-height: 1.5; }}
    .card.collapsed .card-body {{ display: none; }}
    .card-collapse {{ float: right; cursor: pointer; touch-action: manipulation;
                      font-size: 15px; opacity: 0.7; padding: 0 4px; }}
    .yday-line {{ background: rgba(0,0,0,0.35); color: var(--text-bright); border-radius: 10px;
                  padding: 10px 14px; margin-bottom: 12px; font-size: 14px; font-weight: 700; }}
    .rocks-line {{ background: rgba(255,255,255,0.16); border: 2px solid var(--text-bright);
                   border-radius: 10px; padding: 12px 14px; margin-bottom: 14px; font-size: 13px; }}
    .rocks-head {{ font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
                   margin-bottom: 6px; font-weight: 700; }}
    .rock-item {{ padding: 4px 0; line-height: 1.5; }}
    .t5-count {{ font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
                 font-weight: 800; color: var(--text-bright); margin-bottom: 10px; opacity: 0.85; }}
    .t5-row {{ display: flex; gap: 10px; align-items: flex-start; padding: 9px 0;
               border-bottom: 1px solid rgba(255,255,255,0.14); }}
    .t5-row:last-child {{ border-bottom: none; }}
    .t5-tick {{ font-size: 16px; line-height: 1.35; min-width: 18px; color: var(--text-bright); }}
    .t5-task {{ font-size: 15px; font-weight: 700; line-height: 1.45; }}
    .t5-done .t5-task {{ opacity: 0.5; text-decoration: line-through; }}
    .t5-star {{ color: #FFC94A; }}
    .t5-meta {{ font-size: 11px; opacity: 0.75; margin-top: 3px; letter-spacing: 0.04em; }}
    .t5-dw {{ font-size: 12px; opacity: 0.85; margin-top: 3px; font-style: italic; }}
    .t5-empty {{ font-size: 14px; line-height: 1.6; opacity: 0.9; }}
    .new-flag {{ display: inline-block; background: rgba(74,232,160,0.85); color: #062012;
                 font-size: 9px; font-weight: 800; letter-spacing: 0.1em; padding: 2px 6px;
                 border-radius: 4px; margin-right: 6px; vertical-align: middle; }}
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
    .triad-mode {{ margin-bottom: 14px; }}
    .triad-label {{ font-size: 12px; font-weight: 700; color: var(--text-bright); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
    .triad-anchor {{ background: rgba(255,255,255,0.1); border-left: 3px solid var(--text-bright); border-radius: 6px; padding: 10px 12px; margin-bottom: 6px; font-size: 13px; color: var(--text-light); line-height: 1.5; }}
    .triad-anchor-hi {{ background: rgba(255,255,255,0.28); border-left: 5px solid var(--text-bright); font-weight: 700; box-shadow: 0 0 0 1px var(--text-bright); }}
    .triad-text {{ background: rgba(255,255,255,0.1); border: 2px solid var(--text-bright); border-radius: 8px; padding: 12px; font-size: 13px; color: var(--text-light); line-height: 1.5; }}
    .proto-intro {{ font-size: 13px; color: var(--muted); font-style: italic; margin-bottom: 14px; padding: 0 2px; }}
    .proto-drill {{ background: rgba(255,255,255,0.1); border-left: 4px solid #ff6d00; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; }}
    .proto-name {{ font-size: 14px; font-weight: 700; color: var(--text-bright); margin-bottom: 4px; }}
    .proto-inst {{ font-size: 13px; color: var(--text-light); line-height: 1.5; margin-bottom: 4px; }}
    .proto-trigger {{ font-size: 11px; color: var(--muted); font-weight: 600; }}
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
    <img class="character-image" src="hannibal.jpg" alt="The Colonel" onerror="this.style.display='none'">
    <div>
      <div class="character-quote">{colonel['line']}</div>
      <div class="character-name">— The Colonel&rsquo;s Take &middot; {colonel.get('tag','')}</div>
    </div>
  </div>

  {pool_error_html}
  <div id="yday-host"></div>
  <div id="rocks-host"></div>
  <div class="alert-banner">🚨 {mode} {mode_advice}</div>

  <div class="card" style="background: linear-gradient(135deg, rgba(0,0,0,0.25), rgba(30,10,0,0.2)); border: 3px solid var(--text-bright);">
    <div class="card-header"><span class="card-icon">&#x1F4CB;&#x1F334;</span><span>FORGE SITREP</span></div>
    <div style="display:flex; flex-direction:row; gap:16px; align-items:flex-start;">
      <img src="https://theseanman.github.io/forge-daily-brief/hannibal.jpg"
           alt="Hannibal Smith"
           style="width:90px; min-width:90px; border-radius:8px; border:3px solid var(--text-bright); object-fit:cover;"
           onerror="this.style.display='none'; this.nextElementSibling.style.marginLeft='0'">
      <div style="font-size:15px; color:var(--text-bright); line-height:1.9; font-weight:600; flex:1; min-width:0;">{sitrep_text}</div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">&#x1F3AF;&#x1F334;</span><span>Today&rsquo;s Five</span></div>
    <div id="today-five-host"></div>
    <div class="mini-card"><div class="mini-detail"><a href="https://theseanman.github.io/forge-daily-brief/planner.html">Open the day planner &#8594;</a><br><span style="font-size:12px;">Hour-by-hour grid with the calendar auto-filled. Set or edit the five here.</span></div></div>
  </div>

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
      Brief pause before any response. Conscious deliberation first.<br><span style="font-weight:400; font-size:13px;">🚪 Training rep: one slow nasal breath at every doorway, kettle, or red light. Don&rsquo;t force the pause in conversations yet &mdash; groove the breath on the cue and it shows up when it matters.</span>
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
      Deliberate, slower pace in all physical and verbal communication.<br><span style="font-weight:400; font-size:13px;">🐢 The rep: move 20% slower than your impulse &mdash; reach, turn, walk slower. Cue: all day.</span>
    </div>
    <div class="paramount-goal">
      <div class="paramount-num"><span>4️⃣ OPPORTUNITY SCANNING</span>
        <div class="goal-controls">
          <button class="goal-btn" onclick="decrementGoal(3)">−</button>
          <span class="goal-counter" id="goal-3-counter">0</span>
          <button class="goal-btn" onclick="incrementGoal(3)">+</button>
        </div>
      </div>
      Every setback or new environment: "What opportunity does this situation present me with?"<br><span style="font-weight:400; font-size:13px;">⚡ Cue: setback or threshold &mdash; ask it at the first one of the day.</span>
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

{protocol_block}

{triad_block}

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
    <div class="card-header"><span class="card-icon">⚖️🌴</span><span>Body Composition</span></div>
    {body_comp_content}
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">🌤️🌴</span><span>Richmond Weather</span></div>
    <div class="mini-card"><div class="mini-detail">{weather}</div></div>
  </div>

  <div class="card" data-newscan>
    <div class="card-header"><span class="card-icon">📅🌴</span><span>Today — {date_str}</span></div>
    <div class="mini-card"><div class="mini-detail"><pre style="font-size:13px; color:var(--text-light); white-space:pre-wrap; word-wrap:break-word; font-family:-apple-system,sans-serif;">{cal_today}</pre></div></div>
  </div>

  <div class="card" data-newscan>
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
      <div class="advice-item"><div class="advice-label">🥋 Self-Defense</div><div class="advice-text">{wisdom_self_defense}</div></div>
      <div class="advice-item"><div class="advice-label">👨‍👧‍👦 Parenting</div><div class="advice-text">{wisdom_parenting}</div></div>
      <div class="advice-item"><div class="advice-label">👨 Fatherhood</div><div class="advice-text">{wisdom_fatherhood}</div></div>
      <div class="advice-item"><div class="advice-label">🧠 Mindset</div><div class="advice-text">{wisdom_mindset}</div></div>
      <div class="advice-item"><div class="advice-label">⏳ Longevity</div><div class="advice-text">{wisdom_longevity}</div></div>
      <div class="advice-item"><div class="advice-label">⚡ Life Hack</div><div class="advice-text">{wisdom_life_hack}</div></div>
    </div>
  </div>



  <div class="card">
    <div class="card-header"><span class="card-icon">🏆🌴</span><span>Sports Intel</span></div>
    <div class="mini-card"><div class="mini-detail" style="white-space:pre-wrap; font-size:14px; line-height:1.8;">{sports_section}</div></div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">&#x1F3B0;&#x1F334;</span><span>SBOS Betting Intel</span></div>
    {sbos_signals_html}
    <div class="mini-card">
      <div class="mini-title">&#x1F4E1; CFL Telegram</div>
      <div class="mini-detail" style="font-size:13px; line-height:1.8;">
        @SeanTradingAlertsBot &nbsp;&#183;&nbsp; Commands: <strong>STATUS</strong> &nbsp;&#183;&nbsp; <strong>Y</strong> &nbsp;&#183;&nbsp; <strong>HALF</strong> &nbsp;&#183;&nbsp; <strong>WATCH</strong> &nbsp;&#183;&nbsp; <strong>N</strong> &nbsp;&#183;&nbsp; <strong>RESULT</strong>
      </div>
    </div>
    <div class="mini-card">
      <div class="mini-title">&#x1F4CB; S1/S5 Scoring</div>
      <div class="mini-detail" style="font-size:13px; line-height:1.8;">
        <strong>S1:</strong> 1=neutral 2=home edge 3=strong narrative &nbsp;&#183;&nbsp; <strong>S5:</strong> 1=neutral 2=pressure 3=high-stakes<br>
        <strong>Tier A (17-21):</strong> Full &nbsp;&#183;&nbsp; <strong>Tier B (13-16):</strong> Half &nbsp;&#183;&nbsp; <strong>Tier C:</strong> Pass
      </div>
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

  <div class="card" data-card="model">
    <div class="card-header"><span class="card-icon">&#x1F9E0;&#x1F334;</span><span>Mental Model &mdash; {model['name']}</span></div>
    <div class="focus-prompt">{model['focus']}</div>
    <div class="depth-toggle" onclick="toggleDepth(this)">
      <span class="depth-label">What it is &amp; how it applies</span><span class="depth-chevron">&#x25BE;</span>
    </div>
    <div class="depth-body">
      <div class="depth-origin">{model.get('origin','')}</div>
      <div class="depth-what">{model['what']}</div>
      {model_examples_html}
      <div style="margin-top:8px; font-size:12px;"><a href="https://theseanman.github.io/forge-daily-brief/models.html">Browse the full library &#8594;</a></div>
    </div>
  </div>

  <div class="card" data-card="strategy">
    <div class="card-header"><span class="card-icon">&#x265F;&#xFE0F;&#x1F334;</span><span>Strategy &mdash; {strat['name']}</span></div>
    <div class="strat-cat">{strat.get('category','')}</div>
    <div class="focus-prompt">{strat['focus']}</div>
    <div class="depth-toggle" onclick="toggleDepth(this)">
      <span class="depth-label">What it is &amp; how it applies</span><span class="depth-chevron">&#x25BE;</span>
    </div>
    <div class="depth-body">
      <div class="depth-what">{strat['what']}</div>
      {strat_examples_html}
      <div style="margin-top:8px; font-size:12px;"><a href="https://theseanman.github.io/forge-daily-brief/models.html">Browse the full library &#8594;</a></div>
    </div>
  </div>


{concert_cards_html}


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
window.FORGE_GEN_DATE = "{now.strftime('%Y-%m-%d')}";
window.onload = function() {{
  loadCounts(); setInterval(tick, 1000);
  // Staleness check. FORGE_GEN_DATE is stamped in PACIFIC time, but the device may be in
  // any timezone, so a gap of up to a day is normal and is NOT stale. Only a gap of a full
  // day or more means the daily workflow actually failed to run.
  // The reload is attempted at most ONCE per tab, so this can never loop.
  try {{
    var gen = new Date(window.FORGE_GEN_DATE + 'T12:00:00');
    var days = Math.floor((new Date() - gen) / 86400000);
    if (days >= 1) {{
      if (!sessionStorage.getItem('forge-stale-reload')) {{
        sessionStorage.setItem('forge-stale-reload', '1');
        location.replace(location.href.split('?')[0] + '?v=' + Date.now());
        return;
      }}
      var b = document.createElement('div');
      b.style.cssText = 'background:#8b1a1a;color:#fff;padding:10px 14px;font-size:13px;' +
                        'font-weight:800;text-align:center;letter-spacing:0.04em;';
      b.textContent = 'STALE BRIEF \u2014 generated ' + window.FORGE_GEN_DATE +
                      '. The daily workflow has not run since. Data below is out of date.';
      document.body.insertBefore(b, document.body.firstChild);
    }}
  }} catch (e) {{}}
}};
/* ── Depth panels: expand the explanation behind the focus prompt ───────── */
function toggleDepth(el) {{
  el.classList.toggle('open');
  var body = el.nextElementSibling;
  if (body) body.classList.toggle('open');
}}

/* ── Collapsible cards that remember what you left closed ───────────────── */
var FORGE_COLLAPSE_KEY = 'forge-collapsed-cards';
function readCollapsed() {{
  try {{ var v = localStorage.getItem(FORGE_COLLAPSE_KEY); return v ? JSON.parse(v) : []; }}
  catch (e) {{ return []; }}
}}
function writeCollapsed(a) {{
  try {{ localStorage.setItem(FORGE_COLLAPSE_KEY, JSON.stringify(a)); }} catch (e) {{}}
}}
function initCollapse() {{
  var closed = readCollapsed();
  var cards = document.querySelectorAll('.card');
  for (var i = 0; i < cards.length; i++) {{
    (function (card, i) {{
      var header = card.querySelector('.card-header');
      if (!header) return;
      var id = card.getAttribute('data-card') ||
               (header.textContent || '').trim().slice(0, 40) || ('card' + i);
      card.setAttribute('data-cid', id);

      /* wrap everything after the header so it can be hidden */
      if (!card.querySelector('.card-body')) {{
        var body = document.createElement('div');
        body.className = 'card-body';
        while (header.nextSibling) body.appendChild(header.nextSibling);
        card.appendChild(body);
      }}

      var btn = document.createElement('span');
      btn.className = 'card-collapse';
      btn.innerHTML = '&#x25BE;';
      header.appendChild(btn);

      if (closed.indexOf(id) !== -1) {{
        card.classList.add('collapsed');
        btn.innerHTML = '&#x25B8;';
      }}
      header.style.cursor = 'pointer';
      header.onclick = function (ev) {{
        if (ev.target.tagName === 'A' || ev.target.tagName === 'BUTTON') return;
        card.classList.toggle('collapsed');
        var isClosed = card.classList.contains('collapsed');
        btn.innerHTML = isClosed ? '&#x25B8;' : '&#x25BE;';
        var list = readCollapsed();
        var at = list.indexOf(id);
        if (isClosed && at === -1) list.push(id);
        if (!isClosed && at !== -1) list.splice(at, 1);
        writeCollapsed(list);
      }};
    }})(cards[i], i);
  }}
}}

/* ── Yesterday's completion + this week's big rocks, read from planner storage ── */
function ymdOffset(days) {{
  var d = new Date();
  d.setDate(d.getDate() + days);
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') +
         '-' + String(d.getDate()).padStart(2, '0');
}}
function readJSONKey(k, fb) {{
  try {{ var v = localStorage.getItem(k); return v ? JSON.parse(v) : fb; }}
  catch (e) {{ return fb; }}
}}
var SYNC_URL = 'https://forge-sync.yoseanreid.workers.dev';
function syncPullBrief() {{
  fetch(SYNC_URL + '/forge-top5')
    .then(function(r) {{ if (!r.ok) throw new Error(r.status); return r.json(); }})
    .then(function(cloud) {{
      if (!cloud || typeof cloud !== 'object' || Array.isArray(cloud)) return;
      var all = readJSONKey('forge-top5', {{}});
      var changed = false;
      for (var dk in cloud) {{
        if (cloud.hasOwnProperty(dk) && JSON.stringify(all[dk]) !== JSON.stringify(cloud[dk])) {{
          all[dk] = cloud[dk]; changed = true;
        }}
      }}
      if (changed) {{
        try {{ localStorage.setItem('forge-top5', JSON.stringify(all)); }} catch(e) {{}}
        try {{ paintTodayFive(); }} catch(e) {{}}
      }}
    }})
    .catch(function() {{}});
}}
function t5Esc(s) {{
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}}
function paintTodayFive() {{
  var host = document.getElementById('today-five-host');
  if (!host) return;
  var all = readJSONKey('forge-top5', {{}});
  var arr = all[ymdOffset(0)];
  var real = (arr || []).filter(function (i) {{ return i && i.t; }});
  if (!real.length) {{
    host.innerHTML = '<div class="t5-empty">No five set for today yet. Set them in the evening debrief or the planner &mdash; they appear here as soon as they exist.</div>';
    return;
  }}
  var done = real.filter(function (i) {{ return i.done; }}).length;
  var rows = real.map(function (i) {{
    var meta = [];
    if (i.h) meta.push(t5Esc(i.h));
    if (i.m) meta.push(t5Esc(i.m) + ' min');
    if (i.c) meta.push('carried &times;' + t5Esc(i.c));
    return '<div class="t5-row' + (i.done ? ' t5-done' : '') + '">' +
           '<span class="t5-tick">' + (i.done ? '&#10003;' : '&#9633;') + '</span>' +
           '<div style="flex:1; min-width:0;">' +
           '<div class="t5-task">' + (i.k ? '<span class="t5-star">&#9733;</span> ' : '') + t5Esc(i.t) + '</div>' +
           (meta.length ? '<div class="t5-meta">' + meta.join(' &middot; ') + '</div>' : '') +
           (i.dw ? '<div class="t5-dw">Done when: ' + t5Esc(i.dw) + '</div>' : '') +
           '</div></div>';
  }}).join('');
  host.innerHTML = '<div class="t5-count">' + done + ' of ' + real.length + ' closed</div>' + rows;
}}
function paintYesterday() {{
  var host = document.getElementById('yday-host');
  if (!host) return;
  var all = readJSONKey('forge-top5', {{}});
  var arr = all[ymdOffset(-1)];
  if (!arr) {{ host.innerHTML = ''; return; }}
  var real = arr.filter(function (i) {{ return i && i.t; }});
  if (!real.length) {{ host.innerHTML = ''; return; }}
  var done = real.filter(function (i) {{ return i.done; }}).length;
  var msg = done === real.length ? 'Clean sweep.'
          : done === 0 ? 'Nothing closed. Fresh start.'
          : 'Roll the rest forward.';
  host.innerHTML = '<div class="yday-line">Yesterday: ' + done + ' of ' + real.length +
                   ' &nbsp;&middot;&nbsp; <span style="font-weight:400;">' + msg + '</span></div>';
}}
function paintRocks() {{
  var host = document.getElementById('rocks-host');
  if (!host) return;
  var r = readJSONKey('forge-week-rocks', null);
  if (!r || !r.items || !r.items.length) {{ host.innerHTML = ''; return; }}
  var rows = r.items.map(function (t, i) {{
    return '<div class="rock-item">' + (i + 1) + '. ' + t + '</div>';
  }}).join('');
  host.innerHTML = '<div class="rocks-line"><div class="rocks-head">&#x1FAA8; This week&rsquo;s big rocks</div>' +
                   rows + '</div>';
}}

/* ── "New since yesterday" markers on calendar and reminder lines ────────── */
var FORGE_SEEN_KEY = 'forge-seen-lines';
function markNew() {{
  var seen = readJSONKey(FORGE_SEEN_KEY, {{}});
  var prev = seen.lines || [];
  var current = [];
  var targets = document.querySelectorAll('[data-newscan] .mini-title, [data-newscan] .mini-detail');
  for (var i = 0; i < targets.length; i++) {{
    var txt = (targets[i].textContent || '').trim();
    if (!txt) continue;
    current.push(txt);
    if (prev.length && prev.indexOf(txt) === -1) {{
      var flag = document.createElement('span');
      flag.className = 'new-flag';
      flag.textContent = 'NEW';
      targets[i].insertBefore(flag, targets[i].firstChild);
    }}
  }}
  try {{
    localStorage.setItem(FORGE_SEEN_KEY, JSON.stringify({{ lines: current, on: ymdOffset(0) }}));
  }} catch (e) {{}}
}}

window.addEventListener('load', function () {{
  try {{ paintTodayFive(); }} catch (e) {{}}
  try {{ syncPullBrief(); }} catch (e) {{}}
  try {{ paintYesterday(); }} catch (e) {{}}
  try {{ paintRocks(); }} catch (e) {{}}
  try {{ markNew(); }} catch (e) {{}}
  try {{ initCollapse(); }} catch (e) {{}}
}});
</script>
</body>
</html>"""
    return html

def main():
    print("🌴 FORGE OS GitHub Actions Brief Generator")
    
    user_data = load_user_data()
    welltory = user_data.get("welltory", {"stress": 50, "energy": 50, "health": 50})
    sleep = user_data.get("sleep", {"score": 85, "duration": "7h 0m", "hr_range": "50–70"})
    body_comp = user_data.get("body_comp", {"weight": None, "body_fat": None, "muscle_mass": None, "bmi": None, "visceral_fat": None})
    
    print(f"✓ Loaded user data: Stress {welltory['stress']}%, Energy {welltory['energy']}%, Health {welltory['health']}%")
    
    weather = get_weather()
    calendar = get_calendar_events()
    
    # Push 7-day calendar to JSONBin for Evening Debrief
    if calendar.get("week_structured"):
        push_calendar_to_jsonbin(calendar["week_structured"])
    
    html = generate_html(welltory, sleep, weather, calendar, calendar.get("week_structured", []), body_comp)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ index.html generated successfully")

if __name__ == "__main__":
    main()
