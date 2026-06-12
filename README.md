# World Cup 2026 Predictor

An AI-powered football match prediction system that uses historical data and LLM agents to predict World Cup match outcomes.

## Overview

This system uses an LLM agent with function calling to analyze historical football match data and predict World Cup 2026 match outcomes. The agent intelligently calls various statistical analysis tools to gather data about teams' form, head-to-head records, Elo ratings, and more.

## Features

- **Single Match Predictions**: Predict any matchup between national teams
- **Batch Predictions**: Predict multiple matches automatically
- **Data-Driven Analysis**: Uses 150+ years of international football match history
- **8 Statistical Tools**: Weighted form, competitive record, Elo ratings, head-to-head, neutral venue stats, and more
- **Smart Context Handling**: Considers tournament stage, host advantage, and other contextual factors
- **Automatic Tool Registration**: New analysis tools are automatically available to the agent

## Quick Start

### Prerequisites

- Python 3.9+
- OpenAI-compatible API endpoint

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd wc2026_predictor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
API_KEY=your_api_key_here
URL=https://your-openai-compatible-endpoint
```

## Usage

### Single Match Prediction

```bash
# Basic prediction
python main.py Brazil Argentina

# With context
python main.py "United States" Mexico "USA at home as co-host"

# Teams with spaces need quotes
python main.py "South Africa" "Saudi Arabia"
```

### Batch Predictions

Predict all matches with NA scores up to a specific ID:

```bash
python main.py 49300
```

This will:
- Load all matches with NA scores up to ID 49300
- Predict each match sequentially
- Save results to `predictions.csv`
- Append new predictions and overwrite duplicates

### List Valid Team Names

```bash
python src/list_teams.py

# Filter by World Cup year
python src/list_teams.py 2022
```

## Project Structure

```
wc2026_predictor/
├── src/
│   ├── agent.py              # LLM agent orchestration
│   ├── tools.py              # Statistical analysis tools
│   ├── tool_registry.py      # Auto tool registration
│   ├── main.py               # CLI entry point
│   ├── predict_batch.py      # Batch prediction engine
│   ├── prompts.py            # System prompts
│   └── list_teams.py         # Team listing utility
├── data/
│   ├── results.csv           # Match history (150+ years)
│   ├── elo_ranking.tsv       # Current Elo ratings
│   └── en.teams.tsv          # Country name mappings
├── test/
│   └── test_predictions.py   # Testing framework
├── main.py                   # Convenience wrapper
├── requirements.txt
└── CLAUDE.md                 # Developer guide
```

## Analysis Tools

The agent uses 8 specialized tools:

1. **get_weighted_form**: Recent form with time decay and tournament importance (35% weight)
2. **get_competitive_record**: Performance in competitive matches only (25% weight)
3. **get_elo_rating**: Current world ranking and Elo rating (20% weight)
4. **get_head_to_head**: Historical matchup records (10% weight)
5. **get_neutral_venue_stats**: Performance at neutral venues (10% weight)
6. **get_recent_form**: Basic win/draw/loss record
7. **get_tournament_history**: Tournament-specific performance
8. **get_goals_stats**: Attacking and defensive statistics

## Example Output

```
================================================================================
🏆 WORLD CUP 2026 PREDICTION
================================================================================
Match: Brazil vs Argentina
================================================================================

🔧 Calling tool: get_elo_rating({'team': 'Brazil'})
🔧 Calling tool: get_elo_rating({'team': 'Argentina'})
🔧 Calling tool: get_weighted_form({'team': 'Brazil', 'last_n': 20})
...

================================================================================
📊 PREDICTION RESULT
================================================================================
Predicted Score: Brazil 0 - 1 Argentina
Confidence: Medium

Key Factors:
- Weighted form: Argentina 2.19/3.0 vs Brazil 1.82/3.0
- Elo rating: Argentina 2115 (rank 2) vs Brazil 1991 (rank 5)
- Competitive record: Argentina 61.8% win rate vs Brazil 38.7%
- Head-to-head: Argentina leads recent matchups

Reasoning:
Argentina's superior recent form, higher Elo rating, and better competitive
record suggest they hold the edge. Given typical World Cup scoring patterns
in elite matchups, a narrow Argentina win is most likely.
================================================================================
```

## Adding New Tools

1. Define a function in `src/tools.py` with type hints:
```python
@registry.register
def get_my_stat(team: str, last_n: int = 10) -> dict:
    """
    Description of what this tool does

    team: Team name
    last_n: Number of matches to analyze
    """
    # Your implementation
    return {"stat": "value"}
```

2. The tool is automatically registered and available to the agent!

## Testing

Run the test suite to evaluate predictions against historical World Cup data:

```bash
python test/test_predictions.py

# View results only
python test/test_predictions.py --only-results
```

## Configuration

### Model Selection

Edit `src/agent.py`:
```python
def run_agent(user_question: str, verbose: bool = True, model="gpt-5"):
```

### Analysis Weights

Modify the system prompt in `src/prompts.py` to adjust how different factors are weighted.

### Data Sources

Point to custom data:
```python
from src.tools import set_data_source
set_data_source("path/to/custom.csv")
```

## Data Format

### results.csv
Columns: `id, date, home_team, away_team, home_score, away_score, tournament, city, country, neutral`

### elo_ranking.tsv
Tab-separated: `rank_idx, world_rank, country, elo, ...`

## Development

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation and development guidelines.

## License

[Your License Here]

## Credits

Match data sourced from international football databases. Elo ratings maintained by various football statistics organizations.
