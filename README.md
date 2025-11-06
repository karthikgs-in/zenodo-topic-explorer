# Zenodo Topic Explorer 🧭

**What is it?**
This is a lightweight Flask web app that lets you explore the top 500 most-downloaded datasets on [Zenodo.org](https://zenodo.org) through an interactive treemap and drill-down views. Zenodo is a data repository "built and developed by researchers, to ensure that everyone can join in Open Science."


You can toggle between different topic-modeling variants (e.g., keyword mapping, TF-IDF + KMeans, SBERT + KMeans) and see which topics dominate by downloads, views, and dataset counts.

**Why build this?**
Because metadata is beautiful—and sometimes usage patterns tell their own story.
This tool helps you:

* surface topics that attract the most downloads
* compare how different topic-modeling methods classify the same datasets
* dig into individual datasets (title, DOI, license, downloads/views)

**Dataset citation**

> The underlying data is from the Kaggle dataset [“Most downloaded Zenodo datasets”](https://www.kaggle.com/datasets/chrisfilo/most-downloaded-zenodo-datasets) by Chris Filo.
> DOI: `https://www.kaggle.com/datasets/chrisfilo/most-downloaded-zenodo-datasets`

---

## 🚀 Quick Start

### 1  Clone the repo

```bash
git clone https://github.com/your-username/zenodo-topic-explorer.git
cd zenodo-topic-explorer
```

### 2  Precompute topic variants (locally)

> *Only if you want to add or regenerate topic models.*

```bash
python -m venv .venv_pre
source .venv_pre/bin/activate
pip install -r requirements-precompute.txt

# run any or all
python precompute/precompute_keywords.py
python precompute/precompute_tfidf_kmeans.py
python precompute/precompute_sbert_kmeans.py
```

This creates CSVs in `precompute/` and updates `precompute/MANIFEST.json`.

### 3  Run the app

```bash
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

### 4  Deploy for free

Use [Render](https://render.com) or [Railway](https://railway.app):

```
# Procfile
web: gunicorn app:app
```

Push to GitHub, connect the repo, and set runtime to `python-3.11.9`.
Your precomputed CSVs are already committed, keeping the deployment lightweight.

---

## 🧩 Stack & Features

* **Flask** for routing & templates
* **Plotly Express** for interactive treemap visualizations
* **Pandas** for data aggregation
* **Offline precompute scripts** to generate topic variants using different models

### Supported variants

* `keywords`: simple rule-based taxonomy
* `tfidf_kmeans`: classical TF-IDF + KMeans
* `sbert_kmeans`: semantic embeddings via Sentence-Transformers + KMeans

Switch between them via the dropdown on the homepage or `?model=variant_name`.

---

## 🎨 UI Highlights

* Clean dark theme, responsive grid
* Treemap sized by **downloads**, hover shows **datasets/views**
* Click any treemap tile → drills down into that topic
* Sidebar lists top topics by downloads
* Back button and CSV download on topic pages
* Dropdown toggle persists your selected model

---

## ⚠️ Notes

* Designed for **exploration**, not production workloads
* Plotly zoom is native; tile click redirects automatically
* `sbert_kmeans` is RAM-heavier—precompute offline
* Free-tier hosts may sleep when idle

---

## ✨ License & Acknowledgements

* Dataset: CC BY 4.0 (see Kaggle source)
* App: MIT License (unless you choose otherwise)
* Thanks to Chris Filo for the dataset and to the Python open-source community for the tools that made this possible.

—

Happy exploring 👀
## 🧑‍💻 Author

**Karthik G. Shanmugasundaram**  
M.Tech (AI & DS), SRM Institute of Science and Technology  
[GitHub](https://github.com/karthikgs-in) • [LinkedIn](https://linkedin.com/in/karthikgs-in)

