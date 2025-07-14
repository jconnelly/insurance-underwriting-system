"""
Command-line interface for the insurance underwriting system.

This module provides a comprehensive CLI for testing and demonstrating
the underwriting system with various commands and options.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
# from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON

from underwriting.core.engine import UnderwritingEngine
from underwriting.core.models import Application, DecisionType
from underwriting.utils.logging import setup_logging
from underwriting.utils.validation import validate_application_data

# Initialize Typer app and Rich console
app = typer.Typer(
    name="underwriting-cli",
    help="Insurance Underwriting System CLI",
    rich_markup_mode="rich"
)
console = Console()

# Global engine instance
engine: Optional[UnderwritingEngine] = None


def get_engine() -> UnderwritingEngine:
    """Get or create the underwriting engine instance."""
    global engine
    if engine is None:
        engine = UnderwritingEngine()
    return engine


@app.callback()
def main(
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Set logging level"),
    log_file: Optional[str] = typer.Option(None, "--log-file", "-f", help="Log file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Insurance Underwriting System CLI."""
    # Setup logging
    setup_logging(
        level=log_level.upper(),
        log_file=log_file,
        enable_console=verbose,
        enable_file=log_file is not None
    )
    
    if verbose:
        console.print("[green]Underwriting CLI initialized[/green]")


