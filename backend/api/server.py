# ~/gs_platform/app/server.py
# FastAPI localhost UI for running gaussian-splatting via gs_cli.py

from __future__ import annotations

import os
import re
import json
import time
import shlex
import signal
import threading
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from urllib.parse import quote

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# ---------------- App / Templates ----------------

app = FastAPI()

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# If your templates use {{x|urlq}} to URL-encode query values:
templates.env.filters["urlq"] = lambda s: quote(str(s), safe="")

# ---------------- Config ----------------

JOBS_DIR = BASE_DIR / "jobs_db"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mts", ".m2ts"}

# Restrict browsing to safe roots (tweak if you want)
ALLOWED_BROWSE_ROOTS = [
    Path("/mnt/c"),
    Path("/home"),
    Path("/mnt"),
]

# ---------------- Helpers ----------------


def now_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S") + "_" + os.urandom(4).hex()


def safe_str(s: Optional[str]) -> str:
    return (s or "").strip()


def parse_space_list(s: str) -> List[str]:
    s = safe_str(s)
    if not s:
        return []
    return [tok for tok in re.split(r"\s+", s) if tok.strip()]


def is_checked(v: Optional[str]) -> bool:
    # HTML checkbox sends "on" when checked, and sends nothing when unchecked.
    return v is not None and str(v).strip() != ""


