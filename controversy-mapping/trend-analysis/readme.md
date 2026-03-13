## Peak detection using isolation forest

Bruger isolation forest til at detektere peaks.

Kør fra directory YOU-DARE/controversy-mapping/trend-analysis som modul med:

`python -m peak_detection --data-path "path/to/importdata.jsonl"`

Output i form af json under output directory i lande mappe, fil navngivet efter tema. Spytter lige nu også plots ud.

Kan også tage directory som input:

`python -m peak_detection --data-dir "path/to/importdatadirectory"`


## Full run med vægts

For at finde alle peaks og lave alle visualiseringer kør:

`python -m peak_detection --data-dir "/work/YOU-DARE/sentence_filtering/indexed_data_OG_lan_ONLY" --use-weights`

**OBS**: Køres funktionen uden data-input, er default at køre på hele directory: /work/YOU-DARE/sentence_filtering/indexed_data

### Vægte

Mulighed for at tilføje vægte baseret på samlet source-activity (antal tekster i alt) med flag:

`--use-weights`

Default er false. 

Finder selv reduced data ud fra input data sti (antager {country}_{theme}_indexed.jsonl filnavn og reduced data som {country}_reduced). Hvis det ikke kan findes, gives advarsel, og der fortsættes uden brug af vægte.

Vægt er udregnet som 1 / (log(source_text_counts) / sum(log(source_text_counts))).

"weighted" tilføjes til filnavne.