@echo off
echo Starting LC-TAA data update... C:\Users\Car\grepos\LC-TAA\update_log.txt
echo %date% %time% >> C:\Users\Car\grepos\LC-TAA\update_log.txt

cd C:\Users\Car\grepos\LC-TAA

echo Running scraper... ... >> C:\Users\Car\grepos\LC-TAA\update_log.txt
py src/scrape_tracker.py >> C:\Users\Car\grepos\LC-TAA\update_log.txt 2>&1

echo Pushing to GitHub...  >> C:\Users\Car\grepos\LC-TAA\update_log.txt
git add data/processed/cases.csv data/processed/filters.json data/processed/last_run.txt >> C:\Users\Car\grepos\LC-TAA\update_log.txt 2>&1
git commit -m "Automated data update %date%" >> C:\Users\Car\grepos\LC-TAA\update_log.txt 2>&1
git push >> C:\Users\Car\grepos\LC-TAA\update_log.txt 2>&1

echo Done! >> C:\Users\Car\grepos\LC-TAA\update_log.txt
echo %date% %time% >> C:\Users\Car\grepos\LC-TAA\update_log.txt