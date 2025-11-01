import csv
from pathlib import Path
from typing import List

from models.expense import Expense


class CSVHandler:
    """
    Handles reading expense data from CSV files.
    """

    @staticmethod
    def read_expenses(file_path: str) -> List[Expense]:
        """
        Read expenses from a CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of Expense objects parsed from the CSV
        """
        expenses = []
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        with open(file_path, 'r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if not all(key in row for key in ["ItemName", "TotalPrice", "PeopleIncluded"]):
                    raise ValueError(f"CSV file is missing required headers: ItemName, TotalPrice, PeopleIncluded")

                try:
                    total_price = float(row["TotalPrice"])
                except ValueError:
                    raise ValueError(f"Invalid total price: {row['TotalPrice']} for item {row['ItemName']}")

                # Split the PeopleIncluded string into a list of names
                people_included = row["PeopleIncluded"].split()

                expense = Expense(
                    item_name=row["ItemName"],
                    total_price=total_price,
                    people_included=people_included
                )
                expenses.append(expense)

        return expenses