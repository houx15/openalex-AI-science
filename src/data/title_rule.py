"""Exposure eligibility: is an arXiv paper a review-type item rather than a research paper? (SPEC §7)

Two title rules and an abstract rule, validated by hand in reports/phase0_data_audit.md §10:
  OLD    the Phase 0 regex in sql/ctas_author_funnel.sql: any review-type word anywhere in the title.
         About 27% of the titles it excludes are research papers (astronomy "X survey" data papers,
         "from the perspective of", papers about systematic-review automation).
  TITLE  [PROPOSED v2] review-type words only where titles announce a review: at the start ("A survey
         of", "Review on"), after a colon or dash (": a comprehensive survey"), "A perspective on",
         plus lecture notes, errata, comments/replies, position papers and book reviews.
  ABSTRACT [PROPOSED robustness] the abstract calls itself a review, survey, tutorial or notes.
"""

import re

_K = r"(survey|review|overview|tutorial|primer|mapping study)s?"
_ADJ = (r"brief|short|concise|comprehensive|systematic|critical|selective|recent|literature|quick|gentle|"
        r"mini|unified|focused|holistic|structured")
TITLE = re.compile("|".join([
    r"^(a |an )?([\w-]+ ){0,2}(review|overview|tutorial|primer)s? (of|on|for|and)\b",
    rf"^(a |an )?(({_ADJ})[ -]){{0,2}}surveys? (of|on|for|and)\b",  # astronomy uses "X survey of"
    r"^(a |an )?([\w-]+ ){0,2}surveys? on\b",
    rf"^{_K}\b",
    rf"[:,.;?!]\s*(a |an )?([\w-]+[ -]){{0,3}}{_K}\b",
    rf"(--|—|–)\s*(a |an )?([\w-]+[ -]){{0,3}}{_K}\b",
    r"^(a |an )?perspectives? on\b|^perspective:",
    r"lecture notes|\berrat(um|a)\b|\bcorrigendum\b|position paper|book review",
    r"^(a )?(comment on|reply to|response to)\b",
]))
ABSTRACT = re.compile(r"\b(this|the present|in this) (review|survey|tutorial|mini-review)\b"
                      r"|these (lecture )?notes|survey paper|review article|review paper")
OLD = re.compile(r"(^|[^a-z])(survey|review|tutorial|overview|position paper|perspective|primer|lecture notes|"
                 r"erratum|corrigendum|comment on|reply to|response to)([^a-z]|$)")


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def review_title(title):
    return bool(TITLE.search(_norm(title)))


def review_abstract(abstract):
    return bool(ABSTRACT.search(_norm(abstract)))


def review_title_old(title):
    return bool(OLD.search(_norm(title)))
