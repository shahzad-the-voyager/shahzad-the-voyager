import datetime as dt
import json
import urllib.parse
import urllib.request

from common import FONT, esc, path, write_themed

AU_KM = 149_597_870.7
LIGHT_SECONDS_PER_AU = 499.004784
HORIZONS = "https://ssd.jpl.nasa.gov/api/horizons.api"
W, H = 960, 78


def voyager1(day):
    params = {
        "format": "json",
        "COMMAND": "'-31'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'500@399'",
        "START_TIME": f"'{day.isoformat()}'",
        "STOP_TIME": f"'{(day + dt.timedelta(days=1)).isoformat()}'",
        "STEP_SIZE": "'1 d'",
        "QUANTITIES": "'20'",
    }
    url = HORIZONS + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "profile-telemetry"})
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.load(r)["result"]
    row = result.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines()[0].split()
    return float(row[2]), float(row[3])


def months_between(start, today):
    y, m = map(int, start.split("-"))
    total = (today.year - y) * 12 + (today.month - m)
    return total // 12, total % 12


def race_line(race, today):
    d = dt.date.fromisoformat(race["date"])
    goal = race["goal_loops"]
    km = race["loop_km"]
    if race.get("result_loops") is not None:
        n = race["result_loops"]
        mark = " · GOAL REACHED" if n >= goal else ""
        return f"BACKYARD ULTRA · {n} LOOPS · {n * km:.1f} KM{mark}"
    days = (d - today).days
    if days > 1:
        return f"T−{days} DAYS TO THE {race['name'].upper()} · {race['place'].upper()} · GOAL {goal} LOOPS"
    if days == 1:
        return f"T−1 DAY TO THE {race['name'].upper()} · GOAL {goal} LOOPS · {goal * km:.0f} KM"
    if days == 0:
        return f"RACE DAY · LOOP 01 STARTS AT THE TOP OF THE HOUR · GOAL {goal}"
    return f"{race['name'].upper()} · RUN · RESULT INCOMING"


def render(t, data):
    km = data["au"] * AU_KM
    lt = data["au"] * LIGHT_SECONDS_PER_AU
    h, m = int(lt // 3600), int(lt % 3600 // 60)
    milestone = "  ▲ PAST ONE LIGHT-DAY" if lt >= 86400 else ""
    line1 = (f'<tspan fill="{t["fg"]}" font-weight="700">{km / 1e9:,.3f} BILLION KM</tspan> FROM EARTH · '
             f'LIGHT-TIME {h} H {m:02d} M · RECEDING {data["rate"]:.1f} KM/S'
             f'<tspan fill="{t["blue"]}">{milestone}</tspan>')
    yrs, mos = data["service"]
    line2 = (f'<tspan fill="{t["fg"]}" font-weight="700">{yrs} YR {mos} MO</tspan> IN PRODUCTION · '
             f'<tspan fill="{t["red"]}">{esc(data["race"])}</tspan>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">Live telemetry, updated {data["date"]}</title>
  <desc id="desc">Voyager 1 is {km / 1e9:,.3f} billion km from Earth, light-time {h} hours {m} minutes, per NASA JPL Horizons on {data["date"]}. This probe: {yrs} years {mos} months in production. {esc(data["race"])}.</desc>
  <style>
    .t {{ font-family: {FONT}; }}
    .live {{ animation: live 1.6s ease-in-out infinite; }}
    @keyframes live {{ 50% {{ opacity: .25; }} }}
    @media (prefers-reduced-motion: reduce) {{ .live {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="none" stroke="{t["line"]}"/>
  <circle class="live" cx="22" cy="20" r="3.4" fill="{t["blue"]}"/>
  <text x="34" y="24" class="t" font-size="11" letter-spacing="2" fill="{t["blue"]}">VOYAGER 1</text>
  <text x="146" y="24" class="t" font-size="11" letter-spacing="1.2" fill="{t["muted"]}">{line1}</text>
  <circle class="live" cx="22" cy="50" r="3.4" fill="{t["red"]}" style="animation-delay:.8s"/>
  <text x="34" y="54" class="t" font-size="11" letter-spacing="2" fill="{t["red"]}">THIS PROBE</text>
  <text x="146" y="54" class="t" font-size="11" letter-spacing="1.2" fill="{t["muted"]}">{line2}</text>
  <text x="{W - 16}" y="70" text-anchor="end" class="t" font-size="8.5" letter-spacing="1.5" fill="{t["faint"]}">UPDATED {data["date"]} · NASA JPL HORIZONS</text>
</svg>
'''


def main():
    with open(path("data", "mission.json"), encoding="utf-8") as f:
        mission = json.load(f)
    now = dt.datetime.now(dt.timezone.utc)
    local_today = (now + dt.timedelta(hours=mission["timezone_offset_hours"])).date()
    au, rate = voyager1(now.date())
    data = {
        "au": au,
        "rate": rate,
        "date": now.date().isoformat(),
        "service": months_between(mission["launch"], local_today),
        "race": race_line(mission["race"], local_today),
    }
    write_themed("telemetry", lambda t: render(t, data))
    print(json.dumps(data))


if __name__ == "__main__":
    main()
