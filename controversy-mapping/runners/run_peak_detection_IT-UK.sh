source /work/YOU-DARE/environment/bin/activate

cd /work/YOU-DARE/controversy-mapping/trend-analysis/

python -m peak_detection --data-dir "/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data/IT"

python -m peak_detection --data-dir "/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data/UK"

echo "Peak detection done"