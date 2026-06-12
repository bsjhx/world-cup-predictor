# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a World Cup 2026 match prediction system powered by an LLM agent (OpenAI API-compatible) with function calling. The agent analyzes historical football match data to predict outcomes for World Cup matches between national teams.

## Architecture

**Agent-Driven Prediction System:**
- `agent.py`: Core LLM agent orchestration with function calling loop. Uses OpenAI-compatible API (configured via .env). The agent receives a detailed system prompt that guides its analysis methodology and makes function calls to gather data.
- `tools.py`: Statistical analysis functions decorated with `@registry.register` for automatic tool schema generation. Each tool queries the match history dataset (results.csv) using pandas.
- `tool_registry.py`: Automatic tool registration and schema generation from Python type hints. Converts functions to OpenAI-compatible function calling schemas.
- `main.py`: CLI entry point for both single match predictions and batch predictions.
- `predict_batch.py`: Batch prediction engine that loads all NA matches up to a given ID and predicts them sequentially.

**Key Design Pattern:**
Functions in `tools.py` are automatically converted to LLM tools via decorator. The registry extracts parameter types from function signatures and docstrings to generate JSON schemas. The agent calls these tools to gather statistics, then synthesizes predictions.

## Development Commands

### Setup
```bash
# Create virtual environment (Python 3.9+ required)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Create `.env` file with:
```
API_KEY=your_api_key_here
URL=https://your-openai-compatible-endpoint
```

### Running Predictions
```bash
# Single match prediction
python main.py "Team1" "Team2"
python main.py Mexico "South Africa"
python main.py "United States" Paraguay "USA at home as co-host"

# Batch prediction: predict all NA matches up to (including) ID
python main.py 44999
# Outputs to predictions.csv

# List all valid team names
python list_teams.py
```

### Testing
```bash
# Run complete test suite (predicts World Cup 2022 matches)
python test/test_predictions.py

# Show existing results only (no new predictions)
python test/test_predictions.py --only-results
```

**Test Architecture:**
- Test suite uses 5 CSV files (0.csv-4.csv) with progressively more historical data
- Each file has NA scores for World Cup 2022 matches
- Agent makes predictions using only data available in each file
- Predictions compared against actual results in 5.csv
- Supports resume: skips already-predicted matches if re-run
- Outputs: `test/predictions.csv` (results), `test/errors.log`, `test/parsing_errors.log`

### Data Management
```bash
# Set custom data source in code
from tools import set_data_source
set_data_source("path/to/custom.csv")
```

## Key Files

- **data/results.csv**: Complete international football match history (required)
- **data/elo_ranking.tsv**: Current Elo ratings and world rankings for all teams
- **data/former_names.csv**: Historical country name mappings
- **data/shootouts.csv**: Penalty shootout records
- **.env**: API credentials (gitignored)

## Tool System

**Available Analysis Tools** (in tools.py):
- `get_head_to_head`: Historical matchup records between two teams
- `get_recent_form`: Win/draw/loss record and goals for recent matches
- `get_tournament_history`: Performance in specific tournaments (FIFA World Cup, etc.)
- `get_goals_stats`: Attacking/defensive statistics with home/away splits
- `get_weighted_form`: Advanced form metric with time decay and tournament importance weighting
- `get_competitive_record`: Record in non-friendly matches over recent years
- `get_neutral_venue_stats`: Performance at neutral venues (critical for World Cup)
- `get_elo_rating`: Current Elo rating and world ranking for a team

**Adding New Tools:**
1. Define function in `tools.py` with type hints
2. Add `@registry.register` decorator
3. Write docstring with parameter descriptions (format: `param_name: description`)
4. Tool automatically becomes available to agent

**System Prompt Philosophy:**
The agent's system prompt (in agent.py) emphasizes:
- Weighted recent form (40%) > competitive record (30%) > head-to-head (15%) > neutral venue (15%)
- Contextual factors only applied if explicitly provided by user
- World Cup-specific scoring patterns (lower scoring, defensive play)
- Data-driven predictions with explicit confidence levels

## Important Notes

- All team names must match exactly as they appear in results.csv
- The agent uses an OpenAI-compatible API (configured via base_url in .env)
- Data loaded with `@lru_cache()` for performance
- Test framework allows incremental testing with resume capability
- The model parameter in agent.py defaults to "gpt-5" (adjust per your API)
