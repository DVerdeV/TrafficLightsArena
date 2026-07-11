from __future__ import annotations

import argparse
import json
import mimetypes
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / ".arena" / "team.json"
CONTROLLER = ROOT / "controller.py"
DEFAULT_API = os.getenv("TRAFFIC_ARENA_URL", "http://localhost:3000")


def save_token(token: str, base_url: str) -> None:
    CONFIG.parent.mkdir(exist_ok=True)
    CONFIG.write_text(json.dumps({"token": token, "baseUrl": base_url}), encoding="utf-8")


def load_config() -> dict[str, str]:
    if not CONFIG.exists():
        raise SystemExit("Run `python submit.py login YOUR_CODE` first.")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def request_json(url: str, *, token: str, data: bytes | None = None, content_type: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        message = json.loads(exc.read() or b"{}").get("error", exc.reason)
        raise SystemExit(f"Server error ({exc.code}): {message}") from exc


def multipart_file(path: Path) -> tuple[bytes, str]:
    boundary = f"----traffic-arena-{secrets.token_hex(12)}"
    content_type = mimetypes.guess_type(path.name)[0] or "text/plain"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="controller"; filename="{path.name}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            path.read_bytes(),
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    return body, f"multipart/form-data; boundary={boundary}"


def submit() -> None:
    config = load_config()
    body, content_type = multipart_file(CONTROLLER)
    result = request_json(
        f"{config['baseUrl']}/api/v1/submissions",
        token=config["token"],
        data=body,
        content_type=content_type,
    )
    submission_id = result["id"]
    print(f"Queued submission {submission_id[:8]}…")
    while True:
        status = request_json(
            f"{config['baseUrl']}/api/v1/submissions/{submission_id}",
            token=config["token"],
        )
        if status["status"] == "completed":
            print(f"PUBLIC  {status['publicScore']:>8,}")
            print(f"HIDDEN  {status['hiddenScore']:>8,}")
            print(f"TOTAL   {status['totalScore']:>8,}")
            webbrowser.open(f"{config['baseUrl']}/es/replay?submission={submission_id}")
            return
        if status["status"] == "failed":
            raise SystemExit(status.get("errorMessage", "Evaluation failed."))
        time.sleep(1.5)


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit controller.py to Traffic Lights Arena")
    subcommands = parser.add_subparsers(dest="command")
    login = subcommands.add_parser("login")
    login.add_argument("token")
    login.add_argument("--url", default=DEFAULT_API)
    args = parser.parse_args()
    if args.command == "login":
        save_token(args.token.strip().upper(), args.url.rstrip("/"))
        print("Team code saved. Run `python submit.py` when you are ready.")
        return
    submit()


if __name__ == "__main__":
    main()
