import sys
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from llm2sh.config import get_settings
from llm2sh.core.processor import QueryProcessor
from llm2sh.core.client import OpenAIClient
from llm2sh.core.validator import SafetyValidator
from llm2sh.core.models import RiskLevel

console = Console()

async def run_cli(query: str) -> int:
    try:
        # Load settings to verify API key
        settings = get_settings()
        if not settings.openai_api_key or "sk-" not in settings.openai_api_key:
            console.print("[bold red]Error:[/] OPENAI_API_KEY environment variable is not set or invalid.")
            console.print("Please set it in your environment or in a [bold].env[/] file at the root of the project.")
            return 1
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/] {e}")
        return 1

    processor = QueryProcessor()
    client = OpenAIClient()
    validator = SafetyValidator()

    with console.status("[bold green]Translating natural language to shell command...", spinner="dots"):
        try:
            messages = processor.build_messages(query)
            result = await client.generate_command(messages)
            result = validator.validate(result)
        except Exception as e:
            console.print(f"\n[bold red]API Error:[/] {e}")
            return 1

    # Check for clarifying question
    if result.clarifying_question:
        console.print(Panel(
            result.clarifying_question,
            title="[bold yellow]Clarifying Question[/]",
            border_style="yellow"
        ))
        return 0

    # Print results beautifully
    console.print()
    console.print(Panel(
        Syntax(result.command, "bash", theme="monokai", line_numbers=False, word_wrap=True),
        title="[bold green]Suggested Command[/]",
        border_style="green"
    ))

    console.print(f"\n[bold cyan]Explanation:[/]\n{result.explanation}\n")

    if result.flag_explanations:
        table = Table(title="Flag Details", show_header=True, header_style="bold magenta", box=None)
        table.add_column("Flag/Argument", style="cyan")
        table.add_column("Meaning", style="white")
        for flag, explanation in result.flag_explanations.items():
            table.add_row(flag, explanation)
        console.print(table)
        console.print()

    # Risk level color formatting
    risk_style = "green"
    risk_icon = "✅"
    if result.risk_level == RiskLevel.CAUTION:
        risk_style = "yellow"
        risk_icon = "⚠️"
    elif result.risk_level == RiskLevel.DANGER:
        risk_style = "bold red"
        risk_icon = "🛑"

    console.print(f"[bold {risk_style}]Risk Level:[/] {risk_icon} {result.risk_level.value.upper()}")
    if result.risk_reason:
        console.print(f"[bold {risk_style}]Warning/Reason:[/] {result.risk_reason}")
        
    console.print(f"[bold dim]Estimated Effect:[/] [dim]{result.estimated_effect}[/]")
    return 0

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        console.print("[bold cyan]llm2sh[/] - Translate plain English into Unix/Linux shell commands.")
        console.print("\n[bold]Usage:[/] python -m llm2sh \"<natural language query>\"")
        console.print("[bold]Example:[/] python -m llm2sh \"find log files modified in the last 3 days\"")
        sys.exit(0)

    query = sys.argv[1]
    exit_code = asyncio.run(run_cli(query))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
