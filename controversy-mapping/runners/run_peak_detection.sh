source /work/YOU-DARE/environment/bin/activate

cd /work/YOU-DARE/controversy-mapping/trend-analysis/

python -m peak_detection --data-dir "/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data"

echo "Peak detection done"

#python "/work/YOU-DARE/controversy-mapping/sentence_filtering/date_filtering.py"

#echo "Text sampling done"

#python "/work/YOU-DARE/controversy-mapping/trend-analysis/py-scr/extract_words_peaks_spacy.py"

#echo "Word extraction done"

#python "/work/YOU-DARE/controversy-mapping/trend-analysis/py-scr/peaks_to_clouds.py"

#echo "Word clouds done"