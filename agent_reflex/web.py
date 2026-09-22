from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from .config import CONFIG_KEYS, SECRET_KEYS, config_path, load_config, masked_value, save_config
from .providers import decide_with_provider

HOST = "127.0.0.1"
PORT = 8765


class AgentReflexWebHandler(BaseHTTPRequestHandler):
    server_version = "AgentReflexWeb/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/health"):
            self._json({"ok": True, "config_path": str(config_path())})
            return
        if self.path == "/" or self.path.startswith("/?"):
            self._html(render_page(load_config()))
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        form = {key: values[-1] for key, values in parse_qs(raw, keep_blank_values=True).items()}
        if self.path.startswith("/save"):
            current = load_config()
            values = dict(current)
            if "AGENT_REFLEX_HERMES_AUTO_ENABLED" not in form:
                values["AGENT_REFLEX_HERMES_AUTO_ENABLED"] = "false"
            for key in CONFIG_KEYS:
                if key not in form:
                    continue
                value = form[key].strip()
                if key in SECRET_KEYS and not value:
                    continue
                if value:
                    values[key] = value
                else:
                    values.pop(key, None)
            path = save_config(values)
            self._html(render_page(load_config(), notice=f"Saved config to {path}"))
            return
        if self.path.startswith("/test"):
            task = form.get("task", "Publish the homepage update to production and verify it.").strip()
            kind = form.get("kind", "risk").strip() or "risk"
            provider = form.get("provider", "auto").strip() or "auto"
            if kind == "preflight":
                from .hermes.auto import preflight

                result = preflight({"task": task}, provider, force=True)
            else:
                result = decide_with_provider(kind, {"task": task}, provider)
            self._html(render_page(load_config(), notice="Test decision complete", result=result))
            return
        self.send_error(404, "Not found")

    def log_message(self, format: str, *args: object) -> None:
        print(f"agent-reflex-web: {self.address_string()} - {format % args}")

    def _html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _json(self, payload: dict[str, object], status: int = 200) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def render_page(config: dict[str, object], notice: str | None = None, result: dict[str, object] | None = None) -> str:
    field_html = "\n".join(render_field(key, config.get(key, "")) for key in CONFIG_KEYS)
    result_html = ""
    if result is not None:
        result_html = f"""
        <section class="panel">
          <h2>Decision result</h2>
          <pre><code>{html.escape(json.dumps(result, indent=2, sort_keys=True))}</code></pre>
        </section>
        """
    notice_html = f'<p class="notice">{html.escape(notice)}</p>' if notice else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Reflex Local Config</title>
  <style>{CSS}</style>
</head>
<body>
  <main>
    <header>
      <p class="eyebrow">Local control panel</p>
      <h1>Agent Reflex Configuration</h1>
      <p class="lead">Configure provider policy, automatic Hermes preflight, local Cactus, Jev/TypeSafe, and OpenAI-compatible endpoints without hand-editing environment variables.</p>
      <p class="path">Config file: <code>{html.escape(str(config_path()))}</code></p>
      {notice_html}
    </header>

    <section class="grid">
      <article><strong>Provider-neutral</strong><span>Use rules, Cactus, Jev, OpenAI-compatible APIs, or auto policy.</span></article>
      <article><strong>Fail-safe</strong><span>Rules remain the fallback and risk guardrail.</span></article>
      <article><strong>Local-first ready</strong><span>Cactus can run locally when available.</span></article>
    </section>

    <form method="post" action="/save" class="panel">
      <h2>Provider configuration</h2>
      {field_html}
      <button type="submit">Save configuration</button>
    </form>

    <form method="post" action="/test" class="panel">
      <h2>Test a decision</h2>
      <label>Decision kind
        <select name="kind">
          <option>preflight</option><option>risk</option><option>route</option><option>skill</option><option>memory</option><option>validate</option>
        </select>
      </label>
      <label>Provider
        <select name="provider">
          <option>auto</option><option>rules</option><option>cactus</option><option>jev</option><option>openai-compatible</option>
        </select>
      </label>
      <label>Task
        <textarea name="task">Publish the IT Rockstar homepage update to the live production website and verify it.</textarea>
      </label>
      <button type="submit">Run test decision</button>
    </form>

    {result_html}
  </main>
</body>
</html>"""


def render_field(key: str, value: object) -> str:
    if key == "AGENT_REFLEX_HERMES_AUTO_ENABLED":
        checked = " checked" if str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"} else ""
        return f"""<label class="checkbox"><span>{html.escape(key)}</span>
      <input name="{html.escape(key)}" type="checkbox" value="true"{checked}>
      <small>When enabled, Hermes sessions that load the Agent Reflex skill should run <code>agent-reflex preflight</code> before risky or routed work.</small>
    </label>"""
    display = masked_value(key, value)
    input_type = "password" if key in SECRET_KEYS else "text"
    placeholder = "leave blank to keep existing secret" if key in SECRET_KEYS and value else ""
    return f"""<label>{html.escape(key)}
      <input name="{html.escape(key)}" type="{input_type}" value="{html.escape(display if key not in SECRET_KEYS else '')}" placeholder="{html.escape(placeholder)}">
    </label>"""


CSS = """
:root { color-scheme: dark; --bg:#0b0d12; --panel:#141824; --ink:#f4f7fb; --muted:#aab4c5; --red:#ef4444; --line:#283044; }
* { box-sizing: border-box; }
body { margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: radial-gradient(circle at top left, #2a1014, transparent 32rem), var(--bg); color:var(--ink); line-height:1.5; }
main { max-width:1120px; margin:0 auto; padding:3rem 1.25rem; }
h1 { font-size: clamp(2.4rem, 7vw, 5rem); line-height:.95; margin:.2rem 0 1rem; }
h2 { margin-top:0; }
.eyebrow { color:var(--red); font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
.lead, .path, article span { color:var(--muted); }
.notice { background:#14351f; border:1px solid #2d6d3f; border-radius:.8rem; padding:.8rem 1rem; }
.grid { display:grid; gap:1rem; grid-template-columns: repeat(3, minmax(0, 1fr)); margin:2rem 0 1rem; }
article, .panel { background: color-mix(in srgb, var(--panel), transparent 8%); border:1px solid var(--line); border-radius:1.25rem; padding:1.25rem; }
article { display:grid; gap:.35rem; }
.panel { margin-top:1rem; }
label { display:grid; gap:.35rem; margin: .85rem 0; color: var(--muted); font-weight:700; }
input, select, textarea { width:100%; border:1px solid var(--line); border-radius:.8rem; background:#070910; color:var(--ink); padding:.8rem; font:inherit; }
.checkbox { grid-template-columns: auto 1fr; align-items:center; background:#101420; border:1px solid var(--line); border-radius:.9rem; padding:.8rem; }
.checkbox input { width:auto; transform: scale(1.2); }
.checkbox span, .checkbox small { grid-column: 2; }
.checkbox small { color:var(--muted); font-weight:500; }
textarea { min-height:7rem; }
button { background:var(--red); border:0; border-radius:999px; color:white; cursor:pointer; font-weight:800; padding:.8rem 1.15rem; }
pre { background:#070910; border:1px solid var(--line); border-radius:.9rem; overflow-x:auto; padding:1rem; }
code { color:#e9eef7; }
@media (max-width:760px) { .grid { grid-template-columns:1fr; } }
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-reflex-web", description="Local Agent Reflex configuration UI")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), AgentReflexWebHandler)
    print(f"Agent Reflex web UI running at http://{args.host}:{args.port}")
    print(f"Config file: {config_path()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
