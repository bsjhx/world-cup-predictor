
import sys
import argparse
from src.commands import *


def arguments_parser():
    parser = argparse.ArgumentParser(
        prog='wc2026_predictor',
        description='World Cup 2026 Match Predictor - AI-powered football predictions',
        epilog='For more information, see README.md'
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title='commands',
        description='Available commands',
        dest='command',
        help='Command to execute'
    )

    # ==================== PREDICT COMMAND ====================
    predict_parser = subparsers.add_parser(
        'predict',
        help='Predict a single match between two teams',
        description='Predict the outcome of a World Cup match between two national teams'
    )
    predict_parser.add_argument(
        'team1',
        type=str,
        help='First team name (use quotes if it contains spaces)'
    )
    predict_parser.add_argument(
        'team2',
        type=str,
        help='Second team name (use quotes if it contains spaces)'
    )
    predict_parser.add_argument(
        '-c', '--context',
        type=str,
        default=None,
        help='Additional context for the prediction (e.g., "Group stage", "Host nation advantage")'
    )
    predict_parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress tool call output (only show final prediction)'
    )
    predict_parser.set_defaults(func=cmd_predict)

    # ==================== BATCH COMMAND ====================
    batch_parser = subparsers.add_parser(
        'batch',
        help='Predict all NA matches up to a given ID',
        description='Batch predict multiple matches with NA scores up to a maximum match ID'
    )
    batch_parser.add_argument(
        'max_id',
        type=int,
        help='Maximum match ID to predict (inclusive)'
    )
    batch_parser.add_argument(
        '-o', '--output',
        type=str,
        default='predictions.csv',
        help='Output CSV file path (default: predictions.csv)'
    )
    batch_parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    batch_parser.set_defaults(func=cmd_batch)

    # ==================== LIST-TEAMS COMMAND ====================
    list_teams_parser = subparsers.add_parser(
        'list-teams',
        help='List all valid team names',
        description='Display all valid team names from the database'
    )
    list_teams_parser.set_defaults(func=cmd_list_teams)

    # ==================== UPDATE-RESULTS COMMAND ====================
    update_results_parser = subparsers.add_parser(
        'update-results',
        help='Update match results with actual scores from a file',
        description='Update results.csv with actual match scores from updated_results.csv'
    )
    update_results_parser.add_argument(
        'updated_file',
        type=str,
        nargs='?',
        default='data/updated_results.csv',
        help='CSV file with updated scores (default: data/updated_results.csv)'
    )
    update_results_parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/results.csv',
        help='Output CSV file path (default: data/results.csv)'
    )
    update_results_parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    update_results_parser.set_defaults(func=cmd_update_results)

    return parser