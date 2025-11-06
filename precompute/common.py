# precompute/common.py
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

REQUIRED_COLS = [
    "metadata.title",
    "links.doi",
    "metadata.license.id",
    "stats.unique_downloads",
    "stats.downloads",
    "stats.views",
]

OUTPUT_COLS = REQUIRED_COLS + ["topic_id", "topic"]

def read_input(csv_path: str | Path) -> pd.DataFrame:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    for c in ["stats.unique_downloads", "stats.downloads", "stats.views"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df

def write_output(df: pd.DataFrame, out_path: str | Path, variant_name: str, manifest_path: str | Path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # ensure schema
    for c in ["topic_id", "topic"]:
        if c not in df.columns:
            raise ValueError(f"Output is missing '{c}' column.")
    df[OUTPUT_COLS].to_csv(out_path, index=False)
    # update MANIFEST
    manifest_path = Path(manifest_path)
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {}
    manifest.setdefault("variants", {})
    manifest["variants"][variant_name] = str(out_path.name)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"[ok] wrote {out_path} and updated {manifest_path}")
