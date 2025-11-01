from typing import Dict

from models.person import Person


class Formatter:
    """
    Formats the expense calculation results for output.
    """

    @staticmethod
    def format_results(people: Dict[str, Person]) -> str:
        """
        Format the expense calculation results as a string.

        Args:
            people: Dictionary mapping person names to Person objects

        Returns:
            Formatted string with results
        """
        if not people:
            return "No expenses found."

        lines = ["Expense Summary:", "---------------"]

        # Sort people by name for consistent output
        for name in sorted(people.keys()):
            person = people[name]
            lines.append(f"{person.name} owes ${person.total_owed:.2f}")
            lines.append(f"  Included in: {', '.join(sorted(person.items))}")
            lines.append("")

        return "\n".join(lines)