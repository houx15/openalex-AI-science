"""Phase 1: convert kept arXiv v1 LaTeX (from fetch_arxiv_v1.py) to plain text for scoring.

Rule [PROPOSED; to be fixed in the pilot, SPEC §8 "remove references and other boilerplate"]:
  1. Main file: among .tex/.ltx members with \\documentclass and \\begin{document}, prefer names that
     are not supplements, responses or cover letters, then the longest after expanding inputs.
  2. Expand \\input / \\include / \\subfile from the archive (depth <= 5), strip comments.
  3. Keep \\begin{document} .. \\end{document}. Record and drop everything from the bibliography on
     (thebibliography, \\bibliography, \\printbibliography). Drop the appendix (\\appendix,
     \\begin{appendix}) from the main text but report its length, so the appendix rule can be
     changed after the pilot without re-parsing.
  4. Drop floats' bodies but keep captions; replace display math with [MATH] and inline math with
     [M]; drop acknowledgements sections.
  5. Convert the rest with pylatexenc; fall back to a regex de-TeX if it fails.
PDF-only submissions arrive as text already (<id>.pdf.txt.gz); references are cut at the last
'References'/'Bibliography' heading.

Usage:
    python -m src.text.latex_to_text IN_DIR OUT_JSONL_GZ [--shard i/n]
"""

import argparse
import glob
import gzip
import json
import os
import re
import tarfile

from pylatexenc.latex2text import LatexNodes2Text

TEX_EXT = (".tex", ".ltx")
DEPRIORITIZE = re.compile(r"supp|response|reply|rebuttal|cover|letter|highlights|appendix|si[_\-]|template|sample", re.I)
COMMENT = re.compile(r"(?<!\\)%.*")
INPUT = re.compile(r"\\(?:input|include|subfile)\s*\{([^}]+)\}")
BIB_START = re.compile(r"\\begin\{thebibliography\}|\\bibliography\s*\{|\\printbibliography|\\begin\{references\}")
APPENDIX = re.compile(r"\\appendix\b|\\begin\{appendix\}|\\begin\{appendices\}")
ACK = re.compile(r"\\(?:section|subsection)\*?\s*\{\s*acknowledge?ments?\s*\}.*?(?=\\(?:section|subsection)\*?\s*\{|$)"
                 r"|\\begin\{acknowledge?ments?\}.*?\\end\{acknowledge?ments?\}|\\acknowledgments?\b.*?(?=\\section|$)", re.S | re.I)
DISPLAY_MATH = re.compile(r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath|math)\*?\}.*?\\end\{\1\*?\}"
                          r"|\$\$.*?\$\$|\\\[.*?\\\]", re.S)
INLINE_MATH = re.compile(r"(?<!\\)\$[^$]+?(?<!\\)\$|\\\(.*?\\\)", re.S)
FLOAT = re.compile(r"\\begin\{(figure|table|algorithm|lstlisting|verbatim|tikzpicture|minted)\*?\}(.*?)\\end\{\1\*?\}", re.S)
CAPTION = re.compile(r"\\caption(?:\[[^\]]*\])?\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", re.S)
FRONT_CMDS = ("author", "affiliation", "affil", "address", "email", "thanks", "institute", "inst", "date",
              "orcid", "ead", "corref", "IEEEauthorblockN", "IEEEauthorblockA", "icmlauthor", "icmlaffiliation",
              "icmlcorrespondingauthor", "correspondingauthor", "authorrunning", "titlerunning", "markboth")
FRONT_START = re.compile(r"\\(" + "|".join(FRONT_CMDS) + r")\*?\s*(\[[^\]]*\])?\s*\{")
RULES = re.compile(r"[=_\-~*#.]{5,}")
PDF_REFS = re.compile(r"\n\s*(references|bibliography|literature cited)\s*\n", re.I)



def new_converter():
    # A fresh converter per paper: pylatexenc remembers \title/\author across calls, which leaked
    # one paper's title into the next paper's text in the first test.
    return LatexNodes2Text(math_mode="verbatim", strict_latex_spaces=False)


def read_members(path):
    out = {}
    with tarfile.open(path) as tf:
        for m in tf.getmembers():
            if m.isfile():
                out[m.name] = tf.extractfile(m).read().decode("utf-8", errors="replace")
    return out


def expand(src, files, depth=0):
    if depth > 5:
        return src

    def sub(m):
        name = m.group(1).strip()
        for cand in (name, name + ".tex"):
            for k in files:
                if k == cand or k.endswith("/" + cand):
                    return expand(strip_comments(files[k]), files, depth + 1)
        return ""
    return INPUT.sub(sub, src)


def strip_comments(s):
    s = re.sub(r"\\begin\{comment\}.*?\\end\{comment\}", "", s, flags=re.S)
    return COMMENT.sub("", s)


