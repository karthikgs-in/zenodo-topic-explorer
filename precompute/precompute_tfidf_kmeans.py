# precompute/precompute_tfidf_kmeans.py
from __future__ import annotations
import re
from pathlib import Path
from common import read_input, write_output
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\b(v\d+(\.\d+)*)\b", " ", s)
    s = re.sub(r"[^a-z0-9\s\-\+\.]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def run(input_csv="data/zenodo_top500.csv",
        out_dir="precompute",
        n_clusters=12,
        variant="tfidf_kmeans",
        manifest="precompute/MANIFEST.json"):
    df = read_input(input_csv)
    titles = df["metadata.title"].fillna("").astype(str).map(norm)
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=8000)
    X = vec.fit_transform(titles)
    try:
        km = KMeans(n_clusters=n_clusters, n_init="auto", random_state=42)
    except TypeError:
        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = km.fit_predict(X)
    df["topic_id"] = labels
    # name clusters with top centroid terms
    terms = vec.get_feature_names_out()
    names = {}
    for k in range(n_clusters):
        order = km.cluster_centers_[k].argsort()[::-1]
        top = [terms[i] for i in order[:3]]
        names[k] = ", ".join(top[:2]) if top else f"Topic {k}"
    df["topic"] = df["topic_id"].map(names)
    out_path = Path(out_dir) / f"{variant}.csv"
    write_output(df, out_path, variant, manifest)

if __name__ == "__main__":
    run()
