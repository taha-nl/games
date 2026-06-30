import os
import re
import subprocess
import sys
import tempfile

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_team
from database import get_db
from models import Challenge, Team

router = APIRouter()

TIMEOUT_SECONDS = 5
MAX_OUTPUT_BYTES = 10_000

BLOCKED_IMPORTS = [
    "os", "sys", "subprocess", "shutil", "socket", "requests",
    "urllib", "http", "ftplib", "smtplib", "telnetlib",
    "importlib", "ctypes", "multiprocessing", "threading",
    "signal", "resource", "pty", "tty", "termios",
    "pickle", "marshal", "shelve",
]

BLOCK_PREAMBLE = """
import builtins as _builtins
_safe_import = _builtins.__import__
_blocked = """ + repr(BLOCKED_IMPORTS) + """
def _guarded_import(name, *args, **kwargs):
    if name.split(".")[0] in _blocked:
        raise ImportError(f"Module '{name}' is not allowed in this sandbox.")
    return _safe_import(name, *args, **kwargs)
_builtins.__import__ = _guarded_import
_real_open = _builtins.open
def _safe_open(file, mode="r", *args, **kwargs):
    if any(c in mode for c in ("w", "a", "x", "+")):
        raise PermissionError("Writing to files is not allowed.")
    return _real_open(file, mode, *args, **kwargs)
_builtins.open = _safe_open
"""

PREAMBLE_LINES = BLOCK_PREAMBLE.count("\n") + 1


def _fix_linenos(stderr: str) -> str:
    def adjust(m):
        return f'line {max(1, int(m.group(1)) - PREAMBLE_LINES)}'
    return re.sub(r'line (\d+)', adjust, stderr)


def _run_once(code: str, test_driver: str) -> dict:
    """
    test_driver: lines appended after user code to call the function and print output.
    e.g. "print(cosmic_sum([1, 2, 3]))"
    """
    full_code = BLOCK_PREAMBLE + "\n" + code
    if test_driver:
        full_code += "\n" + test_driver
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(full_code)
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=tempfile.gettempdir(),
            env={"PATH": "/usr/bin:/bin"},
        )
        return {
            "stdout": result.stdout[:MAX_OUTPUT_BYTES],
            "stderr": _fix_linenos(result.stderr[:MAX_OUTPUT_BYTES]),
            "exit_code": result.returncode,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Time limit exceeded ({TIMEOUT_SECONDS}s). Check for infinite loops.",
            "exit_code": -1,
            "timed_out": True,
        }
    finally:
        os.unlink(tmp)


class RunRequest(BaseModel):
    code: str
    challenge_id: int | None = None


@router.post("/run")
async def run_code(
    body: RunRequest,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    # No test cases: plain run
    if not body.challenge_id:
        result = _run_once(body.code, "")
        return {"mode": "plain", **result}

    challenge = db.query(Challenge).filter(Challenge.id == body.challenge_id).first()
    if not challenge or not challenge.test_cases:
        result = _run_once(body.code, "")
        return {"mode": "plain", **result}

    # Run against each test case
    results = []
    passed = 0
    for tc in challenge.test_cases:
        r = _run_once(body.code, tc.stdin)
        actual = r["stdout"].strip()
        expected = tc.expected_output.strip()
        ok = (not r["timed_out"]) and (r["exit_code"] == 0) and (actual == expected)
        if ok:
            passed += 1
        results.append({
            "id": tc.order_index + 1,
            "passed": ok,
            "stdin": tc.stdin if not tc.is_hidden else None,
            "expected": expected if not tc.is_hidden else None,
            "actual": actual if not tc.is_hidden else None,
            "stderr": r["stderr"] if not tc.is_hidden else None,
            "timed_out": r["timed_out"],
            "is_hidden": tc.is_hidden,
        })

    total = len(results)
    return {
        "mode": "tests",
        "passed": passed,
        "total": total,
        "all_passed": passed == total,
        "results": results,
    }