@app.command()
def info():
    """Display system information and available rule sets."""
    try:
        engine = get_engine()
        
        # Create info panel
        info_text = """
[bold blue]Insurance Underwriting System[/bold blue]

[bold]Available Rule Sets:[/bold]
"""
        
        for rule_set_name in engine.get_available_rule_sets():
            rule_info = engine.get_rule_set_info(rule_set_name)
            info_text += f"""
• [bold]{rule_set_name.title()}[/bold] (v{rule_info['version']})
  Description: {rule_info['description']}
  Hard Stops: {rule_info['hard_stops_count']}
  Adjudication Triggers: {rule_info['adjudication_triggers_count']}
  Acceptance Criteria: {rule_info['acceptance_criteria_count']}
"""
        
        console.print(Panel(info_text, title="System Information"))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def evaluate(
    application_file: str = typer.Argument(..., help="Path to application JSON file"),
    rule_set: str = typer.Option("standard", "--rule-set", "-r", help="Rule set to use"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Evaluate a single application from JSON file."""
    try:
        # Load application
        application_path = Path(application_file)
        if not application_path.exists():
            console.print(f"[red]Application file not found: {application_file}[/red]")
            raise typer.Exit(1)
        
        with open(application_path, 'r') as f:
            app_data = json.load(f)
        
        application = Application(**app_data)
        
        # Validate application
        is_valid, errors = validate_application_data(application)
        if not is_valid:
            console.print("[red]Application validation failed:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)
        
        # Process application
        engine = get_engine()
        
        console.print("Processing application...", style="yellow")
        decision = engine.process_application(application, rule_set)
        console.print("[OK] Application processed", style="green")
        
        # Display results
        display_decision(decision, verbose=verbose)
        
        # Save to file if requested
        if output_file:
            save_decision_to_file(decision, output_file)
            console.print(f"[green]Results saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def batch(
    applications_dir: str = typer.Argument(..., help="Directory containing application JSON files"),
    rule_set: str = typer.Option("standard", "--rule-set", "-r", help="Rule set to use"),
    output_file: str = typer.Option("batch_results.json", "--output", "-o", help="Output file for results"),
    stats: bool = typer.Option(True, "--stats", help="Show statistics"),
):
    """Process multiple applications from a directory."""
    try:
        # Load applications
        apps_path = Path(applications_dir)
        if not apps_path.exists():
            console.print(f"[red]Applications directory not found: {applications_dir}[/red]")
            raise typer.Exit(1)
        
        json_files = list(apps_path.glob("*.json"))
        if not json_files:
            console.print(f"[red]No JSON files found in: {applications_dir}[/red]")
            raise typer.Exit(1)
        
        applications = []
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    app_data = json.load(f)
                application = Application(**app_data)
                applications.append(application)
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load {file_path}: {e}[/yellow]")
                continue
        
        if not applications:
            console.print("[red]No valid applications found[/red]")
            raise typer.Exit(1)
        
        # Process applications
        engine = get_engine()
        
        console.print(f"Processing {len(applications)} applications...", style="yellow")
        decisions = engine.batch_process_applications(applications, rule_set)
        console.print("[OK] Batch processing completed", style="green")
        
        # Display results
        display_batch_results(decisions, show_stats=stats)
        
        # Save results
        save_batch_results_to_file(decisions, output_file)
        console.print(f"[green]Results saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def compare(
    application_file: str = typer.Argument(..., help="Path to application JSON file"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
):
    """Compare how an application would be evaluated under different rule sets."""
    try:
        # Load application
        application_path = Path(application_file)
        if not application_path.exists():
            console.print(f"[red]Application file not found: {application_file}[/red]")
            raise typer.Exit(1)
        
        with open(application_path, 'r') as f:
            app_data = json.load(f)
        
        application = Application(**app_data)
        
        # Compare rule sets
        engine = get_engine()
        
        console.print("Comparing rule sets...", style="yellow")
        results = engine.compare_rule_sets(application)
        console.print("[OK] Rule set comparison completed", style="green")
        
        # Display comparison
        display_comparison_results(results)
        
        # Save to file if requested
        if output_file:
            save_comparison_to_file(results, output_file)
            console.print(f"[green]Results saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def generate(
    count: int = typer.Option(10, "--count", "-c", help="Number of applications to generate"),
    output_dir: str = typer.Option("sample_data", "--output", "-o", help="Output directory"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for reproducibility"),
):
    """Generate sample application data for testing."""
    try:
        import sys
        from pathlib import Path
        # Add data directory to path
        data_dir = Path(__file__).parent.parent.parent.parent / "data"
        sys.path.insert(0, str(data_dir))
        from sample_generator import SampleDataGenerator
        
        generator = SampleDataGenerator(seed=seed)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate applications
        console.print(f"Generating {count} applications...", style="yellow")
        
        for i in range(count):
            application = generator.generate_application()
            
            # Save to file
            filename = f"application_{i+1:03d}.json"
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(application.dict(), f, indent=2, default=str)
        
        console.print(f"[green]Generated {count} sample applications in: {output_dir}[/green]")
        
    except ImportError:
        console.print("[red]Sample data generator not available[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    application_file: str = typer.Argument(..., help="Path to application JSON file"),
):
    """Validate an application file."""
    try:
        # Load application
        application_path = Path(application_file)
        if not application_path.exists():
            console.print(f"[red]Application file not found: {application_file}[/red]")
            raise typer.Exit(1)
        
        with open(application_path, 'r') as f:
            app_data = json.load(f)
        
        application = Application(**app_data)
        
        # Validate application
        is_valid, errors = validate_application_data(application)
        
        if is_valid:
            console.print("[green][OK] Application is valid[/green]")
        else:
            console.print("[red][ERROR] Application validation failed:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def display_decision(decision, verbose: bool = False):
    """Display a single decision result."""
    # Decision summary
    decision_color = {
        DecisionType.ACCEPT: "green",
        DecisionType.DENY: "red",
        DecisionType.ADJUDICATE: "yellow"
    }
    
    color = decision_color.get(decision.decision, "white")
    
    console.print(f"\n[bold {color}]Decision: {decision.decision.value}[/bold {color}]")
    console.print(f"[bold]Reason:[/bold] {decision.reason}")
    console.print(f"[bold]Risk Score:[/bold] {decision.risk_score.overall_score}/1000 ({decision.risk_score.risk_level})")
    
    if verbose:
        # Risk score breakdown
        console.print(f"\n[bold]Risk Score Breakdown:[/bold]")
        console.print(f"  Driver Risk: {decision.risk_score.driver_risk}/1000")
        console.print(f"  Vehicle Risk: {decision.risk_score.vehicle_risk}/1000")
        console.print(f"  History Risk: {decision.risk_score.history_risk}/1000")
        if decision.risk_score.credit_risk:
            console.print(f"  Credit Risk: {decision.risk_score.credit_risk}/1000")
        
        # Risk factors
        if decision.risk_score.factors:
            console.print(f"\n[bold]Risk Factors:[/bold]")
            for factor in decision.risk_score.factors:
                console.print(f"  • {factor}")
        
        # Triggered rules
        if decision.triggered_rules:
            console.print(f"\n[bold]Triggered Rules:[/bold]")
            for rule in decision.triggered_rules:
                console.print(f"  • {rule}")


def display_batch_results(decisions: List, show_stats: bool = True):
    """Display batch processing results."""
    if not decisions:
        console.print("[red]No decisions to display[/red]")
        return
    
    # Summary table
    table = Table(title="Batch Processing Results")
    table.add_column("Application ID", style="cyan")
    table.add_column("Decision", style="bold")
    table.add_column("Risk Score", justify="right")
    table.add_column("Reason", style="dim")
    
    for decision in decisions:
        decision_color = {
            DecisionType.ACCEPT: "green",
            DecisionType.DENY: "red",
            DecisionType.ADJUDICATE: "yellow"
        }
        
        color = decision_color.get(decision.decision, "white")
        
        table.add_row(
            str(decision.application_id)[:8],
            f"[{color}]{decision.decision.value}[/{color}]",
            f"{decision.risk_score.overall_score}/1000",
            decision.reason[:50] + "..." if len(decision.reason) > 50 else decision.reason
        )
    
    console.print(table)
    
    if show_stats:
        # Statistics
        engine = get_engine()
        stats = engine.get_decision_statistics(decisions)
        
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Total Applications: {stats['total_applications']}")
        console.print(f"  Accept: {stats['decisions']['accept']['count']} ({stats['decisions']['accept']['percentage']:.1f}%)")
        console.print(f"  Deny: {stats['decisions']['deny']['count']} ({stats['decisions']['deny']['percentage']:.1f}%)")
        console.print(f"  Adjudicate: {stats['decisions']['adjudicate']['count']} ({stats['decisions']['adjudicate']['percentage']:.1f}%)")
        console.print(f"  Average Risk Score: {stats['average_risk_score']:.1f}")


def display_comparison_results(results: dict):
    """Display rule set comparison results."""
    table = Table(title="Rule Set Comparison")
    table.add_column("Rule Set", style="cyan")
    table.add_column("Decision", style="bold")
    table.add_column("Risk Score", justify="right")
    table.add_column("Reason", style="dim")
    
    for rule_set_name, decision in results.items():
        decision_color = {
            DecisionType.ACCEPT: "green",
            DecisionType.DENY: "red",
            DecisionType.ADJUDICATE: "yellow"
        }
        
        color = decision_color.get(decision.decision, "white")
        
        table.add_row(
            rule_set_name.title(),
            f"[{color}]{decision.decision.value}[/{color}]",
            f"{decision.risk_score.overall_score}/1000",
            decision.reason[:50] + "..." if len(decision.reason) > 50 else decision.reason
        )
    
    console.print(table)


def save_decision_to_file(decision, output_file: str):
    """Save a single decision to file."""
    decision_data = {
        "application_id": str(decision.application_id),
        "decision": decision.decision.value,
        "reason": decision.reason,
        "risk_score": {
            "overall_score": decision.risk_score.overall_score,
            "risk_level": decision.risk_score.risk_level,
            "driver_risk": decision.risk_score.driver_risk,
            "vehicle_risk": decision.risk_score.vehicle_risk,
            "history_risk": decision.risk_score.history_risk,
            "credit_risk": decision.risk_score.credit_risk,
            "factors": decision.risk_score.factors
        },
        "rule_set": decision.rule_set,
        "triggered_rules": decision.triggered_rules,
        "decision_date": decision.decision_date.isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(decision_data, f, indent=2)


def save_batch_results_to_file(decisions: List, output_file: str):
    """Save batch results to file."""
    results_data = []
    
    for decision in decisions:
        decision_data = {
            "application_id": str(decision.application_id),
            "decision": decision.decision.value,
            "reason": decision.reason,
            "risk_score": {
                "overall_score": decision.risk_score.overall_score,
                "risk_level": decision.risk_score.risk_level,
                "driver_risk": decision.risk_score.driver_risk,
                "vehicle_risk": decision.risk_score.vehicle_risk,
                "history_risk": decision.risk_score.history_risk,
                "credit_risk": decision.risk_score.credit_risk,
                "factors": decision.risk_score.factors
            },
            "rule_set": decision.rule_set,
            "triggered_rules": decision.triggered_rules,
            "decision_date": decision.decision_date.isoformat()
        }
        results_data.append(decision_data)
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)


def save_comparison_to_file(results: dict, output_file: str):
    """Save comparison results to file."""
    comparison_data = {}
    
    for rule_set_name, decision in results.items():
        comparison_data[rule_set_name] = {
            "decision": decision.decision.value,
            "reason": decision.reason,
            "risk_score": decision.risk_score.overall_score,
            "triggered_rules": decision.triggered_rules
        }
    
    with open(output_file, 'w') as f:
        json.dump(comparison_data, f, indent=2)


if __name__ == "__main__":
    app()