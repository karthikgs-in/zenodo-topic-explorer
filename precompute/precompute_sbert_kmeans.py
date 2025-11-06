# precompute/precompute_sbert_kmeans.py
from __future__ import annotations
from pathlib import Path
from common import read_input, write_output
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

def run(input_csv="data/zenodo_top500.csv",
        out_dir="precompute",
        n_clusters=12,
        variant="sbert_kmeans",
        manifest="precompute/MANIFEST.json"):
    df = read_input(input_csv)
    titles = df["metadata.title"].fillna("").astype(str).tolist()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    emb = model.encode(titles, normalize_embeddings=True)
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42).fit(emb)
    df["topic_id"] = km.labels_
    # name clusters using TF-IDF over cluster titles
    df["__t__"] = titles
    names = {}
    for cid in range(n_clusters):
        texts = df.loc[df["topic_id"] == cid, "__t__"].tolist()
        if not texts:
            names[cid] = f"Topic {cid}"
            continue
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=3000)
        X = vec.fit_transform(texts)
        terms = vec.get_feature_names_out()
        centroid = X.mean(axis=0).A1
        order = centroid.argsort()[::-1]
        top = [terms[i] for i in order[:3]]
        names[cid] = ", ".join(top[:2]) if top else f"Topic {cid}"
    df["topic"] = df["topic_id"].map(names)
    df.drop(columns="__t__", inplace=True)
    out_path = Path(out_dir) / f"{variant}.csv"
    write_output(df, out_path, variant, manifest)

if __name__ == "__main__":
    run()
