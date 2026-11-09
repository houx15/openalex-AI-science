import io
import tarfile

from src.text import latex_to_text as L


def make_tar(tmp_path, files):
    p = tmp_path / "x.tex.tar.gz"
    with tarfile.open(p, "w:gz") as tf:
        for name, body in files.items():
            data = body.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return str(p)


DOC = r"""\documentclass{article}
\title{%s}
\begin{document}
\maketitle
\author{Jane Roe \thanks{x@y.org}}
\begin{abstract}We study %s.\end{abstract}
\section{Intro} Text with math $x^2$ and a citation \cite{a}. %% a comment
\input{sec}
\begin{figure}\includegraphics{f}\caption{A {nice} figure.}\end{figure}
\section*{Acknowledgments} We thank funders.
\section{End} Final words.
\appendix \section{Proofs} Long proof.
\bibliography{refs}
\end{document}
"""


def test_parse_drops_boilerplate_and_keeps_prose(tmp_path):
    p = make_tar(tmp_path, {"main.tex": DOC % ("First Paper", "cats"), "sec.tex": "Included section text."})
    r = L.parse_latex(p)
    t = r["text"]
    assert r["title"] == "First Paper"
    assert "We study cats" in t and "Included section text" in t and "A nice figure" in t
    assert "Final words" in t
    for gone in ("Jane Roe", "x@y.org", "a comment", "funders", "Long proof", "\\cite", "NO \\author"):
        assert gone not in t
    assert r["appendix_chars"] > 0 and r["refs_found"]


def test_no_state_carries_over_between_papers(tmp_path):
    p1 = make_tar(tmp_path, {"main.tex": DOC % ("Alpha Title", "dogs"), "sec.tex": ""})
    L.parse_latex(p1)
    (tmp_path / "x.tex.tar.gz").unlink()
    p2 = make_tar(tmp_path, {"main.tex": DOC.replace(r"\title{%s}", "") % "birds", "sec.tex": ""})
    r2 = L.parse_latex(p2)
    assert "Alpha Title" not in r2["text"] and r2["title"] is None


def test_main_file_prefers_non_supplement(tmp_path):
    files = {"supplement.tex": DOC % ("S", "long " * 500), "paper.tex": DOC % ("P", "short"), "sec.tex": ""}
    assert L.choose_main(L.read_members(make_tar(tmp_path, files)))[0] == "paper.tex"
