# LC-TAA (Legal Challenges against the Trump Administration Actions)

**BACKGROUND/MOTIVATION**

It's hard to keep up with all the legal litigations and challenges against the Trump Administration's many actions.
I've been following the tracker created by [Just Security.Org](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/).

My motivation is to build a automated visual dashboard to help me keep track of all the cases/statuses/outcomes and to get 
a better understanding of the trends in the different areas over time.


### WHAT

**This project will touch:**
- Data collection (web scraping)
- Data ingestion
- Change detection
- Data visualization
- Canonical data model
- Auto-generated outputs (reports, dashboards)
- Github actions for automation

**Ethical and Responsible Data Use**
- This project only uses **publicly available data** displayed on [Just Security.Org](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/) litigation tracker page
- Scraping is done with respect to the site terms of use AND checking with [robots.txt](https://www.justsecurity.org/robots.txt) to ensure compliance with their guidelines
- Please consider supporting the [Just Security.Org](https://www.justsecurity.org/donate/) if you find their work valuable
- Data is not republished as raw content; it is structured and automated for visualization and analysis
- This project does **not make legal or political judgments** about the content of cases
- Data used in this project is credited to [Just Security. Org](https://www.justsecurity.org/) as the original source of the tracker data


![robots.txt](https://github.com/thecarsun/LC-TCA/blob/main/images/robotstxt.png)


### PIPELINE

```
+-----------------+
| Justice Org     |
+-----------------+
         |
         v
+----------------------+
| Python data pipeline |
+----------------------+
           | 
           v
+-----------------+
| Justice Org     |
| Website Scraper |
+-----------------+
         | 
         v
+-----------------+
| Structured data |
|     (CSV)       |
+-----------------+
         |
         v
 +----------------+
 | GitHub Actions |
 +----------------+
         |
         v
+----------------+
| output to live |
| Dashboard      | 
| (Streamlit.io) |
+----------------+
```                                                                                   


### TECH

**Web Scraping**

- Python
- Playwright (headless Chromium)
- Tried BeautifulSoup - did not obtain results desired

**Data Processing**

- Pandas

**Visualization & Dashboard**
- Streamlit.io
- Plotly 

**Automation & Version Control**
- Git/GitHub
- GitHub Actions

### LEARNINGS

- JustSecurity renders the table via JavaScript — requests/BeautifulSoup 
  cannot see it; a headless browser (Playwright) works instead

- GitHub Actions cloud IPs are blocked by some sites — scraping must run locally from my computer
  part of the automation will be scheduled to run locally  

- Python version matters — Playwright requires 3.9-3.12; avoid 3.13/3.14 *Note to self: remember this*

- UTF-8 encoding must be declared explicitly (utf-8-sig) for cross-platform CSV compatibility. I had gone through many many
  painful hours troubleshooting this error and resulting in - grey hairs

- Playwright dependencies (playwright) must not be in requirements.txt for Streamlit Cloud

- Filter values (Issue, Executive Action) are not table columns — they are 
  stored in dropdown widgets and must be scraped separately per filter value


### STATUS

Dashboard: Live at [LC-TAA](https://lc-taa.streamlit.app/) 

### MOOD

Happy :) 

*If you like this project and want to see more, please let me know! Feel free to reach out with any feedback/questions/suggestions. Thank you*