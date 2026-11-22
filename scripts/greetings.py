import datetime as dt
import json
import os
import re
import unicodedata

from common import path

REPO = "shahzad-the-voyager/shahzad-the-voyager"
START, END = "<!-- GREETINGS:START -->", "<!-- GREETINGS:END -->"
SHOW = 8
ALLOWED_PUNCT = set(" .,!?'’-:;()")


def clean(text, limit):
    text = unicodedata.normalize("NFC", text or "").strip()
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] in "LNM" or ch in ALLOWED_PUNCT:
            out.append(ch)
        elif ch.isspace():
            out.append(" ")
    text = re.sub(r"\s+", " ", "".join(out)).strip()
    return text[:limit].strip()


def field(body, label):
    m = re.search(rf"###\s*{label}\s*\n+(.+?)(?:\n###|\Z)", body or "", re.S)
    value = m.group(1).strip() if m else ""
    return "" if value == "_No response_" else value


def load():
    p = path("data", "greetings.json")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(items):
    with open(path("data", "greetings.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")


def block(items):
    langs = len({i["language"].casefold() for i in items})
    link = f"https://github.com/{REPO}/issues/new?template=greeting.yml"
    head = (f"**Greetings from Earth** · {len(items)} received · {langs} "
            f"{'language' if langs == 1 else 'languages'} · [add yours →]({link})")
    if not items:
        return head + "\n\n<sub>The first slot on the record is still open.</sub>"
    rows = ["| Language | Greeting | From |", "| :-- | :-- | :-- |"]
    for i in sorted(items, key=lambda i: i["date"], reverse=True)[:SHOW]:
        rows.append(f"| {i['language']} | {i['greeting']} | [{i['user']}](https://github.com/{i['user']}) |")
    return head + "\n\n" + "\n".join(rows)


def render_readme(items):
    p = path("README.md")
    with open(p, encoding="utf-8") as f:
        s = f.read()
    a, b = s.index(START) + len(START), s.index(END)
    s = s[:a] + "\n" + block(items) + "\n" + s[b:]
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def output(**kv):
    target = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in kv.items())
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.write(lines)
    print(lines, end="")


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        event = json.load(f)
    issue = event["issue"]
    body = issue.get("body") or ""
    user = issue["user"]["login"]
    language = clean(field(body, "Language"), 24)
    greeting = clean(field(body, "Greeting"), 80)
    raw = field(body, "Greeting").lower()
    if not language or not greeting:
        return output(accepted="false", reason="empty")
    if "http" in raw or "www." in raw or "@" in raw:
        return output(accepted="false", reason="links")
    items = [i for i in load() if i["user"].lower() != user.lower()]
    items.append({"language": language, "greeting": greeting, "user": user,
                  "date": dt.datetime.now(dt.timezone.utc).date().isoformat()})
    save(items)
    render_readme(items)
    output(accepted="true", reason="ok")


if __name__ == "__main__":
    main()
