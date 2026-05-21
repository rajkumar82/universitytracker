# University Admission Tracker

Scrapes Reddit to track admission offers, rejections, scholarships, and pillar breakdowns for universities.

## Universities

| University | Website | Report |
|---|---|---|
| SUTD | [sutd.edu.sg](https://www.sutd.edu.sg) | [View Report](https://htmlpreview.github.io/?https://github.com/rajkumar82/universitytracker/blob/master/sutd/data/report.html) |

## Setup

```bash
pip install requests
python main.py
```

## Adding a new university

1. Create a folder (e.g. `ntu/`) with a `settings.json` inside — copy `sutd/settings.json` as a template
2. Add the folder name to the outer `settings.json`:

```json
{
  "folders": ["sutd", "ntu"]
}
```

3. Run `python main.py` — each folder's data and report are kept separate

## Adding URLs or keywords

Edit the university's `settings.json` (e.g. `sutd/settings.json`) to add Reddit thread URLs or update keyword patterns for scholarships, pillars, nationality, and status detection. No code changes needed.
