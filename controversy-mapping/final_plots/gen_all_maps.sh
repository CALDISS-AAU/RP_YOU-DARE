source /work/YOU-DARE/controversy-mapping/final_plots/env/bin/activate

# dependencies for kaleido/plotly static images
sudo apt update 
sudo apt-get install libnss3 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2t64 -y
plotly_get_chrome -y

# paths to chome
export CHROME_PATH=/work/YOU-DARE/controversy-mapping/final_plots/env/lib/python3.12/site-packages/choreographer/cli/browser_exe/chrome-linux64/chrome
export PATH=/work/YOU-DARE/controversy-mapping/final_plots/env/lib/python3.12/site-packages/choreographer/cli/browser_exe/chrome-linux64/chrome:$PATH

cd /work/YOU-DARE/controversy-mapping/final_plots/

python -m gen_final_peaksgraphs

echo "Peak streamgraphs done"

python -m gen_final_semantic_maps

echo "Socio-semantic maps done"