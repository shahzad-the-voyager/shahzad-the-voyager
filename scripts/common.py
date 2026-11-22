import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "dark": dict(bg="#0d1117", fg="#e6edf3", muted="#8b949e", faint="#6e7681", line="#30363d", body="#161b22",
                 edge="#8b949e", blue="#58a6ff", red="#ff7b72", star="#c9d1d9"),
    "light": dict(bg="#ffffff", fg="#1f2328", muted="#59636e", faint="#818b98", line="#d0d7de", body="#f6f8fa",
                  edge="#59636e", blue="#0969da", red="#cf222e", star="#57606a"),
}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def path(*parts):
    return os.path.join(ROOT, *parts)


def write_themed(name, render):
    for theme, t in THEMES.items():
        with open(path("assets", f"{name}-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(render(t))
