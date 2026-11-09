"""Local browser interface for the fixed CrewAI equity-research Flow."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Equity Research Agent Team</title>
  <style>
    :root { color-scheme: light; --ink:#14213d; --muted:#5f6b7a; --line:#d9e2ec; --blue:#175cd3; --paper:#fff; --wash:#f5f8fc; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif; color:var(--ink); background:linear-gradient(135deg,#eef4ff,#f9fbff 55%,#eefaf5); }
    main { width:min(1120px,calc(100% - 32px)); margin:32px auto 64px; }
    header { margin-bottom:22px; }
    h1 { margin:0 0 8px; font-size:clamp(2rem,5vw,3.4rem); letter-spacing:-.04em; }
    header p { margin:0; color:var(--muted); font-size:1.05rem; }
    .card { background:rgba(255,255,255,.94); border:1px solid var(--line); border-radius:18px; box-shadow:0 18px 50px rgba(27,55,96,.09); padding:22px; margin-top:18px; }
    form { display:grid; grid-template-columns:1fr 2fr 1fr auto; gap:12px; align-items:end; }
    label { display:grid; gap:7px; font-weight:700; font-size:.88rem; }
    input { width:100%; border:1px solid #b9c7d8; border-radius:10px; padding:12px; font:inherit; background:#fff; }
    input:focus { outline:3px solid #cfe0ff; border-color:var(--blue); }
    button { border:0; border-radius:10px; padding:13px 20px; background:var(--blue); color:#fff; font:inherit; font-weight:800; cursor:pointer; }
    button:disabled { opacity:.55; cursor:wait; }
    .status { display:flex; flex-wrap:wrap; gap:8px; min-height:34px; }
    .node { border:1px solid #a9c6f7; color:#124a9c; background:#eef5ff; border-radius:999px; padding:7px 11px; font-weight:750; font-size:.84rem; }
    .node:last-child { background:#eaf8ef; border-color:#9ed5ad; color:#176b36; }
    pre { white-space:pre-wrap; overflow-wrap:anywhere; margin:0; font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }
    #log { max-height:260px; overflow:auto; color:#344054; background:var(--wash); border-radius:12px; padding:14px; }
    #report { max-height:720px; overflow:auto; }
    .row { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:12px; }
    .row h2 { margin:0; font-size:1.12rem; }
    #path { color:var(--muted); font-size:.85rem; overflow-wrap:anywhere; text-align:right; }
    .error { color:#a11313; background:#fff1f0; border:1px solid #ffc9c5; border-radius:10px; padding:12px; }
    @media (max-width:820px) { form { grid-template-columns:1fr 1fr; } button { width:100%; } }
    @media (max-width:540px) { form { grid-template-columns:1fr; } main { width:min(100% - 20px,1120px); margin-top:18px; } }
  </style>
</head>
<body>
<main>
  <header>
    <h1>Equity Research Agent Team</h1>
    <p>Run the fixed graph, watch every node, and read the evidence marks.</p>
  </header>
  <section class="card">
    <form id="run-form">
      <label>Ticker <input id="ticker" placeholder="Ticker" required maxlength="10" autocomplete="off"></label>
      <label>Peers (optional) <input id="peers" placeholder="PEER1,PEER2,PEER3" autocomplete="off"></label>
      <label>Price (optional) <input id="price" placeholder="123.45" inputmode="decimal"></label>
      <button id="run" type="submit">Run team</button>
    </form>
  </section>
  <section class="card">
    <div class="row"><h2>Fixed node order</h2><span id="state">Ready</span></div>
    <div class="status" id="nodes"></div>
  </section>
  <section class="card">
    <div class="row"><h2>Run log</h2></div>
    <pre id="log">No run started.</pre>
  </section>
  <section class="card">
    <div class="row"><h2>Verified report</h2><span id="path"></span></div>
    <pre id="report">The verified report will appear here.</pre>
  </section>
</main>
<script>
const form=document.querySelector('#run-form'), run=document.querySelector('#run');
const nodes=document.querySelector('#nodes'), log=document.querySelector('#log');
const report=document.querySelector('#report'), state=document.querySelector('#state'), path=document.querySelector('#path');
function appendLog(text){ if(log.textContent==='No run started.') log.textContent=''; log.textContent+=text+'\n'; log.scrollTop=log.scrollHeight; }
form.addEventListener('submit',async(event)=>{
  event.preventDefault(); run.disabled=true; nodes.textContent=''; log.textContent=''; report.textContent='Waiting for the Verifier…'; path.textContent=''; state.textContent='Running';
  const payload={ticker:document.querySelector('#ticker').value,peers:document.querySelector('#peers').value,price:document.querySelector('#price').value};
  try {
    const response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(!response.ok) throw new Error(await response.text());
    const reader=response.body.getReader(), decoder=new TextDecoder(); let buffer='';
    while(true){ const {value,done}=await reader.read(); buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});
      const lines=buffer.split('\n'); buffer=lines.pop();
      for(const line of lines){ if(!line) continue; const event=JSON.parse(line);
        if(event.type==='node'){ const item=document.createElement('span'); item.className='node'; item.textContent=event.name; nodes.appendChild(item); }
        else if(event.type==='log') appendLog(event.text);
        else if(event.type==='report'){ report.textContent=event.content; path.textContent=event.path; }
        else if(event.type==='done'){ state.textContent=event.exit_code===0?'Complete':'Stopped with an error'; }
        else if(event.type==='error'){ appendLog(event.message); state.textContent='Error'; }
      }
      if(done) break;
    }
  } catch(error){ log.className='error'; log.textContent=String(error); state.textContent='Error'; }
  finally { run.disabled=false; }
});
</script>
</body>
</html>
"""


