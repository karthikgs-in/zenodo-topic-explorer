import os
import json
from pathlib import Path
from flask import Flask, render_template, redirect, url_for
from flask import send_file, abort, request

import pandas as pd
import plotly.express as px
from io import BytesIO

APP_TITLE = "Zenodo Topic Explorer"
PRECOMPUTE_DIR = Path("precompute")
MANIFEST = PRECOMPUTE_DIR / "MANIFEST.json"

app = Flask(__name__)

# ---------- Load variants ----------
def load_manifest():
    if not MANIFEST.exists():
        return {"variants": {}}
    return json.loads(MANIFEST.read_text())

def load_variant_df(csv_name: str) -> pd.DataFrame:
    path = PRECOMPUTE_DIR / csv_name
    if not path.exists():
        raise FileNotFoundError(f"Variant CSV not found: {path}")
    df = pd.read_csv(path)
    # ensure dtypes
    for c in ['stats.unique_downloads', 'stats.downloads', 'stats.views']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    # ensure topic columns
    if "topic" not in df.columns or "topic_id" not in df.columns:
        raise ValueError("Precomputed file missing 'topic' or 'topic_id'")
    return df

MAN = load_manifest()
VARIANTS = MAN.get("variants", {})  # {name: filename}

# Eager-load dataframes for speed (small file)
DF_CACHE = {}
for name, csv_name in VARIANTS.items():
    try:
        DF_CACHE[name] = load_variant_df(csv_name)
    except Exception as e:
        print(f"[warn] could not load variant {name}: {e}")

def variant_names():
    # stable order: keywords, tfidf_kmeans, sbert_kmeans if present
    preferred = ["keywords", "tfidf_kmeans", "sbert_kmeans"]
    existing = [v for v in preferred if v in DF_CACHE]
    others = [k for k in DF_CACHE.keys() if k not in existing]
    return existing + sorted(others)

def get_selected_variant():
    # priority: query param -> cookie -> default (first available)
    name = request.args.get("model")
    if name and name in DF_CACHE:
        return name
    # optional: cookie for stickiness
    cookie = request.cookies.get("model")
    if cookie and cookie in DF_CACHE:
        return cookie
    names = variant_names()
    if not names:
        return None
    return names[0]

def treemap_html(df_topic_agg: pd.DataFrame):
    treemap_df = df_topic_agg.copy()
    treemap_df.insert(0, "parent", "All Topics")
    treemap_df.rename(columns={"topic": "label"}, inplace=True)
    fig = px.treemap(
        treemap_df,
        path=["parent", "label"],
        values="downloads",
        hover_data={"datasets": True, "downloads": ":,", "views": ":,", "unique_downloads": ":,"}
    )
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=24, l=0, r=0, b=0), height=620)
    return fig.to_html(full_html=False, include_plotlyjs="cdn")

def make_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby('topic', as_index=False)
          .agg(
              datasets=('metadata.title', 'count'),
              downloads=('stats.downloads', 'sum'),
              views=('stats.views', 'sum'),
              unique_downloads=('stats.unique_downloads', 'sum')
          )
          .sort_values('downloads', ascending=False)
    )
    return agg

@app.route("/")
def index():
    sel = get_selected_variant()
    if sel is None:
        # friendly message with instructions
        return render_template("index.html",
                               app_title=APP_TITLE,
                               variants=[],
                               selected=None,
                               treemap=None,
                               sidebar=[],
                               topic_count=0,
                               row_count=0,
                               total_downloads="0",
                               message="No precomputed variants found. Run precompute scripts and commit precompute/*.csv + MANIFEST.json.")
    df = DF_CACHE[sel]
    agg = make_aggregates(df)

    # preformat in Python (clean templates)
    sidebar = (
        agg[['topic', 'downloads']]
        .head(20)
        .assign(downloads_fmt=lambda d: d['downloads'].map(lambda v: f"{int(v):,}"))
        .to_dict(orient="records")
    )

    treemap = treemap_html(agg)
    total_downloads = f"{int(agg['downloads'].sum()):,}"

    return render_template("index.html",
        app_title=APP_TITLE,
        message=None,
        variants=variant_names(),
        selected=sel,
        treemap=treemap,
        sidebar=sidebar,
        topic_count=agg.shape[0],
        row_count=df.shape[0],
        total_downloads=total_downloads
    )

@app.route("/topic/<path:topic>")
def topic_page(topic):
    sel = get_selected_variant()
    if sel is None:
        abort(404, "No variants available.")
    df = DF_CACHE[sel]
    filtered = df[df['topic'] == topic].copy()
    if filtered.empty:
        abort(404, description="Topic not found for selected variant.")
    filtered = filtered.sort_values(['stats.downloads', 'stats.views'], ascending=False)

    def fmt(n): return f"{int(n):,}"
    rows = []
    for _, r in filtered.iterrows():
        rows.append({
            "metadata.title": r["metadata.title"],
            "links.doi": r["links.doi"],
            "stats.downloads": fmt(r["stats.downloads"]),
            "stats.views": fmt(r["stats.views"]),
            "stats.unique_downloads": fmt(r["stats.unique_downloads"]),
            "metadata.license.id": r["metadata.license.id"],
        })

    return render_template("topic.html",
        app_title=APP_TITLE,
        topic=topic,
        selected=sel,
        variants=variant_names(),
        rows=rows
    )

# @app.route("/download/variant.csv")
# def download_variant_csv():
#     sel = get_selected_variant()
#     if sel is None:
#         abort(404, "No variants available.")
#     csv_name = VARIANTS[sel]
#     path = PRECOMPUTE_DIR / csv_name
#     return send_file(path, as_attachment=True, download_name=f"{sel}.csv")

@app.route("/download/variant.csv")
def download_variant_csv():
    sel = get_selected_variant()
    if sel is None:
        abort(404, "No variants available.")
    df = DF_CACHE[sel]

    buf = BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    fname = f"{sel}.csv"
    return send_file(buf, mimetype="text/csv", as_attachment=True, download_name=fname)

@app.route("/download/topic.csv")
def download_topic_csv():
    sel = get_selected_variant()
    if sel is None:
        abort(404, "No variants available.")
    df = DF_CACHE[sel]

    topic = request.args.get("topic")
    if not topic:
        abort(400, "Missing ?topic=")
    sub = df[df["topic"] == topic]
    if sub.empty:
        abort(404, "Topic not found for selected variant.")

    buf = BytesIO()
    sub.to_csv(buf, index=False)
    buf.seek(0)
    safe = "".join(ch if ch.isalnum() else "_" for ch in topic)[:80] or "topic"
    fname = f"topic_{safe}.csv"
    return send_file(buf, mimetype="text/csv", as_attachment=True, download_name=fname)


# Persist model choice via redirect + cookie (optional nicety)
@app.route("/set-model")
def set_model():
    name = request.args.get("model")
    if name not in DF_CACHE:
        abort(400, "Unknown model variant.")
    resp = redirect(url_for('index', model=name))
    resp.set_cookie("model", name, max_age=30*24*3600)
    return resp

if __name__ == "__main__":
    app.run(debug=True)
