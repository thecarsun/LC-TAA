@echo off
echo Starting LC-TAA data update...
echo %date% %time%

cd C:\Users\Car\grepos\LC-TAA

echo Running scraper...
py src/scrape_tracker.py

echo Pushing to GitHub...
git add data/processed/cases.csv data/processed/filters.json data/processed/last_run.txt
git commit -m "Automated data update %date%"
git push

echo Done!
echo %date% %time%