# Super Lotto Data Analysis System (DLT Analyzer)

The Super Lotto Data Analysis System is a Web application system designed for historical data analysis, number recommendations, and review queries regarding the China Super Lotto.

## Project Introduction

This system provides complete management of Super Lotto historical data, statistical analysis of number frequencies, intelligent number recommendations, draw verification, and other functions to help lottery players better analyze number trends.

## Features

### 📊 Data Management
- Automatically fetch Super Lotto historical draw data
- Local persistent storage
- Support export in CSV/TXT formats

### 📈 Statistical Analysis
- Number appearance frequency statistics
- Customizable analysis period range (last N periods)
- Comprehensive analysis of Front Zone + Back Zone

### 🎯 Number Recommendation
- **Intelligent Recommendation**: Smart number selection based on historical frequency analysis
- **Random Recommendation**: True random number generation within a custom range

### 🔍 Review & Verification
- Input issue number and selected numbers for review
- Automatically calculate match status
- View historical review records

### 💰 Prize Inquiry
- Winning judgment (supports comparison with any selected numbers)
- Prize rule explanations
- Select draw issue number

## Technology Stack

- **Backend**: Python Flask + FastAPI
- **Frontend**: HTML5 + CSS3 + JavaScript (Native)
- **Data Storage**: JSON local files

## Directory Structure

```
.
├── app.py                  # Flask Web application entry
├── dlt_core.py             # Core business logic module
├── dlt/                    # FastAPI version backend
│   ├── app.py              # FastAPI application
│   └── dlt_core.py         # Core logic
├── templates/
│   └── index.html          # Frontend page
├── requirements.txt        # Python dependencies
└── .dlt_data/              # Data storage directory
    ├── history.json        # Historical draw data
    ├── raw_history.json    # Raw complete data
    ├── predictions.json    # Recommendation data
    └── latest_stats.json   # Latest statistics
```

## Quick Start

### Environment Requirements

- Python 3.8+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

**Method 1: Flask Version**
```bash
python app.py
```

**Method 2: FastAPI Version**
```bash
cd dlt
uvicorn app:app --reload --port 8000
```

Access `http://localhost:5000` (Flask) or `http://localhost:8000` (FastAPI)

## API Interfaces

| Interface | Method | Description |
|------|------|------|
| `/api/latest` | GET | Get latest draw information |
| `/api/history` | GET | Get historical draw list |
| `/api/history/raw` | GET | Get full raw data |
| `/api/stats` | GET/POST | Number frequency statistics |
| `/api/recommend` | GET/POST | Generate recommended numbers |
| `/api/review` | POST | Review verification |
| `/api/prize-check` | POST | Winning check |
| `/api/prize-rules` | GET | Prize rules |
| `/api/all-combos` | GET | Query all combinations |
| `/api/appeared-combos` | GET | Appeared combinations |
| `/api/random-unopened` | GET | Random unopened combinations |
| `/api/export/csv` | GET | Export CSV |
| `/api/export/txt` | GET | Export TXT |
| `/api/fetch` | POST | Fetch latest data |
| `/api/archive` | GET | Review history records |

## Prize Rules

Super Lotto Winning Rules:
- **1st Prize**: Front Zone 5 + Back Zone 2 fully matched (Floating Prize)
- **2nd Prize**: Front Zone 5 + Back Zone 1 matched (Floating Prize)
- **3rd Prize**: Front Zone 5 fully matched (10,000 Yuan)
- **4th Prize**: Front Zone 4 + Back Zone 2 (3,000 Yuan)
- **5th Prize**: Front Zone 4 + Back Zone 1 matched (300 Yuan)
- **6th Prize**: Front Zone 4 fully matched (200 Yuan)
- **7th Prize**: Front Zone 3 + Back Zone 2 (100 Yuan)
- **8th Prize**: Front Zone 3 + Back Zone 1 matched (15 Yuan)
- **9th Prize**: Front Zone 3 matched OR Back Zone 2 matched (5 Yuan)

## Usage Instructions

1. **First Use**: Click the "Fetch Data" button to get the latest draw history
2. **View Analysis**: Check number frequencies in the "Statistical Analysis" tab
3. **Get Recommendations**: Get smart recommended numbers in the "Number Recommendation" tab
4. **Review Verification**: Select an issue number, enter selected numbers to review
5. **Export Data**: Export historical data for offline analysis

## License

This project is for learning and research purposes only. Please comply with relevant laws and regulations. Lottery betting involves risk; please consume rationally.