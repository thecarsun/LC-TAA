# LC-TCA

**BACKGROUND/MOTIVATION**

It's hard to keep up with all the legal litigations and challenges against the Trump Administration's many actions.
I've been following the tracker created by [Just Security.Org](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/).

My motivation is to build a automated visual dashboard to help me keep track of all the cases/statuses/outcomes and to get 
a better understanding of the trends in the different areas over time.


#WHAT

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


# ARCHETECTURE

```
+-----------------+
| Justice Org site|
+-----------------+
         |
         v
+----------------------+
| Python data pipeline |
+----------------------+
           | 
           v
+-----------------+
| Structured data |
|   (CSV/JSON)    |
+-----------------+
         |
         v
 +----------------+
 | Auto-generated |
 | summaries      |
 +----------------+
         |
         v
+----------------+
| Dashboard      | 
| (Streamlit.io) |
+----------------+
```



# TECH

**Web Scraping**
- Python
 

**Data Processing & Normalization**


**Change Detection & Reporting**
- Markdown

**Visualization & Dashboard**
- Streamlit.io

**Automation & Version Control**
- Git/GitHub
- GitHub Actions


# LEARNINGS

# STATUS

# MOOD