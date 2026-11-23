import datetime as dt
import json

from common import FONT, esc, path, write_themed

W, H = 960, 412
CELL_X0, CELL_Y = 34, 168
CELL_W, CELL_H = 68, 92


def secs(p):
    m, s = p.split(":")
    return int(m) * 60 + int(s)


def mmss(t):
    t = int(round(t))
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def summarize(run):
    paces = [secs(p) for p in run["splits"]]
    km = run.get("km", float(len(paces)))
    total = run.get("time_s", sum(paces))
    return dict(date=dt.date.fromisoformat(run["date"]), paces=paces,
                gap=[secs(p) for p in run.get("gap", [])], km=km, total=total, avg=total / km)


def bars(x, y, w, h, paces, t, color, labels=False):
    if not paces:
        return ""
    fast, slow = min(paces), max(paces)
    span = max(slow - fast, 1)
    n = len(paces)
    gap = 3 if n < 12 else 1.5
    bw = (w - gap * (n - 1)) / n
    out = []
    for i, p in enumerate(paces):
        frac = 0.35 + 0.65 * (slow - p) / span
        bh = h * frac
        bx = x + i * (bw + gap)
        best = p == fast
        out.append(f'<rect x="{bx:.1f}" y="{y + h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1.5" '
                   f'fill="{t["red"] if best else color}" opacity="{1 if best else .85}"/>')
        if labels:
            out.append(f'<text x="{bx + bw / 2:.1f}" y="{y + h - bh - 8:.1f}" text-anchor="middle" class="t" font-size="11" '
                       f'fill="{t["red"] if best else t["fg"]}">{mmss(p)}</text>')
            out.append(f'<text x="{bx + bw / 2:.1f}" y="{y + h + 16:.1f}" text-anchor="middle" class="t" font-size="9.5" '
                       f'letter-spacing="1" fill="{t["faint"]}">KM {i + 1}</text>')
    return "".join(out)


