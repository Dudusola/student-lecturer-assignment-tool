"""Field similarity between students and lecturers.

Each text is split into topics ("AI, Data Science" -> two topics), acronyms are expanded
using phrases seen anywhere in the data ("AI" -> "artificial intelligence"), then topics are
embedded with character n-gram TF-IDF so typos, plurals and word order still match.
A student/lecturer score is the cosine similarity of their best-matching topic pair (0..1).
"""
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_SPLIT = re.compile(r"[,;/|\n]+")
_STOP = {"of", "and", "the", "in", "for", "to", "on", "with", "&"}


def _clean(text: str) -> str:
    return re.sub(r"[^a-z0-9&]+", " ", text.lower()).strip()


def _topics(text: str) -> list[str]:
    return [t for t in (_clean(p) for p in _SPLIT.split(str(text))) if t]


def _acronym(phrase: str) -> str:
    words = [w for w in phrase.split() if w not in _STOP]
    return "".join(w[0] for w in words) if len(words) > 1 else ""


def similarity_matrix(student_fields, lecturer_fields) -> np.ndarray:
    """Return an (n_students, n_lecturers) array of scores in [0, 1]."""
    # Fields repeat a lot (a cohort has few departments): score unique texts only.
    s_uniq, s_inv = np.unique(np.asarray(student_fields, dtype=str), return_inverse=True)
    l_uniq, l_inv = np.unique(np.asarray(lecturer_fields, dtype=str), return_inverse=True)
    return _unique_scores(s_uniq, l_uniq)[np.ix_(s_inv.ravel(), l_inv.ravel())]


def _unique_scores(student_fields, lecturer_fields) -> np.ndarray:
    s_topics = [_topics(f) for f in student_fields]
    l_topics = [_topics(f) for f in lecturer_fields]
    scores = np.zeros((len(s_topics), len(l_topics)))

    phrases = {t for ts in s_topics + l_topics for t in ts}
    if not phrases:
        return scores
    acronyms = {}
    for p in phrases:
        if a := _acronym(p):
            acronyms.setdefault(a, p)
    expand = lambda t: acronyms.get(t.replace(" ", ""), t) if len(t) <= 6 else t
    s_topics = [[expand(t) for t in ts] for ts in s_topics]
    l_topics = [[expand(t) for t in ts] for ts in l_topics]

    vocab = sorted({t for ts in s_topics + l_topics for t in ts})
    index = {t: i for i, t in enumerate(vocab)}
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)
    topic_sim = cosine_similarity(vec.fit_transform(vocab))
    np.fill_diagonal(topic_sim, 1.0)

    for i, st in enumerate(s_topics):
        if not st:
            continue
        si = [index[t] for t in st]
        for j, lt in enumerate(l_topics):
            if lt:
                scores[i, j] = topic_sim[np.ix_(si, [index[t] for t in lt])].max()
    return np.clip(scores, 0.0, 1.0)
