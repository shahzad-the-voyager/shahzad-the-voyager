import datetime as dt
import hashlib
import json
import os
import urllib.request

from common import FONT, esc, write_themed

LOGIN = os.environ.get("PROFILE_LOGIN", "shahzad-the-voyager")
W, H = 960, 250
GX0, GY0 = 34, 52
CW, CH = 17.2, 22
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
QUERY = """query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar {
  totalContributions weeks { contributionDays { date contributionCount contributionLevel } } } } } }"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-constellation"})
    with urllib.request.urlopen(req, timeout=60) as r:
        cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], cal["weeks"]


def jitter(date, k):
    h = hashlib.sha256(f"{date}{k}".encode()).digest()
    return (h[0] / 255 - 0.5), (h[1] / 255 - 0.5)


def render(t, total, weeks, updated):
    dust, stars, links, months = [], [], [], []
    brightest = None
    prev = None
    last_month = None
    if weeks and weeks[0]["contributionDays"]:
        last_month = dt.date.fromisoformat(weeks[0]["contributionDays"][0]["date"]).month
    for wi, week in enumerate(weeks):
        best = None
        for day in week["contributionDays"]:
            d = dt.date.fromisoformat(day["date"])
            jx, jy = jitter(day["date"], 0)
            x = GX0 + wi * CW + CW / 2 + jx * CW * 0.7
            y = GY0 + d.isoweekday() % 7 * CH + CH / 2 + jy * CH * 0.6
            lvl = LEVELS.get(day["contributionLevel"], 0)
            n = day["contributionCount"]
            if lvl == 0:
                dust.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r=".7"/>')
                continue
            r = 0.9 + lvl * 0.7
            stars.append((x, y, r, lvl, day["date"], n))
            if best is None or n > best[5]:
                best = (x, y, r, lvl, day["date"], n)
            if brightest is None or n > brightest[5]:
                brightest = (x, y, r, lvl, day["date"], n)
        if week["contributionDays"]:
            first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
            if first.month != last_month and wi > 1:
                last_month = first.month
                months.append(f'<text x="{GX0 + wi * CW:.1f}" y="{GY0 + 7 * CH + 18}" class="t" font-size="9" letter-spacing="1.5" fill="{t["faint"]}">{first.strftime("%b").upper()}</text>')
        if best:
            if prev and wi - prev[0] <= 2:
                links.append(f'<line x1="{prev[1]:.1f}" y1="{prev[2]:.1f}" x2="{best[0]:.1f}" y2="{best[1]:.1f}"/>')
            prev = (wi, best[0], best[1])
    star_svg = []
    for x, y, r, lvl, date, n in stars:
        is_top = brightest and date == brightest[4]
        cls = ' class="tw"' if lvl >= 3 and not is_top else ""
        fill = t["red"] if is_top else t["star"]
        star_svg.append(f'<circle{cls} cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{0.45 + lvl * 0.13:.2f}"/>')
    label = ""
    if brightest:
        x, y = brightest[0], brightest[1]
        anchor = "end" if x > W - 220 else "start"
        tx = x - 10 if anchor == "end" else x + 10
        bd = dt.date.fromisoformat(brightest[4]).strftime("%d %b %Y").upper()
        label = (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{brightest[2] + 5:.1f}" fill="none" stroke="{t["red"]}" stroke-width="1" opacity=".6"/>'
                 f'<text x="{tx:.1f}" y="{y - 8:.1f}" text-anchor="{anchor}" class="t" font-size="9.5" letter-spacing="1.5" fill="{t["red"]}">α SA · {bd} · {brightest[5]}</text>')
    lit = len(stars)
    sky = "A YOUNG SKY" if lit < 30 else "STILL MAPPING"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">Constellation SA: a year of contributions as a star chart</title>
  <desc id="desc">Every day of the last year on this GitHub account drawn as a star, brighter on busier days, with the busiest day of each week joined into a constellation. {total} contributions over {lit} active days. Updated {updated}.</desc>
  <style>
    .t {{ font-family: {FONT}; }}
    .tw {{ animation: tw 4s ease-in-out infinite; }}
    .tw:nth-of-type(3n) {{ animation-delay: 1.3s; }} .tw:nth-of-type(3n+1) {{ animation-delay: 2.6s; }}
    @keyframes tw {{ 50% {{ opacity: .25; }} }}
    @media (prefers-reduced-motion: reduce) {{ .tw {{ animation: none; }} }}
  </style>
  <text x="{GX0}" y="26" class="t" font-size="11" letter-spacing="2.5" fill="{t["muted"]}">CONSTELLATION SA // LAST 365 DAYS</text>
  <text x="{W - GX0}" y="26" text-anchor="end" class="t" font-size="11" letter-spacing="2" fill="{t["muted"]}">{total} CONTRIBUTIONS · {lit} STARS · {sky}</text>
  <g fill="{t["faint"]}" opacity=".35">{"".join(dust)}</g>
  <g stroke="{t["blue"]}" stroke-width="1" opacity=".55">{"".join(links)}</g>
  {"".join(star_svg)}
  {label}
  {"".join(months)}
  <text x="{W - GX0}" y="{H - 6}" text-anchor="end" class="t" font-size="8.5" letter-spacing="1.5" fill="{t["faint"]}">ONE STAR PER DAY · UPDATED {esc(updated)}</text>
</svg>
'''


def main():
    total, weeks = fetch()
    updated = dt.datetime.now(dt.timezone.utc).date().isoformat()
    write_themed("constellation", lambda t: render(t, total, weeks, updated))
    print(json.dumps({"total": total, "weeks": len(weeks)}))


if __name__ == "__main__":
    main()
