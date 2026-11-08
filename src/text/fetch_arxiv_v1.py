"""Phase 1: fetch arXiv v1 source packages one paper at a time and keep only the text-bearing parts.

Runs in tmux on an internet-connected login node (Slurm compute nodes are offline). For each ID it
downloads https://arxiv.org/e-print/<id>v1 at no more than one request per DELAY seconds and stores:
  - LaTeX submissions: the .tex/.ltx/.bbl members, repacked as <id>.tex.tar.gz (figures dropped);
  - PDF-only submissions: text extracted with PyMuPDF, stored as <id>.pdf.txt.gz (PDF dropped).
LaTeX-to-text conversion happens later, offline, so the parsing rule can be fixed in the pilot
without re-downloading. Archives are read in memory; nothing from them is written as a path.

Every attempt is logged to manifest.jsonl in the output directory. A rerun skips IDs whose last
record is final (ok, or a permanent HTTP error), so the job resumes after an interrupted session.

Usage:
    python -I fetch_arxiv_v1.py ID_LIST OUT_DIR [--delay 3] [--limit N]
ID_LIST has one arXiv ID per line (header 'arxiv_id' allowed).
"""

import argparse
import gzip
import hashlib
import io
import json
import os
import sys
import tarfile
import time

import requests

USER_AGENT = "oaai-research-pilot/0.1 (Princeton research use; one request per 3 s)"
TEXT_EXT = (".tex", ".ltx", ".bbl")
MAX_MEMBER = 20 * 2**20   # skip any single text member above 20 MB
PERMANENT = {400, 404, 410}


def shard_dir(out_dir, arxiv_id):
    key = arxiv_id.replace("/", "_")
    sub = os.path.join(out_dir, key.split(".")[0] if "." in key else key[:-3])
    os.makedirs(sub, exist_ok=True)
    return os.path.join(sub, key)


def kind_of(data):
    if data[:4] == b"%PDF":
        return "pdf"
    if data[:2] == b"\x1f\x8b":
        return "gzip"
    if data.lstrip()[:15].lower().startswith((b"<!doctype html", b"<html")):
        return "html"
    return "other"


def keep_latex(raw, dest):
    """Repack text members of a tar.gz, or a single gzipped .tex file, into dest.tex.tar.gz."""
    members = []
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
            for m in tf.getmembers():
                if m.isfile() and m.name.lower().endswith(TEXT_EXT) and m.size <= MAX_MEMBER:
                    members.append((os.path.basename(m.name) or "main.tex", m.name, tf.extractfile(m).read()))
    except tarfile.ReadError:
        body = gzip.decompress(raw)  # a single gzipped file, usually the main .tex
        if kind_of(body) == "pdf":
            return None
        members.append(("main.tex", "main.tex", body))
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as out:
        for _, name, body in members:
            info = tarfile.TarInfo(name=name.lstrip("/").replace("..", "_"))
            info.size = len(body)
            out.addfile(info, io.BytesIO(body))
    with open(dest + ".tex.tar.gz", "wb") as f:
        f.write(buf.getvalue())
    return {"n_text_files": len(members), "kept_bytes": len(buf.getvalue())}


def keep_pdf_text(raw, dest):
    import fitz  # PyMuPDF
    with fitz.open(stream=raw, filetype="pdf") as doc:
        text = "\n".join(page.get_text() for page in doc)
    data = gzip.compress(text.encode("utf-8"))
    with open(dest + ".pdf.txt.gz", "wb") as f:
        f.write(data)
    return {"kept_bytes": len(data), "n_chars": len(text)}


def load_done(manifest):
    done = {}
    if os.path.exists(manifest):
        with open(manifest) as f:
            for line in f:
                r = json.loads(line)
                done[r["arxiv_id"]] = r
    return {k for k, r in done.items() if r["status"] == "ok" or r.get("http") in PERMANENT}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id_list")
    ap.add_argument("out_dir")
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    manifest = os.path.join(a.out_dir, "manifest.jsonl")
    with open(a.id_list) as f:
        ids = [x.strip() for x in f if x.strip() and x.strip() != "arxiv_id"]
    done = load_done(manifest)
    todo = [i for i in ids if i not in done][: a.limit]
    print(f"{len(ids):,} IDs, {len(done):,} done, {len(todo):,} to fetch", flush=True)
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    last, backoff = 0.0, a.delay
    with open(manifest, "a") as log:
        for n, arxiv_id in enumerate(todo, 1):
            time.sleep(max(0.0, last + backoff - time.time()))
            last = time.time()
            rec = {"arxiv_id": arxiv_id, "t": time.strftime("%Y-%m-%dT%H:%M:%S")}
            try:
                r = s.get(f"https://arxiv.org/e-print/{arxiv_id}v1", timeout=120)
                rec["http"] = r.status_code
                if r.status_code != 200:
                    rec["status"] = "http_error"
                    if r.status_code in (403, 429, 503):
                        backoff = min(backoff * 2, 300)  # arXiv asks clients to slow down
                else:
                    backoff = a.delay
                    raw = r.content
                    rec.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), kind=kind_of(raw))
                    dest = shard_dir(a.out_dir, arxiv_id)
                    if rec["kind"] == "pdf":
                        rec.update(keep_pdf_text(raw, dest), status="ok", text_source="pdf")
                    elif rec["kind"] == "gzip":
                        kept = keep_latex(raw, dest)
                        if kept is None:
                            rec.update(keep_pdf_text(gzip.decompress(raw), dest), status="ok", text_source="pdf")
                        else:
                            rec.update(kept, status="ok", text_source="latex")
                    else:
                        rec["status"] = "unexpected_" + rec["kind"]
            except Exception as e:  # network errors, corrupt archives: log and move on
                rec.update(status="error", error=f"{type(e).__name__}: {e}"[:300])
            log.write(json.dumps(rec) + "\n")
            log.flush()
            if n % 100 == 0:
                print(f"{n:,}/{len(todo):,} {rec['t']} last={rec['status']}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
