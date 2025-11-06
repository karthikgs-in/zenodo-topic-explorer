# precompute/precompute_keywords.py
from __future__ import annotations
import re
from pathlib import Path
from common import read_input, write_output

TOPIC_KEYWORDS = {
    "AI/ML": ["machine learning","deep learning","neural","dataset","classification","segmentation","transformer","bert","gpt","cnn","pytorch","tensorflow","model"],
    "Biology": ["genome","genomic","protein","cell","rna","dna","microbiome","bio","bioinformatics","sequencing","mouse","yeast"],
    "Health": ["clinical","covid","epidemiology","patient","medical","hospital","trial","health","disease","ct","mri"],
    "Earth Science": ["climate","weather","geospatial","remote sensing","satellite","earth","hydro","ocean","seismic","gis","land","soil"],
    "Astronomy": ["telescope","astronomy","astro","galaxy","stellar","cosmic","planet","space","jwst","hubble"],
    "Physics": ["quantum","particle","physics","simulation","lattice","spectra","optics","plasma","superconduct"],
    "Chemistry": ["chemical","chemistry","molecule","compound","mass spectrometry","nmr","spectroscopy","chemi"],
    "Social Science": ["survey","social","policy","economic","education","language","twitter","demographic","census","behavior"],
    "Engineering": ["robot","sensor","control","manufacturing","mechanical","electrical","signal","cad","engineering","circuit"],
    "Other": [],
}

def normalize(s: str) -> str:
    return re.sub(r"\s+"," ", str(s).lower()).strip()

def assign_topic(title: str) -> str:
    t = normalize(title)
    best_topic, best_hits = "Other", 0
    for topic, kws in TOPIC_KEYWORDS.items():
        hits = sum(1 for kw in kws if kw in t)
        if hits > best_hits:
            best_topic, best_hits = topic, hits
    return best_topic

def run(input_csv="data/zenodo_top500.csv",
        out_dir="precompute",
        variant="keywords",
        manifest="precompute/MANIFEST.json"):
    df = read_input(input_csv)
    df["topic"] = df["metadata.title"].fillna("").map(assign_topic)
    # make stable topic_id from category list
    categories = {name:i for i, name in enumerate(sorted(set(df["topic"])))}
    df["topic_id"] = df["topic"].map(categories)
    out_path = Path(out_dir) / f"{variant}.csv"
    write_output(df, out_path, variant, manifest)

if __name__ == "__main__":
    run()