def render(t, mission, runs, today):
    race = mission["race"]
    race_day = dt.date.fromisoformat(race["date"])
    loop_km = race["loop_km"]
    goal = race["goal_loops"]
    days_left = (race_day - today).days
    by_date = {r["date"]: r for r in runs}
    start = min([r["date"] for r in runs] + [today])
    ndays = (race_day - start).days + 1
    cells = []
    take_no = {r["date"]: i + 1 for i, r in enumerate(sorted(runs, key=lambda r: r["date"]))}
    cw = min(CELL_W, (W - 2 * CELL_X0 - 6 * (ndays - 1)) / ndays)
    for i in range(ndays):
        d = start + dt.timedelta(days=i)
        x = CELL_X0 + i * (cw + 6)
        lbl = d.strftime("%d %b").upper()
        is_today = d == today
        g = [f'<text x="{x + cw / 2:.1f}" y="{CELL_Y - 10}" text-anchor="middle" class="t" font-size="9.5" letter-spacing="1" '
             f'fill="{t["red"] if is_today else t["faint"]}">{lbl}</text>']
        if d == race_day:
            g.append(f'<rect x="{x:.1f}" y="{CELL_Y}" width="{cw:.1f}" height="{CELL_H}" rx="4" fill="{t["red"]}"/>')
            g.append(f'<path d="M {x + cw / 2 - 6:.1f} {CELL_Y + 52} V {CELL_Y + 22} h 15 l -4 5 l 4 5 h -15" fill="{t["bg"]}" stroke="{t["bg"]}" stroke-width="1.4" stroke-linejoin="round"/>')
            g.append(f'<text x="{x + cw / 2:.1f}" y="{CELL_Y + 74}" text-anchor="middle" class="t" font-size="9" font-weight="700" letter-spacing="1.2" fill="{t["bg"]}">MASTER</text>')
        elif d in by_date:
            r = by_date[d]
            g.append(f'<rect x="{x:.1f}" y="{CELL_Y}" width="{cw:.1f}" height="{CELL_H}" rx="4" fill="{t["body"]}" stroke="{t["edge"]}" stroke-width="1.2"/>')
            g.append(bars(x + 8, CELL_Y + 12, cw - 16, 40, r["paces"], t, t["blue"]))
            g.append(f'<text x="{x + cw / 2:.1f}" y="{CELL_Y + 70}" text-anchor="middle" class="t" font-size="11" font-weight="700" fill="{t["fg"]}">{r["km"]:.1f}K</text>')
            g.append(f'<text x="{x + cw / 2:.1f}" y="{CELL_Y + 84}" text-anchor="middle" class="t" font-size="8.5" letter-spacing="1" fill="{t["muted"]}">TAKE {take_no[d]:02d}</text>')
        elif d < today:
            g.append(f'<rect x="{x:.1f}" y="{CELL_Y}" width="{cw:.1f}" height="{CELL_H}" rx="4" fill="none" stroke="{t["line"]}" stroke-width="1.2"/>')
            g.append(f'<text x="{x + cw / 2:.1f}" y="{CELL_Y + 50}" text-anchor="middle" class="t" font-size="9" letter-spacing="1.5" fill="{t["faint"]}">REST</text>')
        else:
            g.append(f'<rect x="{x:.1f}" y="{CELL_Y}" width="{cw:.1f}" height="{CELL_H}" rx="4" fill="none" stroke="{t["faint"]}" stroke-width="1" stroke-dasharray="3 4" opacity=".7"/>')
        if is_today:
            g.append(f'<rect class="now" x="{x:.1f}" y="{CELL_Y + CELL_H + 6}" width="{cw:.1f}" height="2.5" rx="1" fill="{t["red"]}"/>')
        cells.append("".join(g))

    logged = sum(r["km"] for r in runs)
    latest = max(runs, key=lambda r: r["date"]) if runs else None
    best_avg = min((r["avg"] for r in runs), default=None)
    if days_left > 0:
        count, count_lbl = f"T−{days_left}", f"{'DAY' if days_left == 1 else 'DAYS'} TO THE MASTER TAKE"
    elif days_left == 0:
        count, count_lbl = "T−0", "THE MASTER TAKE IS TODAY"
    else:
        count, count_lbl = "DONE", "THE MASTER TAKE IS RECORDED"
    stats = [f"{len(runs)} {'TAKE' if len(runs) == 1 else 'TAKES'} · {logged:.1f} KM LOGGED · {logged / loop_km:.2f} RACE LOOPS"]
    if best_avg:
        loop_t = best_avg * loop_km
        stats.append(f"BEST AVG {mmss(best_avg)} /KM → ONE {loop_km} KM LOOP IN {mmss(loop_t)}")
        stats.append(f"AT THAT PACE: {mmss(3600 - loop_t)} BANKED EVERY HOUR · GOAL {goal} LOOPS")
    stat_svg = "".join(
        f'<text x="300" y="{70 + i * 22}" class="t" font-size="12" letter-spacing="1.2" fill="{t["fg"] if i == 0 else t["muted"]}">{esc(s)}</text>'
        for i, s in enumerate(stats))

    detail = ""
    if latest:
        ld = latest["date"].strftime("%d %b").upper()
        note = ""
        if latest["paces"] and latest["paces"][-1] == min(latest["paces"]) and len(latest["paces"]) > 1:
            note = " · FASTEST KM LAST ▲"
        head = (f'LATEST · TAKE {take_no[latest["date"]]:02d} · {ld} · {latest["km"]:.2f} KM · {mmss(latest["total"])} · '
                f'AVG {mmss(latest["avg"])} /KM{note}')
        gap_txt = ""
        if latest["gap"]:
            gap_txt = "GRADE-ADJUSTED: " + " · ".join(mmss(g) for g in latest["gap"])
        detail = (f'<text x="{CELL_X0}" y="300" class="t" font-size="11" letter-spacing="1.5" fill="{t["muted"]}">{esc(head)}</text>'
                  + bars(CELL_X0, 326, 360, 44, latest["paces"], t, t["blue"], labels=True)
                  + f'<text x="{CELL_X0 + 390}" y="350" class="t" font-size="10" letter-spacing="1" fill="{t["faint"]}">{esc(gap_txt)}</text>'
                  + f'<text x="{CELL_X0 + 390}" y="368" class="t" font-size="10" letter-spacing="1" fill="{t["faint"]}">TALLER BAR = FASTER KM · CORAL = FASTEST</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">B5 recording sessions: training for the backyard ultra</title>
  <desc id="desc">{esc(count)} {esc(count_lbl.lower())}, {race_day.strftime("%d %B %Y")} in {esc(race["place"])}. {esc(". ".join(stats))}. Each training run is a take, shown as bars of its kilometre splits.</desc>
  <style>
    .t {{ font-family: {FONT}; }}
    .now {{ animation: now 1.4s ease-in-out infinite; }}
    @keyframes now {{ 50% {{ opacity: .25; }} }}
    @media (prefers-reduced-motion: reduce) {{ .now {{ animation: none; }} }}
  </style>
  <text x="{CELL_X0}" y="26" class="t" font-size="11" letter-spacing="2.5" fill="{t["muted"]}">TRACK B5 // RECORDING SESSIONS</text>
  <text x="{W - CELL_X0}" y="26" text-anchor="end" class="t" font-size="11" letter-spacing="2" fill="{t["muted"]}">BACKYARD ULTRA · {esc(race["place"].upper())} · {race_day.strftime("%d %b %Y").upper()}</text>
  <text x="{CELL_X0 - 3}" y="104" class="t" font-size="62" font-weight="700" letter-spacing="1" fill="{t["red"]}">{esc(count)}</text>
  <text x="{CELL_X0}" y="128" class="t" font-size="10.5" letter-spacing="2" fill="{t["muted"]}">{esc(count_lbl)}</text>
  {stat_svg}
  {"".join(cells)}
  {detail}
  <text x="{W - CELL_X0}" y="{H - 8}" text-anchor="end" class="t" font-size="8.5" letter-spacing="1.5" fill="{t["faint"]}">EVERY RUN IS A TAKE · UPDATED {today.isoformat()}</text>
</svg>
'''


def main():
    with open(path("data", "mission.json"), encoding="utf-8") as f:
        mission = json.load(f)
    with open(path("data", "training.json"), encoding="utf-8") as f:
        runs = [summarize(r) for r in json.load(f)["runs"]]
    now = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=mission["timezone_offset_hours"])
    today = now.date()
    write_themed("training", lambda t: render(t, mission, runs, today))
    print(json.dumps({"runs": len(runs), "today": today.isoformat()}))


if __name__ == "__main__":
    main()
