## Peak detection using isolation forest

Bruger isolation forest til at detektere peaks.

Kør fra directory YOU-DARE/controversy-mapping/trend-analysis som modul med:

`python -m run_peak_detection --data-path "path/to/importdata.jsonl"`

Output i form af jsonlines under output directory med tidspunkt + is_anomaly variabel. Spytter lige nu også plot ud.

### Vægte

Mulighed for at tilføje vægte baseret på samlet source-activity (antal tekster i alt) med flag:

`--use-weights`

Default er false. 

Finder selv reduced data ud fra input data sti (antager {country}_{theme}_indexed.jsonl filnavn og reduced data som {country}_reduced). Hvis det ikke kan findes, gives advarsel, og der fortsættes uden brug af vægte.

Vægt er udregnet som 1 / (log(source_text_counts) / sum(log(source_text_counts))).

"weighted" tilføjes til filnavne.