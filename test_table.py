from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Test", row_styles=["", "on grey23"])
table.add_column("Col1")
table.add_column("Col2")
table.add_row("A", "1")
table.add_row("B", "2")
table.add_row("C", "3")
console.print(table)
