import argparse
import sys
from pathlib import Path

from services.csv_handler import CSVHandler
from services.expense_calculator import ExpenseCalculator
from utils.formatter import Formatter


def main():
    """
    Main entry point for the expense aggregator application.
    """
    parser = argparse.ArgumentParser(description="Aggregate expenses and calculate what each person owes.")
    parser.add_argument("csv_file", help="Path to the CSV file containing expense data")

    args = parser.parse_args()

    try:
        # Read expenses from the CSV file
        expenses = CSVHandler.read_expenses(args.csv_file)

        # Calculate how much each person owes
        people = ExpenseCalculator.calculate_debts(expenses)

        # Format and display the results
        result = Formatter.format_results(people)
        print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
     # Command to run: python main.py files/filename.csv
    main()
