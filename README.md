# University Admission Tracker

Scrapes Reddit to track admission offers, rejections, scholarships, pillar breakdowns, and sentiment analysis for universities.

## Universities

| University | Website | Admission Report | Sentiment Report |
|---|---|---|---|
| SUTD | [sutd.edu.sg](https://www.sutd.edu.sg) | [View](https://htmlpreview.github.io/?https://github.com/rajkumar82/universitytracker/blob/master/universities/sutd/data/report.html) | [View](https://htmlpreview.github.io/?https://github.com/rajkumar82/universitytracker/blob/master/universities/sutd/data/sentiment_report.html) |
| Plaksha | [plaksha.org](https://plaksha.org) | [View](https://htmlpreview.github.io/?https://github.com/rajkumar82/universitytracker/blob/master/universities/plaksha/data/report.html) | [View](https://htmlpreview.github.io/?https://github.com/rajkumar82/universitytracker/blob/master/universities/plaksha/data/sentiment_report.html) |
| SNU Noida | [snu.edu.in](https://snu.edu.in) | [View](https://htmlpreview.github.io/?https://github.com/rajkumar82/universitytracker/blob/master/universities/snu_noida/data/report.html) | [View](https://htmlpreview.github.io/?https://github.com/rajkumar82/universitytracker/blob/master/universities/snu_noida/data/sentiment_report.html) |

## Setup

```bash
pip install requests
python main.py
```

Use `--reparse` to reprocess all existing records when keywords or topics change:

```bash
python main.py --reparse
```

## Adding a new university

1. Create a folder (e.g. `universities/ntu/`) with a `settings.json` inside — copy `universities/sutd/settings.json` as a template
2. Add the folder to the outer `settings.json`:

```json
{
  "folders": ["universities/sutd", "universities/ntu"]
}
```

3. Run `python main.py` — each folder's data and reports are kept separate

## Adding URLs, keywords or sentiment topics

Edit the university's `settings.json` to:
- Add Reddit thread URLs under `"urls"`
- Update keyword patterns for scholarships, pillars, nationality and status under `"keywords"`
- Add or edit sentiment topics under `"topics"`

No code changes needed.
