# YOU-DARE Repository

This repository is part of the **YOU-DARE** project and contains the core data processing and analysis pipelines used for the Far-right gender controversy mapping. It structures the workflow from raw scraped data through annotation, filtering, analysis, and finally visualization outputs such as timelines and semantic maps.

The repository is organised as a sequence of interconnected pipelines, where each step produces outputs that are used as inputs for the next.

The repository is not in active development and mainly serves as technical documentation for how the analysis was conducted.

---

## Project Context

YOU-DARE (YOUth Debunking the Gendered Arguments of far-Right Extremism) is an EU-funded research project exploring how far-right youth movements across Europe use gender narratives to shape identity, build influence, and impact democratic values.

Methodologically, the project combines:
- Qualitative annotation
- Computational text analysis
- Temporal and semantic mapping of controversies

This repository supports that work by implementing the full data pipeline from raw text data to analytical outputs.

Project website: https://you-dare.eu/

---

## Background

The overall workflow is designed to transform heterogeneous, multi-source textual data into structured analytical outputs. The pipeline includes:

- Data collection (submodule: https://github.com/CALDISS-AAU/YOU-DARE_scrapers/tree/master)
- Annotation
- Data standardisation and merging
- Sentence-level filtering and indexing
- Temporal analysis (peak detection)
- Semantic embedding and mapping
- Final visualisation and reporting outputs

The goal is to enable cross-country and cross-theme analysis of discourse dynamics.

---

## Repository Purpose

The repository is designed as a **modular pipeline** that:

1. Collects web contents from websites, YouTube and Telegram
1. Structures and prepares data for annotation
2. Processes raw scraped data
3. Filters and indexes relevant content based on theme dictionaries
4. Detects temporal patterns (peaks)
5. Maps semantic structures in discourse based on annotations and filters
6. Produces visual and tabular outputs for reporting based on researcher insights from output from step 4 and 5.

Each step builds on the previous one.

---

## Pipeline Overview

### 1. Collecting web contents via scrapers

Data scraping is handled in a separate repository:

👉 https://github.com/CALDISS-AAU/YOU-DARE_scrapers

This includes:
- Platform-specific scrapers (websites, YouTube and Telegram)
- Data extraction pipelines
- Initial raw `.jsonl` outputs

This repository assumes scraped data is already available in the expected directory structure.
Please consult this repo before.

---

### 2. Doccano (open-coding annotation)

The annotation of texts within this repository was introduced before all data had been collected and before data had been standardised fully. However, this step in itself hold some standardisation practices that were later used as the foundation for step 2 (Data Standardisation), where e.g. Telegram posts and replies were combined.

This step was also introduced before data collection was standardised, hence all scrapers used for data collection for websites and some scrapers used for YouTube has been standardised later on where fields have been combined, renamed or in other ways changed compared to the initial collected data.

Due to the introduction of this annotation layer before the rest of the pipeline was in place, the standardisation and cleaning process within this step will for the most part be redundant and will likely cause errors, if one were to apply this step to any newly collected data using the standardised version of the scrapers.

Annotation was performed using [Doccano](https://doccano.github.io/doccano/).

At this stage:
- Data is standardised and reduced to only include relevant data fields
- Relevant data fields besides the text is combined into a YAML-header for the text for easier searchability of e.g. matched keywords
- Raw text data is manually labelled by the researchers
- Relevant entities, themes, and spans are identified
- Output is exported as `.jsonl` files

These annotations served as the basis for which themes to focus on.

---

### 3. raw-data / data-combiner (data standardisation)

This step consolidates raw datasets into a unified structure. The standardisation step in this pipeline is build to handle data collected from scrapers which have not yet been standardised. While this code in its current form will not result in any errors if used on data collected by the now standardised scrapers, some of the code will be redundant. 

Key operations:
- Load multiple `.jsonl` and `.csv` datasets from different platforms (websites, Telegram and YouTube)
- Infer and assign metadata such as platform/source
- Standardise schema across datasets. 
- Merge into combined country-level `.jsonl` datasets, where each row represents one text including only data fields relevant to that specific text

The output is a harmonised dataset for each country that is part of the project, and one that can be consistently processed downstream.

---

### 4. controversy-mapping / pre-processing / sentence_filtering (preprocessing & indexing)

This stage transforms the harmonised datasets into analysis-ready datasets.

Main steps:
- Clean and normalise text fields
- Segment texts into sentences
- Match on provided keywords
- Attach metadata (actor, source, timestamps)
- Produce indexed datasets per country and theme only including provided keywords

The output is structured `.jl` files containing filtered and indexed text units, which are used in both temporal and semantic analyses.

---

### 5. controversy-mapping / peak-detection (temporal analysis)

This pipeline identifies peaks in activity over time based on publication date for each text. Weights were introduced so peaks had to contain texts from more than one source.

A 300-character text chunk was extracted from all texts associated with each identified peak, allowing researchers to contextualise the text and qualitatively assess the meanings, narratives, and attitudes expressed in the peaks.

Core logic:
- Aggregate text counts per actor over time (configurable frequency, e.g. monthly)
- Compute relative activity weights per actor
- Apply anomaly detection (isolation forest logic)

Outputs:
- Time series data per actor
- Identified peak periods

#### 5.1 Facilitating interpretation

To facilitate interpretation of the identified peak periods, relevant materials were provided for researchers:
- Word clouds based on all texts published within a peak period (controversy-mapping/pre-processing/sentence_filtering/date_filtering.py)
- A table of text snippets from up to 100 randomly sampled texts from the peak period (round robin sampling approach) (controversy-mapping/trend-analysis/py-scr/wordclouds/)

---

### 6. controversy-mapping / semantic-maps

This stage generates semantic representations of the discourse by mapping textual similarity between sentence chunks and actor positions in a reduced embedding space.

The workflow is based on multilingual sentence embeddings and combines dimensionality reduction and clustering techniques to identify structures across themes and countries.

> Note: This step depends on the sentence-filtering pipeline having already been executed.

**Steps involved**:
1. Load chunked sentence data and corresponding embeddings
2. Cluster embeddings using HDBSCAN
3. Reduce embedding dimensions using UMAP
4. Calculate actor-level embeddings using mean pooling
5. Generate interactive semantic visualisations using Plotly

**Input Data**
The pipeline expects:
- Chunked sentence datasets (.parquet)
- precomputed embedding arrays (.npy)
- Actor mapping files per country

***Example inputs***:
| File                                | Description                     |
| ----------------------------------- | ------------------------------- |
| `{country}_{theme}_chunked.parquet` | Chunked sentences with metadata |
| `{country}_{theme}_embeddings.npy`  | Sentence embeddings             |
| `actor_mapping.json`                | Mapping of sources to actors    |

Embeddings are expected:
```bash(!)
controversy-mapping/semantic-mapping/output/embeddings/
```

Outputs:
- Reduced embedding coordinates for text chunks and actors
- Clustered semantic space
- Intermediate data for final visualisations

#### 6.1 Embedding & Clustering

Sentence embeddings are generated using multilingual sentence-transformer models, allowing texts across different languages to be represented in a shared semantic space.

The pipeline then:

* Applies HDBSCAN to identify semantic clusters
* Uses UMAP for dimensionality reduction and visualisation
* Computes average actor embeddings through mean pooling, enabling actors to be positioned relative to the discourse they produce, based on the represented themes.

This makes it possible to compare:

* Semantic proximity between discourse clusters
* Actor positioning within discourse space
* Cross-country and cross-theme similarities

Sentence embeddings are generated using multilingual sentence-transformer models, allowing texts across different languages to be represented in a shared semantic space.

The pipeline then:

Applies HDBSCAN to identify semantic clusters
Uses UMAP for dimensionality reduction and visualisation
Computes average actor embeddings through mean pooling, enabling actors to be positioned relative to the discourse they produce

This makes it possible to compare:

* Semantic proximity between discourse clusters
* Actor positioning within discourse space
* Cross-country and cross-theme similarities

Output

The main output is an interactive UMAP visualisation exported as HTML:

```bash(!)
controversy-mapping/semantic-mapping/plots/country_plots/{country}_{theme}_umap.html
```

The visualisation includes:

* Annotated text chunk (with publication date, text,)
* Text chunk positions
* Cluster structures
* Actor positions in semantic space

These outputs are later used in the final socio-semantic maps generated in the final-plots pipeline.

Parameters

The clustering and dimensionality reduction parameters are configured using a shared baseline setup. The have been adapted to each visual output accordingly. A ```Dimension configs.yml``` file has been generated containing parameters for each map for recreational purposes.

***HDBSCAN***
| Parameter                   | Value     |
| --------------------------- | --------- |
| `min_cluster_size`          | 15        |
| `min_samples`               | 1         |
| `metric`                    | euclidean |
| `cluster_selection_epsilon` | 0.05      |
| `cluster_selection_method`  | leaf      |

***UMAP***
| Parameter      | Value     |
| -------------- | --------- |
| `n_neighbors`  | 40        |
| `n_components` | 20        |
| `min_dist`     | 0.09      |
| `metric`       | euclidean |

***Execution***
The pipeline is executed from the semantic-mapping directory:

```bash(!)
python -m cluster_fun.make_da_map --country {country} --theme {theme}
```

Supported themes:
`lgb`, `migration`, `woke`

Example usage: 
```bash!
python -m cluster_fun.make_da_map --country DK --theme migration
```

**Special Cases**

For Sweden (SE), sources containing flashback are automatically excluded from the dataset before mapping.

---

### 7. controversy-mapping / final-plots (visualisations for report)

This is the final output stage where analytical results are turned into visual deliverables.

Researchers provided their analysis for both peak periods and semantic maps.

**Peak detection**
Based on the provided materials from peak periods of activity, researchers were asked to determine whether a period of activity was meaningful (event, shared discourse, etc.). The annotated peaks are highlighted on the final visualisations.

**Semantic maps**
After the semantic maps were generated, researchers reviewed the maps and identify areas of interest, particularly regions where a controversy appears to be present within the semantic space. Researchers then analyse and annotate these areas by defining coordinate boundaries directly on the maps.

The resulting coordinates are returned and plotted on top of the semantic maps as highlighted regions. This allows the final visualisations to combine computational semnatic mapping with qualitative researcher interpretation and contextual analysis.

Thus the full worklow for all the visual output is:

#### Peak Streamgraphs
- Built using aggregated actor activity over time
- Smoothed and normalised weights
- Annotated with detected peaks from external Excel inputs
- Exported as `.png` and `.pdf`

#### Socio-semantic Maps
- Based on UMAP-reduced embeddings
- Show distribution of text chunks and actor positions
- Include annotated regions from external Excel inputs
- Exported as high-resolution images

Main scripts:
- `gen_final_peaksgraphs.py` → generates streamgraphs and peak tables
- `gen_final_semantic_maps.py` → generates semantic maps

A helper script (`gen_all_maps.sh`) orchestrates the full plotting pipeline, including environment setup and dependencies for static image rendering (e.g. Plotly + Kaleido).

---

### 8. documentation-tables (Reporting Outputs)

This step produces structured outputs for reporting purposes.

Examples:
- Peak summary tables (exported as `.docx`)
- Aggregated statistics for report

Tables are generated directly from annotated peak data and linked to the visual outputs.


---

## Requirements

Dependencies are split across environments:

- `./requirements_environment.txt` → main pipeline dependencies  
- `./controversy-mapping/final_plots/requirements_finalplots.txt` → plotting-specific dependencies 
- `./controversy-mapping/semantic-mapping/environment_semanticmaps.yml` → embedding and clustering. 

Key libraries include:
- NLP: `spaCy`, `huspaCy`, `transformers`, `sentence-transformers`
- Data processing: `pandas`, `numpy`
- Visualisation: `matplotlib`, `plotly`
- Scraping & IO: `Scrapy`, `pytubefix`, `yt-dlp`, `telepathy`, `aiohttp`
