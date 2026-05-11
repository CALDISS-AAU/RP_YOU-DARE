## Semantic mapping on text embeddings using HDBSCAN and UMAP

Bruger en multilingual sentence-transformers til at beregne embeddings af chunked sætninger fra nøgleord.

> **OBS**: før dette køres skal sentence filtering køres.

---
## Overblik

Scriptet kører en pipeline de:
1. Indlæser chunk-embeddings fra '.parquet' og '.npy' filer
2. Clusterer embeedings med **HDBSCAN**
3. Reducerer dimensioner med **UMAP**
4. Beregner aktør-embeddings via mean pooling pr. aktør
5. Genererer en interaktiv HTML-visualisering med **plotly**

---

## Forudsætninger

Scriptet forventer at følgende allerede er kørt:

- **Sentences filtering** – filtrerer og chunker sætninger
- **Embedding-beregning** – genererer embeddings med en multilingual sentence-transformer

--- 

## Input

|FIL | Beskrivelse |
|----|-------------|
| `{country}_{theme}_chunked.parquet` | Chunked sætninger med metadata |
| `{country}_{theme}_embeddings.npy` | Tilhørende embeddings som numpy array |
| `actor_mapping.json` | Mapping fra kilde til aktør pr. land |

Embeddings forventes i:

```
/work/YOU-DARE/controversy-mapping/semantic-mapping/output/embeddings/
```

---

## Brug

Sørg for at stå i `semantic-mapping` dir: `cd ./controversy-mapping/semantic-mapping`.

Aktivér conda miljø.

Kør:

```bash
python -m cluster_fun.make_da_map --country {country} --theme {theme} 
```

### Gyldige lande
`DK`, `ES`, `FR`, `HU`, `IT`, `RO`, `SWE`, `UK`

### Gyldige temaer
`lgb`, `migration`, `woke`

### Eksempel
```bash
python -m cluster_fun.make_da_map --country DK --theme migration
```

---

## Output

En interaktiv UMAP-visualisering gemmes som HTML-fil:
```
./controversy-mapping/semantic-mapping/plots/country_plots/{country}_{theme}_umap.html
```

Plottet viser både chunk, clustering og aktør-positioner i det reducerede rum.

---

## Parametre

Parametre er sat ud fra en generel standard. Disse kan ændres


### HDBSCAN
| Parameter | Værdi |
|-----------|-------|
| `min_cluster_size` | 15 |
| `min_samples` | 1 |
| `metric` | euclidean |
| `cluster_selection_epsilon` | 0.05 |
| `cluster_selection_method` | leaf |

### UMAP
| Parameter | Værdi |
|-----------|-------|
| `n_neighbors` | 40 |
| `n_components` | 20 |
| `min_dist` | 0.09 |
| `metric` | euclidean |

---

## Særlige tilfælde
Kilder der indeholder `flashback` fjernes automatisk fra datasættet. Dette er kun gældende for **Sverige (SE)**