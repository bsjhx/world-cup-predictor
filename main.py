import sys
from agent import run_agent

def print_usage():
    print("Usage: python main.py <team1> <team2> [context]")
    print("\nExamples:")
    print('  python main.py Mexico "South Africa"')
    print('  python main.py Mexico "South Africa" "First match, Mexico is host"')
    print('  python main.py Brazil Argentina "Group stage match"')
    print('\nNote: Use quotes for team names with spaces')

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("❌ Error: Not enough arguments\n")
        print_usage()
        sys.exit(1)

    team1 = sys.argv[1]
    team2 = sys.argv[2]
    context = sys.argv[3] if len(sys.argv) > 3 else None

    # Build the prompt
    if context:
        prompt = f"""Predict the World Cup 2026 match between {team1} and {team2}.

Context: {context}

Consider this context when making your prediction - it may affect home advantage, motivation, or other factors."""
    else:
        prompt = f"Predict the World Cup 2026 match between {team1} and {team2}."

    print("=" * 80)
    print(f"🏆 WORLD CUP 2026 PREDICTION")
    print("=" * 80)
    print(f"Match: {team1} vs {team2}")
    if context:
        print(f"Context: {context}")
    print("=" * 80)
    print("\n")

    # Run the agent
    result = run_agent(prompt, verbose=True)

    print("\n" + "=" * 80)
    print("📊 PREDICTION RESULT")
    print("=" * 80)
    print(result)
    print("=" * 80)