def validate_payload(value: dict[str, Any]) -> tuple[str, str, float | None]:
    ticker = str(value.get("ticker", "")).strip().upper()
    if not TICKER_RE.fullmatch(ticker):
        raise ValueError("Enter a valid U.S. ticker symbol.")
    peers_list = [part.strip().upper() for part in str(value.get("peers", "")).split(",") if part.strip()]
    if any(not TICKER_RE.fullmatch(peer) for peer in peers_list):
        raise ValueError("Enter peers as comma-separated ticker symbols.")
    raw_price = str(value.get("price", "")).strip()
    price = float(raw_price) if raw_price else None
    if price is not None and price <= 0:
        raise ValueError("Price must be greater than zero.")
    return ticker, ",".join(peers_list), price


class AgentTeamHandler(BaseHTTPRequestHandler):
    server_version = "AgentTeamUI/1.0"

    def log_message(self, format_string: str, *args: object) -> None:
        print(format_string % args)

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _event(self, event: dict[str, Any]) -> None:
        self.wfile.write((json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8"))
        self.wfile.flush()

    def do_POST(self) -> None:
        if self.path != "/api/run":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 20_000:
                raise ValueError("Request is too large.")
            value = json.loads(self.rfile.read(length).decode("utf-8"))
            ticker, peers, price = validate_payload(value)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return

        command = [sys.executable, str(ROOT / "crewai_flow.py"), ticker]
        if peers:
            command.extend(["--peers", peers])
        if price is not None:
            command.extend(["--price", str(price)])

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        started = time.time()
        try:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert process.stdout is not None
            for raw_line in process.stdout:
                line = raw_line.rstrip()
                if line.startswith("Node: "):
                    self._event({"type": "node", "name": line.removeprefix("Node: ")})
                self._event({"type": "log", "text": line})
            exit_code = process.wait()
            candidates = [
                folder
                for folder in (ROOT / "outputs").glob(f"{ticker}_*")
                if folder.is_dir() and folder.stat().st_mtime >= started - 2
            ]
            if candidates:
                latest = max(candidates, key=lambda folder: folder.stat().st_mtime)
                verified_report = latest / "verified_report.md"
                if verified_report.exists():
                    self._event(
                        {
                            "type": "report",
                            "path": str(verified_report.relative_to(ROOT)),
                            "content": verified_report.read_text(encoding="utf-8"),
                        }
                    )
            self._event({"type": "done", "exit_code": exit_code})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:  # The browser must receive the exact run error.
            self._event({"type": "error", "message": f"{type(exc).__name__}: {exc}"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), AgentTeamHandler)
    print(f"Agent Team page: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
