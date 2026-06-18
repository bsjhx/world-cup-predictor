import sys

from src.arguments import arguments_parser

def main():
    """Main entry point with argparse command structure"""
    parser = arguments_parser()
    # Parse arguments
    args = parser.parse_args()

    # If no command provided, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()