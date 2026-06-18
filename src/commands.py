import sys
from pathlib import Path
from src.agent import run_agent
from src.tools import get_all_team_names, load_data
from src.predict_batch import predict_na_matches, save_predictions
from src.update_results import load_updated_results, update_matches, save_updated_results

def cmd_predict(args):
    """Handle the 'predict' command - single match prediction"""
    team1_input = args.team1
    team2_input = args.team2
    context = args.context

    # Get all valid team names
    all_teams = get_all_team_names()

    # Validate team1
    if team1_input not in all_teams:
        print(f"❌ Error: Team '{team1_input}' not found in database")
        print("\n💡 To see all valid team names, run:")
        print('   python src/main.py list-teams')
        sys.exit(1)

    # Validate team2
    if team2_input not in all_teams:
        print(f"❌ Error: Team '{team2_input}' not found in database")
        print("\n💡 To see all valid team names, run:")
        print('   python src/main.py list-teams')
        sys.exit(1)

    # Build the prompt
    if context:
        prompt = f"""Predict the World Cup 2026 match between {team1_input} and {team2_input}.

Context: {context}

Consider this context when making your prediction - it may affect home advantage, motivation, or other factors."""
    else:
        prompt = f"Predict the World Cup 2026 match between {team1_input} and {team2_input}."

    # Display header
    print("=" * 80)
    print(f"🏆 WORLD CUP 2026 PREDICTION")
    print("=" * 80)
    print(f"Match: {team1_input} vs {team2_input}")
    if context:
        print(f"Context: {context}")
    print("=" * 80)
    print("\n")

    # Run the agent
    result = run_agent(prompt, verbose=not args.quiet)

    # Display result
    print("\n" + "=" * 80)
    print("📊 PREDICTION RESULT")
    print("=" * 80)
    print(result)
    print("=" * 80)


def cmd_batch(args):
    """Handle the 'batch' command - batch predictions up to max_id"""
    max_id = args.max_id
    output_file = args.output or "predictions.csv"
    verbose = not args.quiet

    # Run batch predictions
    predictions_df = predict_na_matches(max_id, verbose=verbose)

    if len(predictions_df) > 0:
        save_predictions(predictions_df, output_file)
    else:
        print(f"No matches found with ID <= {max_id}")


def cmd_list_teams(args):
    """Handle the 'list-teams' command"""
    teams = get_all_team_names()

    print("=" * 80)
    print(f"📋 ALL VALID TEAM NAMES ({len(teams)} teams)")
    print("=" * 80)
    print()

    for idx, team in enumerate(teams, 1):
        # Add quotes if team name has spaces
        display_name = f'"{team}"' if ' ' in team else team
        print(f"{idx:3}. {display_name}")

    print()
    print("=" * 80)
    print("💡 Use these exact names (with quotes if they contain spaces)")
    print("   Example: python src/main.py predict \"United States\" Mexico")
    print("=" * 80)


def cmd_update_results(args):
    """Handle the 'update-results' command"""
    updated_file = args.updated_file
    output_file = args.output
    verbose = not args.quiet

    # Validate updated_file exists
    if not Path(updated_file).exists():
        print(f"❌ Error: File '{updated_file}' not found")
        sys.exit(1)

    # Load both files
    print("=" * 80)
    print("🔄 UPDATING MATCH RESULTS")
    print("=" * 80)
    print(f"📂 Loading data files...")
    print(f"   Source: data/results.csv")
    print(f"   Updates: {updated_file}")

    results_df = load_data()  # from tools.py
    updated_df = load_updated_results(updated_file)

    # Update matches
    updated_df_final, stats = update_matches(results_df, updated_df, verbose)

    # Save results
    save_updated_results(updated_df_final, output_file)

    # Print summary
    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE!")
    print("=" * 80)
    print(f"  ✅ Updated:   {stats['updated_count']} matches")
    print(f"  ⏭️  Skipped:   {stats['skipped_count']} matches (no new data)")
    print(f"  ⚠️  Not found: {stats['not_found_count']} matches")
    print(f"  💾 Saved to:  {output_file}")
    print("=" * 80)