def add_flag(cmd: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        cmd.append(flag)


def ensure_browse_path(p: str) -> Path:
    p = safe_str(p)
    if not p:
        raise HTTPException(400, "Empty path")

    path = Path(p)

    # resolve if possible (don't fail if missing)
    try:
        rp = path.resolve()
    except Exception:
        rp = path

    # must be under allowed roots
    ok = False
    for root in ALLOWED_BROWSE_ROOTS:
        try:
            if str(rp).startswith(str(root)):
                ok = True
                break
        except Exception:
            continue

    if not ok:
        raise HTTPException(403, f"Browsing not allowed: {rp}")

    return rp


def list_dir(cur: Path, mode: str, q: str, video_only: bool) -> Tuple[List[str], List[str], Optional[str]]:
    ql = safe_str(q).lower()
    try:
        if not cur.exists():
            return [], [], f"Path does not exist: {cur}"
        if not cur.is_dir():
            return [], [], f"Not a directory: {cur}"

        dirs: List[str] = []
        files: List[str] = []

        entries = sorted(cur.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            name = entry.name
            if ql and ql not in name.lower():
                continue
            if entry.is_dir():
                dirs.append(name)
            else:
                if mode == "file":
                    if video_only:
                        if entry.suffix.lower() in VIDEO_EXTS:
                            files.append(name)
                    else:
                        files.append(name)

        files = files[:600]
        return dirs, files, None
    except Exception as e:
        return [], [], str(e)


# ---------------- Jobs ----------------

@dataclass
class Job:
    id: str
    created_ts: float
    state: str  # queued / running / done / error / stopped
    pid: Optional[int]
    workspace: str
    gs_repo: str
    video: Optional[str]
    images_dir: Optional[str]
    command: str
    log_path: str
    return_code: Optional[int] = None
    error: Optional[str] = None

    # Template compatibility (some older templates use returncode)
    @property
    def returncode(self) -> Optional[int]:
        return self.return_code


def job_dir(job_id: str) -> Path:
    d = JOBS_DIR / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def job_meta_path(job_id: str) -> Path:
    return job_dir(job_id) / "job.json"


def job_log_path(job_id: str) -> Path:
    return job_dir(job_id) / "live.log"


def save_job(job: Job) -> None:
    job_meta_path(job.id).write_text(json.dumps(asdict(job), indent=2), encoding="utf-8")


def load_job(job_id: str) -> Job:
    p = job_meta_path(job_id)
    if not p.exists():
        raise HTTPException(404, "Job not found")
    data = json.loads(p.read_text(encoding="utf-8"))
    return Job(**data)


def list_jobs() -> List[Job]:
    jobs: List[Job] = []
    for d in sorted(JOBS_DIR.iterdir(), key=lambda p: p.name, reverse=True):
        if not d.is_dir():
            continue
        jp = d / "job.json"
        if not jp.exists():
            continue
        try:
            jobs.append(load_job(d.name))
        except Exception:
            continue
    return jobs


# ---------------- Command builder ----------------

def build_gs_cli_run_cmd(
    *,
    gs_cli_path: Path,
    workspace: str,
    gs_repo: str,
    video: Optional[str],
    images_dir: Optional[str],
    fps: float,
    jpg_quality: int,
    matcher: str,
    overlap: int,
    loop_detection: bool,
    vocab_tree: Optional[str],
    camera_model: str,
    single_camera: bool,
    use_gpu: bool,
    iterations: int,
    save_iters: List[str],
    checkpoint_iters: List[str],
    extra_train_args: str,
    resume: bool,
) -> List[str]:
    v = safe_str(video or "")
    im = safe_str(images_dir or "")

    # XOR rule
    if v and im:
        raise HTTPException(400, "Provide either Video path OR Images dir (not both).")
    if not v and not im:
        raise HTTPException(400, "Provide either Video path OR Images dir.")

    cmd: List[str] = [
        "python",
        str(gs_cli_path),
        "run",
        "--workspace", workspace,
        "--gs-repo", gs_repo,
        "--fps", str(float(fps)),
        "--jpg-quality", str(int(jpg_quality)),
        "--matcher", matcher,
        "--overlap", str(int(overlap)),
        "--iterations", str(int(iterations)),
        "--camera-model", camera_model,
    ]

    if v:
        cmd += ["--video", v]
    else:
        # must match your gs_cli.py flag name
        cmd += ["--images-dir", im]

    # ✅ booleans must be flags only (NO "1")
    add_flag(cmd, "--single-camera", single_camera)
    add_flag(cmd, "--use-gpu", use_gpu)
    add_flag(cmd, "--loop-detection", loop_detection)
    add_flag(cmd, "--resume", resume)

    vt = safe_str(vocab_tree or "")
    if vt:
        cmd += ["--vocab-tree", vt]

    if save_iters:
        cmd += ["--save-iters"] + save_iters

    if checkpoint_iters:
        cmd += ["--checkpoint-iters"] + checkpoint_iters

    extra = safe_str(extra_train_args)
    if extra:
        cmd += ["--extra-train-args", extra]

    return cmd


# ---------------- Process runner ----------------

def spawn_job(job: Job, cmd_list: List[str]) -> None:
    log_path = Path(job.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def _runner():
        nonlocal job
        job.state = "running"
        save_job(job)

        with log_path.open("a", encoding="utf-8", errors="replace") as lf:
            lf.write("=" * 34 + "\n")
            lf.write(f"CMD: {job.command}\n")
            lf.write("=" * 46 + "\n")
            lf.flush()

            try:
                proc = subprocess.Popen(
                    cmd_list,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    preexec_fn=os.setsid,  # kill process group on stop
                )
                job.pid = proc.pid
                save_job(job)

                assert proc.stdout is not None
                for line in proc.stdout:
                    lf.write(line)
                    lf.flush()

                rc = proc.wait()
                job.return_code = rc

                if job.state == "stopped":
                    # stop handler already set state
                    pass
                elif rc == 0:
                    job.state = "done"
                else:
                    job.state = "error"
                    job.error = f"Process exited with code {rc}"

                save_job(job)

            except Exception as e:
                job.state = "error"
                job.error = str(e)
                save_job(job)
                lf.write(f"\n[SERVER ERROR] {e}\n")
                lf.flush()

    t = threading.Thread(target=_runner, daemon=True)
    t.start()


# ---------------- Routes ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "video_exts": ", ".join(sorted(VIDEO_EXTS)),
        },
    )


@app.get("/jobs", response_class=HTMLResponse)
def jobs_partial(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="_jobs.html",
        context={"jobs": list_jobs()},
    )


@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_page(request: Request, job_id: str):
    job = load_job(job_id)

    # Build meta the way your job.html expects: meta.args.* and meta.cmd list
    cmd_list: List[str] = []
    args_map: Dict[str, Any] = {}
    try:
        if job.command:
            cmd_list = shlex.split(job.command)

        i = 0
        while i < len(cmd_list):
            tok = cmd_list[i]
            if tok.startswith("--"):
                key = tok.lstrip("-").replace("-", "_")
                if i + 1 >= len(cmd_list) or cmd_list[i + 1].startswith("--"):
                    args_map[key] = True
                    i += 1
                else:
                    args_map[key] = cmd_list[i + 1]
                    i += 2
            else:
                i += 1

        args_map.setdefault("workspace", job.workspace)
        args_map.setdefault("gs_repo", job.gs_repo)
        args_map.setdefault("video", job.video)
        args_map.setdefault("images_dir", job.images_dir)
    except Exception:
        args_map = {
            "workspace": job.workspace,
            "gs_repo": job.gs_repo,
            "video": job.video,
            "images_dir": job.images_dir,
        }

    meta = {"args": args_map, "cmd": cmd_list}

    # ✅ Pass both "job" and "status" so old templates don't crash
    return templates.TemplateResponse(
        request=request,
        name="job.html",
        context={
            "job_id": job_id,
            "job": job,
            "status": job,
            "meta": meta,
        },
    )


@app.get("/job/{job_id}/log", response_class=PlainTextResponse)
def job_log(job_id: str, tail: int = 6000):
    job = load_job(job_id)
    p = Path(job.log_path)
    if not p.exists():
        return PlainTextResponse("")
    data = p.read_text(encoding="utf-8", errors="replace")
    if tail > 0 and len(data) > tail:
        data = data[-tail:]
    return PlainTextResponse(data)


@app.post("/job/{job_id}/stop")
def stop_job(job_id: str):
    job = load_job(job_id)

    if job.pid is None:
        job.state = "stopped"
        save_job(job)
        return JSONResponse({"ok": True, "state": job.state})

    try:
        os.killpg(job.pid, signal.SIGTERM)
        job.state = "stopped"
        save_job(job)
        return JSONResponse({"ok": True, "state": job.state})
    except ProcessLookupError:
        job.state = "stopped"
        save_job(job)
        return JSONResponse({"ok": True, "state": job.state})
    except Exception as e:
        job.error = str(e)
        save_job(job)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/browse", response_class=HTMLResponse)
def browse(
    request: Request,
    target: str,
    mode: str = "dir",
    path: str = "/mnt/c",
    q: str = "",
):
    target = safe_str(target)
    mode = safe_str(mode)

    allowed_targets = {"workspace", "video", "images_dir", "vocab_tree", "gs_repo"}
    if target not in allowed_targets:
        raise HTTPException(400, "bad target")
    if mode not in {"dir", "file"}:
        raise HTTPException(400, "bad mode")

    cur = ensure_browse_path(path)
    if not cur.is_dir():
        cur = cur.parent

    parent = str(cur.parent) if cur.parent != cur else str(cur)
    video_only = (target == "video" and mode == "file")

    dirs, files, error = list_dir(cur, mode, q, video_only)

    return templates.TemplateResponse(
        request=request,
        name="_browse_modal.html",
        context={
            "target": target,
            "mode": mode,
            "cur": str(cur),
            "parent": parent,
            "dirs": dirs,
            "files": files,
            "q": q,
            "video_only": video_only,
            "video_exts": ", ".join(sorted(VIDEO_EXTS)),
            "error": error,
        },
    )


@app.post("/browse/mkdir", response_class=HTMLResponse)
def browse_mkdir(
    request: Request,
    # Support both old and new modal implementations:
    # new modal: sends path + name via fetch()
    # old modal: sends cur + name + target + mode + q
    path: Optional[str] = Form(None),
    cur: Optional[str] = Form(None),
    name: str = Form(...),
    target: str = Form("workspace"),
    mode: str = Form("dir"),
    q: str = Form(""),
):
    target = safe_str(target) or "workspace"
    mode = safe_str(mode) or "dir"
    name = safe_str(name)

    if target not in {"workspace", "video", "images_dir", "vocab_tree", "gs_repo"}:
        raise HTTPException(400, "bad target")
    if mode not in {"dir", "file"}:
        raise HTTPException(400, "bad mode")

    base_path = safe_str(path or cur or "")
    base = ensure_browse_path(base_path) if base_path else ensure_browse_path("/mnt/c")

    if not base.exists() or not base.is_dir():
        raise HTTPException(400, "current folder does not exist")

    if not name:
        return browse(request, target=target, mode=mode, path=str(base), q=q)

    if "/" in name or "\\" in name or name in {".", ".."}:
        return browse(request, target=target, mode=mode, path=str(base), q=q)

    newp = base / name
    err: Optional[str] = None
    try:
        newp.mkdir(parents=False, exist_ok=False)
    except FileExistsError:
        err = "Folder already exists"
    except Exception as e:
        err = str(e)

    # Re-render modal at same folder
    cur = base
    parent = str(cur.parent) if cur.parent != cur else str(cur)
    video_only = (target == "video" and mode == "file")
    dirs, files, _ = list_dir(cur, mode, q, video_only)

    return templates.TemplateResponse(
        request=request,
        name="_browse_modal.html",
        context={
            "target": target,
            "mode": mode,
            "cur": str(cur),
            "parent": parent,
            "dirs": dirs,
            "files": files,
            "q": q,
            "video_only": video_only,
            "video_exts": ", ".join(sorted(VIDEO_EXTS)),
            "error": err,
        },
    )


@app.post("/run")
def run_job(
    request: Request,
    # paths
    workspace: str = Form(...),
    gs_repo: str = Form(...),
    video: str = Form(""),
    images_dir: str = Form(""),
    vocab_tree: str = Form(""),
    # extraction
    fps: str = Form("2"),
    jpg_quality: str = Form("2"),
    # colmap
    matcher: str = Form("sequential"),
    overlap: str = Form("20"),
    loop_detection: Optional[str] = Form(None),
    camera_model: str = Form("SIMPLE_RADIAL"),
    single_camera: Optional[str] = Form(None),
    use_gpu: Optional[str] = Form(None),
    # training
    iterations: str = Form("30000"),
    save_iters: str = Form("7000 10000 15000 20000 30000"),
    checkpoint_iters: str = Form(""),
    extra_train_args: str = Form(""),
    resume: Optional[str] = Form(None),
):
    ws = safe_str(workspace)
    gr = safe_str(gs_repo)

    if not ws:
        raise HTTPException(400, "workspace is required")
    if not gr:
        raise HTTPException(400, "gs_repo is required")

    gs_cli_path = Path(gr) / "gs_cli.py"
    if not gs_cli_path.exists():
        raise HTTPException(400, f"gs_cli.py not found at {gs_cli_path}")

    try:
        fps_f = float(fps)
        jq_i = int(jpg_quality)
        overlap_i = int(overlap)
        it_i = int(iterations)
    except Exception:
        raise HTTPException(400, "Bad numeric value")

    save_list = parse_space_list(save_iters)
    ckpt_list = parse_space_list(checkpoint_iters)

    loop_b = is_checked(loop_detection)
    single_b = is_checked(single_camera)
    gpu_b = is_checked(use_gpu)
    resume_b = is_checked(resume)

    cmd_list = build_gs_cli_run_cmd(
        gs_cli_path=gs_cli_path,
        workspace=ws,
        gs_repo=gr,
        video=safe_str(video) or None,
        images_dir=safe_str(images_dir) or None,
        fps=fps_f,
        jpg_quality=jq_i,
        matcher=safe_str(matcher) or "sequential",
        overlap=overlap_i,
        loop_detection=loop_b,
        vocab_tree=safe_str(vocab_tree) or None,
        camera_model=safe_str(camera_model) or "SIMPLE_RADIAL",
        single_camera=single_b,
        use_gpu=gpu_b,
        iterations=it_i,
        save_iters=save_list,
        checkpoint_iters=ckpt_list,
        extra_train_args=extra_train_args,
        resume=resume_b,
    )

    cmd_str = " ".join(shlex.quote(x) for x in cmd_list)

    job_id = now_id()
    lp = job_log_path(job_id)

    job = Job(
        id=job_id,
        created_ts=time.time(),
        state="queued",
        pid=None,
        workspace=ws,
        gs_repo=gr,
        video=safe_str(video) or None,
        images_dir=safe_str(images_dir) or None,
        command=cmd_str,
        log_path=str(lp),
    )
    save_job(job)

    spawn_job(job, cmd_list)

    return RedirectResponse(url=f"/job/{job_id}", status_code=303)