def choose_main(files):
    cands = []
    for name, body in files.items():
        if name.lower().endswith(TEX_EXT) and "\\documentclass" in body and "\\begin{document}" in body:
            full = expand(strip_comments(body), files)
            cands.append((bool(DEPRIORITIZE.search(os.path.basename(name))), -len(full), name, full))
    if not cands:  # no documentclass: concatenate everything (rare fragments)
        texts = [strip_comments(b) for n, b in sorted(files.items()) if n.lower().endswith(TEX_EXT)]
        return None, "\n".join(texts)
    cands.sort()
    return cands[0][2], cands[0][3]


def drop_commands(s):
    """Remove author/affiliation-type commands with their (nested) brace arguments."""
    out, pos = [], 0
    for m in FRONT_START.finditer(s):
        if m.start() < pos:
            continue
        depth, j = 1, m.end()
        while j < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[j], 0) if s[j - 1] != "\\" else 0
            j += 1
        out.append(s[pos:m.start()])
        pos = j
    out.append(s[pos:])
    return "".join(out)


def detex(s):
    s = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}]", "", s)
    return s


def clean_body(src):
    info = {}
    b = src.find("\\begin{document}")
    e = src.rfind("\\end{document}")
    body = src[b + len("\\begin{document}"): e if e > b else None] if b >= 0 else src
    m = BIB_START.search(body)
    info["refs_found"] = m is not None
    if m:
        body = body[: m.start()]
    m = APPENDIX.search(body)
    info["appendix_chars"] = 0
    if m:
        info["appendix_chars"] = len(body) - m.start()
        body = body[: m.start()]
    body = re.sub(r"\\maketitle\b", " ", body)
    body = drop_commands(body)
    body = ACK.sub(" ", body)
    body = FLOAT.sub(lambda f: "\n" + " ".join(c for c in CAPTION.findall(f.group(2))) + "\n", body)
    body = DISPLAY_MATH.sub(" [MATH] ", body)
    body = INLINE_MATH.sub(" [M] ", body)
    body = re.sub(r"\\(?:cite[a-zA-Z]*|ref|eqref|autoref|cref|Cref|label|url|footnotemark)\*?(\[[^\]]*\])*\{[^}]*\}", "", body)
    return body, info


def braced_arg(s, cmd):
    m = re.search(r"\\" + cmd + r"\*?\s*(\[[^\]]*\])?\s*\{", s)
    if not m:
        return None
    depth, j = 1, m.end()
    while j < len(s) and depth:
        depth += {"{": 1, "}": -1}.get(s[j], 0) if s[j - 1] != "\\" else 0
        j += 1
    return s[m.end(): j - 1]


def to_text(body):
    l2t = new_converter()
    try:
        text, method = l2t.latex_to_text(body), "pylatexenc"
    except Exception:  # pylatexenc fails on some constructs: convert paragraph by paragraph
        parts, n_bad = [], 0
        for para in re.split(r"\n\s*\n", body):
            try:
                parts.append(l2t.latex_to_text(para))
            except Exception:
                parts.append(detex(para))
                n_bad += 1
        text, method = "\n\n".join(parts), f"pylatexenc_by_paragraph(regex={n_bad})"
    text = RULES.sub(" ", text)
    text = re.sub(r"\S+@\S+\.[A-Za-z]{2,}", " ", text)  # stray e-mail addresses
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*(\n\s*)+", "\n\n", text)
    return text.strip(), method


def parse_latex(path):
    files = read_members(path)
    main, src = choose_main(files)
    body, info = clean_body(src)
    text, method = to_text(body)
    title = braced_arg(src, "title")
    if title is not None:
        title = re.sub(r"\s+", " ", to_text(drop_commands(title))[0]).strip()
    return {"main_file": main, "method": method, "title": title, **info, "text": text}


def parse_pdf_text(path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        text = f.read()
    hits = list(PDF_REFS.finditer(text))
    cut = hits[-1].start() if hits and hits[-1].start() > 0.5 * len(text) else None
    return {"main_file": None, "method": "pdf", "refs_found": cut is not None, "appendix_chars": None,
            "text": text[:cut].strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir")
    ap.add_argument("out")
    ap.add_argument("--shard", default="0/1")
    a = ap.parse_args()
    i, n = map(int, a.shard.split("/"))
    paths = sorted(glob.glob(os.path.join(a.in_dir, "*", "*.tex.tar.gz")) + glob.glob(os.path.join(a.in_dir, "*", "*.pdf.txt.gz")))
    paths = paths[i::n]
    with gzip.open(a.out, "wt", encoding="utf-8") as out:
        for p in paths:
            name = os.path.basename(p)
            arxiv_id = name.split(".tex.tar.gz")[0].split(".pdf.txt.gz")[0].replace("_", "/")
            try:
                rec = parse_latex(p) if name.endswith(".tex.tar.gz") else parse_pdf_text(p)
                rec["status"] = "ok"
            except Exception as e:
                rec = {"status": "error", "error": f"{type(e).__name__}: {e}"[:300], "text": ""}
            rec.update(arxiv_id=arxiv_id, source="latex" if name.endswith(".tex.tar.gz") else "pdf",
                       n_chars=len(rec["text"]), n_words=len(rec["text"].split()))
            out.write(json.dumps(rec) + "\n")


if __name__ == "__main__":
    main()
