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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from underwriting.core.engine import UnderwritingEngine
from underwriting.core.ai_engine import AIEnhancedUnderwritingEngine, EnhancedUnderwritingDecision
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

# Global engine instances
engine: Optional[UnderwritingEngine] = None
ai_engine: Optional[AIEnhancedUnderwritingEngine] = None


def get_engine() -> UnderwritingEngine:
    """Get or create the underwriting engine instance."""
    global engine
    if engine is None:
        engine = UnderwritingEngine()
    return engine


def get_ai_engine() -> AIEnhancedUnderwritingEngine:
    """Get or create the AI-enhanced underwriting engine instance."""
    global ai_engine
    if ai_engine is None:
        ai_engine = AIEnhancedUnderwritingEngine()
    return ai_engine


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


@app.command()
def ai_evaluate(
    application_file: str = typer.Argument(..., help="Path to application JSON file"),
    rule_set: str = typer.Option("standard", "--rule-set", "-r", help="Rule set to use"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    ai_only: bool = typer.Option(False, "--ai-only", help="Use AI evaluation only"),
    rules_only: bool = typer.Option(False, "--rules-only", help="Use rules evaluation only"),
):
    """Evaluate application using AI-enhanced underwriting."""
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
        
        # Get AI engine
        ai_engine = get_ai_engine()
        
        # Determine AI usage
        use_ai = not rules_only
        
        console.print("Processing application with AI enhancement...", style="yellow")
        
        # Process application
        enhanced_decision = ai_engine.process_application_enhanced_sync(
            application, rule_set, use_ai=use_ai
        )
        
        console.print("[OK] AI-enhanced evaluation completed", style="green")
        
        # Display results
        display_enhanced_decision(enhanced_decision, verbose=verbose, ai_only=ai_only)
        
        # Save to file if requested
        if output_file:
            save_enhanced_decision_to_file(enhanced_decision, output_file)
            console.print(f"[green]Results saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ai_batch(
    applications_dir: str = typer.Argument(..., help="Directory containing application JSON files"),
    rule_set: str = typer.Option("standard", "--rule-set", "-r", help="Rule set to use"),
    output_file: str = typer.Option("ai_batch_results.json", "--output", "-o", help="Output file for results"),
    use_ai: bool = typer.Option(True, "--use-ai/--no-ai", help="Enable/disable AI evaluation"),
    stats: bool = typer.Option(True, "--stats", help="Show statistics"),
):
    """Process multiple applications with AI enhancement."""
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
        
        # Get AI engine
        ai_engine = get_ai_engine()
        
        console.print(f"Processing {len(applications)} applications with AI enhancement...", style="yellow")
        
        # Process applications - need to run async function
        import asyncio
        enhanced_decisions = asyncio.run(
            ai_engine.batch_process_applications_enhanced(applications, rule_set, use_ai)
        )
        
        console.print("[OK] AI-enhanced batch processing completed", style="green")
        
        # Display results
        display_enhanced_batch_results(enhanced_decisions, show_stats=stats)
        
        # Save results
        save_enhanced_batch_results_to_file(enhanced_decisions, output_file)
        console.print(f"[green]Results saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ai_compare(
    application_file: str = typer.Argument(..., help="Path to application JSON file"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
    include_ai: bool = typer.Option(True, "--include-ai/--no-ai", help="Include AI evaluation"),
):
    """Compare rule sets with optional AI enhancement."""
    try:
        # Load application
        application_path = Path(application_file)
        if not application_path.exists():
            console.print(f"[red]Application file not found: {application_file}[/red]")
            raise typer.Exit(1)
        
        with open(application_path, 'r') as f:
            app_data = json.load(f)
        
        application = Application(**app_data)
        
        # Get engines
        engine = get_engine()
        ai_engine = get_ai_engine()
        
        console.print("Comparing rule sets with AI enhancement...", style="yellow")
        
        # Compare traditional rule sets
        rule_results = engine.compare_rule_sets(application)
        
        # Get AI-enhanced results if requested
        ai_results = {}
        if include_ai:
            import asyncio
            try:
                ai_results = asyncio.run(
                    ai_engine.compare_rule_sets_enhanced(application, include_ai=True)
                )
            except Exception as e:
                console.print(f"[yellow]AI-enhanced comparison failed: {e}[/yellow]")
                # Fallback to individual evaluations
                for rule_set in ["conservative", "standard", "liberal"]:
                    try:
                        enhanced_decision = asyncio.run(
                            ai_engine.process_application_enhanced(application, rule_set, use_ai=True)
                        )
                        ai_results[rule_set] = enhanced_decision
                    except Exception as e:
                        console.print(f"[yellow]AI evaluation failed for {rule_set}: {e}[/yellow]")
        
        console.print("[OK] Comparison completed", style="green")
        
        # Display comparison
        display_ai_comparison_results(rule_results, ai_results)
        
        # Save to file if requested
        if output_file:
            save_ai_comparison_to_file(rule_results, ai_results, output_file)
            console.print(f"[green]Results saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ai_health():
    """Check AI service health and configuration."""
    try:
        ai_engine = get_ai_engine()
        
        console.print("Checking AI service health...", style="yellow")
        
        health = ai_engine.get_ai_service_health()
        
        # Display health status
        if health.get("status") == "healthy":
            console.print("[green][OK] AI service is healthy[/green]")
        elif health.get("status") == "disabled":
            console.print("[yellow][INFO] AI service is disabled[/yellow]")
        else:
            console.print("[red][ERROR] AI service is unhealthy[/red]")
        
        # Health details table
        table = Table(title="AI Service Health Details")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in health.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    table.add_row(f"{key}.{subkey}", str(subvalue))
            else:
                table.add_row(key, str(value))
        
        console.print(table)
        
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
        json.dump(decision_data, f, indent=2, default=str)


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
        json.dump(results_data, f, indent=2, default=str)


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
        json.dump(comparison_data, f, indent=2, default=str)


def display_enhanced_decision(enhanced_decision: EnhancedUnderwritingDecision, verbose: bool = False, ai_only: bool = False):
    """Display enhanced decision with both rule and AI results."""
    if ai_only and enhanced_decision.ai_decision:
        # Display only AI decision
        console.print(f"\n[bold]AI Decision Results[/bold]")
        ai_decision = enhanced_decision.ai_decision
        
        decision_color = {
            DecisionType.ACCEPT: "green",
            DecisionType.DENY: "red", 
            DecisionType.ADJUDICATE: "yellow"
        }
        color = decision_color.get(ai_decision.decision, "white")
        
        console.print(f"[bold {color}]Decision: {ai_decision.decision.value}[/bold {color}]")
        console.print(f"[bold]Reasoning:[/bold] {ai_decision.reasoning}")
        console.print(f"[bold]Confidence:[/bold] {ai_decision.confidence_level.value}")
        console.print(f"[bold]Risk Score:[/bold] {ai_decision.risk_assessment.overall_risk_score}/1000 ({ai_decision.risk_assessment.risk_level})")
        
        if verbose and ai_decision.risk_assessment.key_risk_factors:
            console.print(f"\n[bold]Key Risk Factors:[/bold]")
            for factor in ai_decision.risk_assessment.key_risk_factors:
                console.print(f"  • {factor}")
        
        # Show LangSmith tracing information for AI-only decisions
        if ai_decision.langsmith_run_url:
            console.print(f"\n[bold]LangSmith Trace:[/bold]")
            console.print(f"  Run ID: {ai_decision.langsmith_run_id}")
            console.print(f"  Trace URL: [link={ai_decision.langsmith_run_url}]{ai_decision.langsmith_run_url}[/link]")
    else:
        # Display rule decision
        display_decision(enhanced_decision.final_decision, verbose)
        
        # Display AI comparison if available
        if enhanced_decision.ai_decision:
            console.print(f"\n[bold]AI Comparison:[/bold]")
            ai_decision = enhanced_decision.ai_decision
            console.print(f"  AI Decision: {ai_decision.decision.value}")
            console.print(f"  AI Risk Score: {ai_decision.risk_assessment.overall_risk_score}/1000")
            console.print(f"  AI Confidence: {ai_decision.confidence_level.value}")
            
            # Show combination metadata
            if enhanced_decision.combination_metadata:
                metadata = enhanced_decision.combination_metadata
                console.print(f"  Combination Strategy: {metadata.get('combination_strategy', 'N/A')}")
                if 'decision_basis' in metadata:
                    console.print(f"  Decision Basis: {metadata['decision_basis']}")
        
        # Show LangSmith tracing information
        if enhanced_decision.langsmith_run_url:
            console.print(f"\n[bold]LangSmith Trace:[/bold]")
            console.print(f"  Run ID: {enhanced_decision.langsmith_run_id}")
            console.print(f"  Trace URL: [link={enhanced_decision.langsmith_run_url}]{enhanced_decision.langsmith_run_url}[/link]")


def display_enhanced_batch_results(enhanced_decisions: List[EnhancedUnderwritingDecision], show_stats: bool = True):
    """Display enhanced batch processing results."""
    if not enhanced_decisions:
        console.print("[red]No decisions to display[/red]")
        return
    
    # Summary table
    table = Table(title="AI-Enhanced Batch Processing Results")
    table.add_column("Application ID", style="cyan")
    table.add_column("Final Decision", style="bold")
    table.add_column("Rule Decision", style="dim")
    table.add_column("AI Decision", style="dim")
    table.add_column("Risk Score", justify="right")
    table.add_column("AI Available", justify="center")
    table.add_column("LangSmith", justify="center")
    
    for ed in enhanced_decisions:
        final_decision = ed.final_decision
        rule_decision = ed.rule_decision
        ai_decision = ed.ai_decision
        
        decision_color = {
            DecisionType.ACCEPT: "green",
            DecisionType.DENY: "red",
            DecisionType.ADJUDICATE: "yellow"
        }
        
        final_color = decision_color.get(final_decision.decision, "white")
        ai_available = "[OK]" if ai_decision else "[X]"
        ai_decision_str = ai_decision.decision.value if ai_decision else "N/A"
        langsmith_available = "[OK]" if ed.langsmith_run_id else "[X]"
        
        table.add_row(
            str(final_decision.application_id)[:8],
            f"[{final_color}]{final_decision.decision.value}[/{final_color}]",
            rule_decision.decision.value,
            ai_decision_str,
            f"{final_decision.risk_score.overall_score}/1000",
            ai_available,
            langsmith_available
        )
    
    console.print(table)
    
    if show_stats:
        # Enhanced statistics
        ai_engine = get_ai_engine()
        stats = ai_engine.get_enhanced_statistics(enhanced_decisions)
        
        console.print(f"\n[bold]Enhanced Statistics:[/bold]")
        console.print(f"  Total Applications: {stats['total_applications']}")
        console.print(f"  Accept: {stats['decisions']['accept']['count']} ({stats['decisions']['accept']['percentage']:.1f}%)")
        console.print(f"  Deny: {stats['decisions']['deny']['count']} ({stats['decisions']['deny']['percentage']:.1f}%)")
        console.print(f"  Adjudicate: {stats['decisions']['adjudicate']['count']} ({stats['decisions']['adjudicate']['percentage']:.1f}%)")
        console.print(f"  Average Risk Score: {stats['average_risk_score']:.1f}")
        console.print(f"  AI Coverage: {stats['ai_coverage_percentage']:.1f}%")
        console.print(f"  Rule-AI Agreement: {stats['rule_ai_agreement_percentage']:.1f}%")
        
        # Show LangSmith batch tracing info if available
        langsmith_urls = [ed.langsmith_run_url for ed in enhanced_decisions if ed.langsmith_run_url]
        if langsmith_urls:
            console.print(f"\n[bold]LangSmith Batch Traces Available:[/bold] {len(langsmith_urls)}")
            # Show first few URLs
            for i, url in enumerate(langsmith_urls[:3]):
                console.print(f"  Trace {i+1}: [link={url}]{url}[/link]")
            if len(langsmith_urls) > 3:
                console.print(f"  ... and {len(langsmith_urls) - 3} more traces")


def display_ai_comparison_results(rule_results: dict, ai_results: dict):
    """Display AI comparison results."""
    table = Table(title="Rule Set Comparison with AI Enhancement")
    table.add_column("Rule Set", style="cyan")
    table.add_column("Rule Decision", style="bold")
    table.add_column("AI Decision", style="bold")
    table.add_column("Final Decision", style="bold")
    table.add_column("Rule Score", justify="right")
    table.add_column("AI Score", justify="right")
    
    decision_color = {
        DecisionType.ACCEPT: "green",
        DecisionType.DENY: "red", 
        DecisionType.ADJUDICATE: "yellow"
    }
    
    for rule_set in ["conservative", "standard", "liberal"]:
        rule_decision = rule_results.get(rule_set)
        enhanced_decision = ai_results.get(rule_set)
        
        if rule_decision:
            rule_color = decision_color.get(rule_decision.decision, "white")
            rule_decision_str = f"[{rule_color}]{rule_decision.decision.value}[/{rule_color}]"
            rule_score = rule_decision.risk_score.overall_score
        else:
            rule_decision_str = "N/A"
            rule_score = "N/A"
        
        if enhanced_decision and enhanced_decision.ai_decision:
            ai_decision = enhanced_decision.ai_decision
            ai_color = decision_color.get(ai_decision.decision, "white")
            ai_decision_str = f"[{ai_color}]{ai_decision.decision.value}[/{ai_color}]"
            ai_score = ai_decision.risk_assessment.overall_risk_score
            
            final_decision = enhanced_decision.final_decision
            final_color = decision_color.get(final_decision.decision, "white")
            final_decision_str = f"[{final_color}]{final_decision.decision.value}[/{final_color}]"
        else:
            ai_decision_str = "N/A"
            ai_score = "N/A"
            final_decision_str = rule_decision_str
        
        table.add_row(
            rule_set.title(),
            rule_decision_str,
            ai_decision_str,
            final_decision_str,
            str(rule_score),
            str(ai_score)
        )
    
    console.print(table)
    
    # Show LangSmith A/B testing trace if available
    ab_test_urls = []
    for enhanced_decision in ai_results.values():
        if hasattr(enhanced_decision, 'langsmith_comparison_run_url') and enhanced_decision.langsmith_comparison_run_url:
            ab_test_urls.append(enhanced_decision.langsmith_comparison_run_url)
        elif hasattr(enhanced_decision, 'langsmith_run_url') and enhanced_decision.langsmith_run_url:
            ab_test_urls.append(enhanced_decision.langsmith_run_url)
    
    if ab_test_urls:
        # Remove duplicates and show unique A/B test traces
        unique_urls = list(set(ab_test_urls))
        console.print(f"\n[bold]LangSmith A/B Testing Traces:[/bold]")
        for i, url in enumerate(unique_urls):
            console.print(f"  A/B Test Trace {i+1}: [link={url}]{url}[/link]")


def save_enhanced_decision_to_file(enhanced_decision: EnhancedUnderwritingDecision, output_file: str):
    """Save enhanced decision to file."""
    decision_data = {
        "application_id": enhanced_decision.final_decision.application_id,
        "final_decision": {
            "decision": enhanced_decision.final_decision.decision.value,
            "reason": enhanced_decision.final_decision.reason,
            "risk_score": enhanced_decision.final_decision.risk_score.overall_score,
            "rule_set": enhanced_decision.final_decision.rule_set
        },
        "rule_decision": {
            "decision": enhanced_decision.rule_decision.decision.value,
            "reason": enhanced_decision.rule_decision.reason,
            "risk_score": enhanced_decision.rule_decision.risk_score.overall_score
        },
        "ai_decision": None,
        "combination_metadata": enhanced_decision.combination_metadata,
        "langsmith_tracing": {
            "run_id": enhanced_decision.langsmith_run_id,
            "run_url": enhanced_decision.langsmith_run_url
        }
    }
    
    if enhanced_decision.ai_decision:
        decision_data["ai_decision"] = {
            "decision": enhanced_decision.ai_decision.decision.value,
            "reasoning": enhanced_decision.ai_decision.reasoning,
            "confidence_level": enhanced_decision.ai_decision.confidence_level.value,
            "risk_score": enhanced_decision.ai_decision.risk_assessment.overall_risk_score,
            "key_risk_factors": enhanced_decision.ai_decision.risk_assessment.key_risk_factors
        }
    
    with open(output_file, 'w') as f:
        json.dump(decision_data, f, indent=2, default=str)


def save_enhanced_batch_results_to_file(enhanced_decisions: List[EnhancedUnderwritingDecision], output_file: str):
    """Save enhanced batch results to file."""
    results_data = []
    
    for ed in enhanced_decisions:
        decision_data = {
            "application_id": ed.final_decision.application_id,
            "final_decision": {
                "decision": ed.final_decision.decision.value,
                "reason": ed.final_decision.reason,
                "risk_score": ed.final_decision.risk_score.overall_score
            },
            "rule_decision": {
                "decision": ed.rule_decision.decision.value,
                "risk_score": ed.rule_decision.risk_score.overall_score
            },
            "ai_decision": None,
            "combination_metadata": ed.combination_metadata,
            "langsmith_tracing": {
                "run_id": ed.langsmith_run_id,
                "run_url": ed.langsmith_run_url
            }
        }
        
        if ed.ai_decision:
            decision_data["ai_decision"] = {
                "decision": ed.ai_decision.decision.value,
                "confidence_level": ed.ai_decision.confidence_level.value,
                "risk_score": ed.ai_decision.risk_assessment.overall_risk_score
            }
        
        results_data.append(decision_data)
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2, default=str)


def save_ai_comparison_to_file(rule_results: dict, ai_results: dict, output_file: str):
    """Save AI comparison results to file."""
    comparison_data = {}
    
    for rule_set in ["conservative", "standard", "liberal"]:
        rule_decision = rule_results.get(rule_set)
        enhanced_decision = ai_results.get(rule_set)
        
        comparison_data[rule_set] = {
            "rule_decision": rule_decision.decision.value if rule_decision else None,
            "rule_risk_score": rule_decision.risk_score.overall_score if rule_decision else None,
            "ai_decision": None,
            "ai_risk_score": None,
            "final_decision": None,
            "langsmith_tracing": {
                "run_id": enhanced_decision.langsmith_run_id if enhanced_decision else None,
                "run_url": enhanced_decision.langsmith_run_url if enhanced_decision else None
            }
        }
        
        if enhanced_decision:
            if enhanced_decision.ai_decision:
                comparison_data[rule_set]["ai_decision"] = enhanced_decision.ai_decision.decision.value
                comparison_data[rule_set]["ai_risk_score"] = enhanced_decision.ai_decision.risk_assessment.overall_risk_score
            comparison_data[rule_set]["final_decision"] = enhanced_decision.final_decision.decision.value
    
    with open(output_file, 'w') as f:
        json.dump(comparison_data, f, indent=2, default=str)


# Rate limiting management commands

@app.command(name="rate-status")
def rate_status(
    identifier: Optional[str] = typer.Option(None, "--identifier", "-i", help="Specific identifier to check"),
    operation_type: Optional[str] = typer.Option(None, "--operation", "-o", help="Operation type to check"),
    all_status: bool = typer.Option(False, "--all", "-a", help="Show all rate limit status"),
):
    """Check rate limiting status for identifiers and operation types."""
    try:
        ai_engine = get_ai_engine()
        
        if all_status:
            console.print("Getting all rate limit status...", style="yellow")
            status = ai_engine.get_all_rate_limit_status()
            
            if "error" in status:
                console.print(f"[red]Error: {status['error']}[/red]")
                return
            
            # Display all status in a table
            table = Table(title="Rate Limit Status - All Identifiers")
            table.add_column("Identifier", style="cyan")
            table.add_column("Operation", style="green")
            table.add_column("Daily Usage", style="yellow")
            table.add_column("Weekly Usage", style="yellow")
            table.add_column("Monthly Usage", style="yellow")
            table.add_column("Burst Usage", style="red")
            table.add_column("Blocked", style="red")
            table.add_column("Override", style="magenta")
            
            for key, data in status.items():
                if isinstance(data, dict) and "identifier" in data:
                    daily = f"{data['daily']['usage']}/{data['daily']['limit']}"
                    weekly = f"{data['weekly']['usage']}/{data['weekly']['limit']}"
                    monthly = f"{data['monthly']['usage']}/{data['monthly']['limit']}"
                    burst = f"{data['burst']['usage']}/{data['burst']['limit']}"
                    blocked = str(data.get('total_blocked', 0))
                    override = "[green]Yes[/green]" if data.get('override_active', False) else "[red]No[/red]"
                    
                    table.add_row(
                        data['identifier'],
                        data['operation_type'],
                        daily,
                        weekly,
                        monthly,
                        burst,
                        blocked,
                        override
                    )
            
            console.print(table)
            
        elif identifier and operation_type:
            console.print(f"Getting rate limit status for {identifier}:{operation_type}...", style="yellow")
            status = ai_engine.get_rate_limit_status(identifier, operation_type)
            
            if "error" in status:
                console.print(f"[red]Error: {status['error']}[/red]")
                return
            
            # Display detailed status
            console.print(f"\n[bold]Rate Limit Status: {identifier}:{operation_type}[/bold]")
            console.print(f"[bold]Enabled:[/bold] {status['enabled']}")
            
            if status['enabled']:
                console.print(f"\n[bold]Daily Usage:[/bold] {status['daily']['usage']}/{status['daily']['limit']} ({status['daily']['remaining']} remaining)")
                console.print(f"[bold]Weekly Usage:[/bold] {status['weekly']['usage']}/{status['weekly']['limit']} ({status['weekly']['remaining']} remaining)")
                console.print(f"[bold]Monthly Usage:[/bold] {status['monthly']['usage']}/{status['monthly']['limit']} ({status['monthly']['remaining']} remaining)")
                console.print(f"[bold]Burst Usage:[/bold] {status['burst']['usage']}/{status['burst']['limit']} ({status['burst']['remaining']} remaining)")
                console.print(f"[bold]Total Blocked:[/bold] {status['total_blocked']}")
                console.print(f"[bold]Override Active:[/bold] {status['override_active']}")
                
                if status['override_active'] and status['override_expiry']:
                    from datetime import datetime
                    expiry_time = datetime.fromtimestamp(status['override_expiry'])
                    console.print(f"[bold]Override Expires:[/bold] {expiry_time}")
        else:
            console.print("[yellow]Please specify both --identifier and --operation, or use --all[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="rate-analytics")
def rate_analytics(
    operation_type: Optional[str] = typer.Option(None, "--operation", "-o", help="Filter by operation type"),
    hours: int = typer.Option(24, "--hours", "-h", help="Hours of history to analyze"),
    output_file: Optional[str] = typer.Option(None, "--output", "-f", help="Output file for results"),
):
    """Generate usage analytics report."""
    try:
        ai_engine = get_ai_engine()
        
        console.print(f"Generating usage analytics for last {hours} hours...", style="yellow")
        analytics = ai_engine.generate_usage_analytics(operation_type, hours)
        
        if "error" in analytics:
            console.print(f"[red]Error: {analytics['error']}[/red]")
            return
        
        # Display analytics summary
        summary = analytics.get("summary", {})
        console.print(f"\n[bold]Usage Analytics Summary ({hours} hours)[/bold]")
        console.print(f"[bold]Total Requests:[/bold] {summary.get('total_requests', 0)}")
        console.print(f"[bold]Total Blocked:[/bold] {summary.get('total_blocked', 0)}")
        console.print(f"[bold]Success Rate:[/bold] {summary.get('success_rate_percent', 0):.1f}%")
        console.print(f"[bold]Block Rate:[/bold] {summary.get('block_rate_percent', 0):.1f}%")
        console.print(f"[bold]Request Rate:[/bold] {summary.get('request_rate_per_hour', 0):.1f} requests/hour")
        
        # Display breakdown
        breakdown = analytics.get("breakdown", {})
        console.print(f"\n[bold]Breakdown:[/bold]")
        console.print(f"[bold]Unique Identifiers:[/bold] {breakdown.get('unique_identifiers', 0)}")
        
        # Operation types
        operation_types = breakdown.get("operation_types", {})
        if operation_types:
            console.print(f"\n[bold]By Operation Type:[/bold]")
            for op_type, count in operation_types.items():
                console.print(f"  {op_type}: {count} requests")
        
        # Top users
        top_users = breakdown.get("top_users", {})
        if top_users:
            console.print(f"\n[bold]Top Users:[/bold]")
            for user, count in list(top_users.items())[:5]:
                console.print(f"  {user}: {count} requests")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(analytics, f, indent=2, default=str)
            console.print(f"[green]Analytics saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="rate-report")
def rate_report(
    report_type: str = typer.Option("daily", "--type", "-t", help="Report type (daily, weekly, monthly)"),
    operation_type: Optional[str] = typer.Option(None, "--operation", "-o", help="Filter by operation type"),
    output_file: Optional[str] = typer.Option(None, "--output", "-f", help="Output file for results"),
):
    """Generate comprehensive usage report."""
    try:
        ai_engine = get_ai_engine()
        
        console.print(f"Generating {report_type} usage report...", style="yellow")
        report = ai_engine.generate_usage_report(report_type, operation_type)
        
        if "error" in report:
            console.print(f"[red]Error: {report['error']}[/red]")
            return
        
        # Display report summary
        console.print(f"\n[bold]{report_type.title()} Usage Report[/bold]")
        console.print(f"[bold]Generated:[/bold] {report['generated_at_human']}")
        
        if report.get("operation_type_filter"):
            console.print(f"[bold]Filter:[/bold] {report['operation_type_filter']}")
        
        # Statistics
        stats = report.get("statistics", {}).get("summary", {})
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Total Requests: {stats.get('total_requests', 0)}")
        console.print(f"  Total Blocked: {stats.get('total_blocked', 0)}")
        console.print(f"  Success Rate: {stats.get('success_rate_percent', 0):.1f}%")
        console.print(f"  Block Rate: {stats.get('block_rate_percent', 0):.1f}%")
        
        # Alerts
        alerts = report.get("alerts", {})
        console.print(f"\n[bold]Alerts:[/bold]")
        console.print(f"  Total: {alerts.get('total', 0)}")
        
        severity_counts = alerts.get("by_severity", {})
        for severity, count in severity_counts.items():
            color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "green"}.get(severity, "white")
            console.print(f"  {severity.title()}: [{color}]{count}[/{color}]")
        
        # Insights
        insights = report.get("insights", [])
        if insights:
            console.print(f"\n[bold]Insights:[/bold]")
            for insight in insights:
                console.print(f"  • {insight}")
        
        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            console.print(f"\n[bold]Recommendations:[/bold]")
            for rec in recommendations:
                console.print(f"  • {rec}")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"[green]Report saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="rate-override")
def rate_override(
    identifier: str = typer.Argument(..., help="Identifier to override"),
    operation_type: str = typer.Argument(..., help="Operation type to override"),
    justification: str = typer.Option(..., "--justification", "-j", help="Justification for override"),
    duration: int = typer.Option(24, "--duration", "-d", help="Duration in hours"),
    admin_user: str = typer.Option("admin", "--admin", "-a", help="Admin user"),
    revoke: bool = typer.Option(False, "--revoke", "-r", help="Revoke existing override"),
):
    """Request or revoke admin override for rate limiting."""
    try:
        ai_engine = get_ai_engine()
        
        if revoke:
            console.print(f"Revoking override for {identifier}:{operation_type}...", style="yellow")
            success = ai_engine.revoke_admin_override(identifier, operation_type, admin_user)
            
            if success:
                console.print(f"[green]Override revoked successfully[/green]")
            else:
                console.print(f"[red]Failed to revoke override[/red]")
        else:
            console.print(f"Requesting override for {identifier}:{operation_type}...", style="yellow")
            success = ai_engine.request_admin_override(
                identifier, operation_type, justification, duration, admin_user
            )
            
            if success:
                console.print(f"[green]Override granted successfully[/green]")
                console.print(f"[bold]Duration:[/bold] {duration} hours")
                console.print(f"[bold]Justification:[/bold] {justification}")
            else:
                console.print(f"[red]Failed to grant override[/red]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="rate-override-status")
def rate_override_status(
    identifier: Optional[str] = typer.Option(None, "--identifier", "-i", help="Specific identifier"),
    operation_type: Optional[str] = typer.Option(None, "--operation", "-o", help="Operation type"),
):
    """Check admin override status."""
    try:
        ai_engine = get_ai_engine()
        
        console.print("Getting override status...", style="yellow")
        status = ai_engine.get_admin_override_status(identifier, operation_type)
        
        if "error" in status:
            console.print(f"[red]Error: {status['error']}[/red]")
            return
        
        console.print(f"\n[bold]Admin Override Status[/bold]")
        console.print(f"[bold]Override Enabled:[/bold] {status['override_enabled']}")
        console.print(f"[bold]Emergency Override Enabled:[/bold] {status['emergency_override_enabled']}")
        console.print(f"[bold]Total Active Overrides:[/bold] {status['total_active']}")
        
        active_overrides = status.get("active_overrides", {})
        if active_overrides:
            console.print(f"\n[bold]Active Overrides:[/bold]")
            for key, override_info in active_overrides.items():
                console.print(f"  {key}:")
                console.print(f"    Active: {override_info['active']}")
                if override_info['expiry_human']:
                    console.print(f"    Expires: {override_info['expiry_human']}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="rate-cleanup")
def rate_cleanup():
    """Clean up old rate limiting data."""
    try:
        ai_engine = get_ai_engine()
        
        console.print("Cleaning up old rate limiting data...", style="yellow")
        cleanup_stats = ai_engine.cleanup_rate_limiting_data()
        
        if "error" in cleanup_stats:
            console.print(f"[red]Error: {cleanup_stats['error']}[/red]")
            return
        
        console.print(f"[green]Cleanup completed successfully[/green]")
        
        for category, count in cleanup_stats.items():
            console.print(f"[bold]{category.replace('_', ' ').title()}:[/bold] {count} records cleaned")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="rate-config-reload")
def rate_config_reload():
    """Reload rate limiting configuration."""
    try:
        ai_engine = get_ai_engine()
        
        console.print("Reloading rate limiting configuration...", style="yellow")
        success = ai_engine.reload_rate_limiting_config()
        
        if success:
            console.print(f"[green]Configuration reloaded successfully[/green]")
        else:
            console.print(f"[red]Failed to reload configuration[/red]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ai-token-usage")
def ai_token_usage(
    hours: int = typer.Option(24, "--hours", "-h", help="Hours to look back for token usage"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed usage breakdown"),
    output_file: Optional[str] = typer.Option(None, "--output", "-f", help="Output file for results"),
):
    """Show detailed OpenAI token usage and cost information."""
    try:
        ai_engine = get_ai_engine()
        
        if not ai_engine.ai_enabled or not ai_engine.ai_service:
            console.print("[red]AI service is not enabled or not configured.[/red]")
            raise typer.Exit(1)
        
        # Get token usage summary
        usage_summary = ai_engine.ai_service.get_token_usage_summary(hours)
        
        console.print(f"[bold]OpenAI Token Usage Summary (Last {hours} hours)[/bold]")
        console.print(f"[bold]Model:[/bold] {usage_summary['model']}")
        console.print(f"[bold]Total Requests:[/bold] {usage_summary['total_requests']}")
        console.print(f"[bold]Total Tokens:[/bold] {usage_summary['total_tokens']:,}")
        console.print(f"[bold]Total Cost:[/bold] ${usage_summary['total_cost_usd']:.6f} USD")
        
        if usage_summary['total_requests'] > 0:
            console.print(f"[bold]Average Tokens/Request:[/bold] {usage_summary['average_tokens_per_request']}")
            console.print(f"[bold]Prompt Tokens:[/bold] {usage_summary['prompt_tokens']:,}")
            console.print(f"[bold]Completion Tokens:[/bold] {usage_summary['completion_tokens']:,}")
        
        if detailed and usage_summary['recent_usage']:
            console.print(f"\n[bold]Recent Usage Details:[/bold]")
            
            # Create a table for detailed usage
            table = Table(title="Recent OpenAI API Calls")
            table.add_column("Time", style="cyan")
            table.add_column("Total Tokens", justify="right", style="yellow")
            table.add_column("Input", justify="right", style="green")
            table.add_column("Output", justify="right", style="blue")
            table.add_column("Cost (USD)", justify="right", style="red")
            
            for record in usage_summary['recent_usage']:
                # Format timestamp
                from datetime import datetime
                timestamp = datetime.fromisoformat(record['timestamp'])
                time_str = timestamp.strftime("%H:%M:%S")
                
                table.add_row(
                    time_str,
                    f"{record['total_tokens']:,}",
                    f"{record['prompt_tokens']:,}",
                    f"{record['completion_tokens']:,}",
                    f"${record['total_cost_usd']:.6f}"
                )
            
            console.print(table)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(usage_summary, f, indent=2, default=str)
            console.print(f"[green]Token usage data saved to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error getting token usage: {e}[/red]")
        raise typer.Exit(1)


# A/B Testing Commands

@app.command(name="ab-list-configs")
def ab_list_configs(
    test_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by test type"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Filter by tags (comma-separated)"),
    predefined_only: bool = typer.Option(False, "--predefined", help="Show only predefined configs"),
):
    """List available A/B test configurations."""
    try:
        from underwriting.ab_testing.config import ABTestConfigManager, ABTestType
        
        config_manager = ABTestConfigManager()
        
        # Parse filters
        test_type_filter = None
        if test_type:
            try:
                test_type_filter = ABTestType(test_type)
            except ValueError:
                console.print(f"[red]Invalid test type: {test_type}[/red]")
                raise typer.Exit(1)
        
        tags_filter = None
        if tags:
            tags_filter = [tag.strip() for tag in tags.split(',')]
        
        # Get configurations
        configs = config_manager.list_configs(test_type_filter, tags_filter)
        
        if predefined_only:
            configs = [c for c in configs if c.test_id in config_manager.predefined_configs]
        
        if not configs:
            console.print("[yellow]No configurations found matching the criteria.[/yellow]")
            return
        
        # Display configurations
        table = Table(title="A/B Test Configurations")
        table.add_column("Test ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Type", style="green")
        table.add_column("Sample Size", justify="right", style="yellow")
        table.add_column("Metrics", style="blue")
        table.add_column("Tags", style="magenta")
        
        for config in configs:
            table.add_row(
                config.test_id,
                config.name,
                config.test_type.value,
                str(config.sample_size),
                ", ".join(config.success_metrics[:2]) + ("..." if len(config.success_metrics) > 2 else ""),
                ", ".join(config.tags[:2]) + ("..." if len(config.tags) > 2 else "")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing configurations: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-show-config")
def ab_show_config(
    test_id: str = typer.Argument(..., help="Test ID to show"),
    output_file: Optional[str] = typer.Option(None, "--output", "-f", help="Export to file"),
):
    """Show detailed A/B test configuration."""
    try:
        from underwriting.ab_testing.config import ABTestConfigManager
        
        config_manager = ABTestConfigManager()
        config = config_manager.get_config(test_id)
        
        if not config:
            console.print(f"[red]Configuration '{test_id}' not found.[/red]")
            raise typer.Exit(1)
        
        # Display configuration
        console.print(f"[bold]A/B Test Configuration: {config.name}[/bold]")
        console.print(f"[bold]Test ID:[/bold] {config.test_id}")
        console.print(f"[bold]Description:[/bold] {config.description}")
        console.print(f"[bold]Test Type:[/bold] {config.test_type.value}")
        console.print(f"[bold]Sample Size:[/bold] {config.sample_size}")
        console.print(f"[bold]Confidence Level:[/bold] {config.confidence_level}")
        console.print(f"[bold]Minimum Effect Size:[/bold] {config.minimum_effect_size}")
        console.print(f"[bold]Success Metrics:[/bold] {', '.join(config.success_metrics)}")
        console.print(f"[bold]Tags:[/bold] {', '.join(config.tags)}")
        
        # Control configuration
        console.print(f"\n[bold]Control Configuration:[/bold]")
        for key, value in config.control_config.items():
            console.print(f"  {key}: {value}")
        
        # Treatment configuration
        console.print(f"\n[bold]Treatment Configuration:[/bold]")
        for key, value in config.treatment_config.items():
            console.print(f"  {key}: {value}")
        
        # Export if requested
        if output_file:
            config_manager.export_config(test_id, output_file)
            console.print(f"[green]Configuration exported to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-create-test")
def ab_create_test(
    config_id: str = typer.Argument(..., help="Configuration ID to use"),
    sample_size: Optional[int] = typer.Option(None, "--sample-size", "-s", help="Override sample size"),
    profile: str = typer.Option("mixed", "--profile", "-p", help="Sample profile (low_risk, medium_risk, high_risk, mixed, edge_cases)"),
):
    """Create and start a new A/B test."""
    try:
        from underwriting.ab_testing.config import ABTestConfigManager
        from underwriting.ab_testing.framework import ABTestFramework
        from underwriting.ab_testing.sample_generator import ABTestSampleGenerator, ABTestSampleProfile
        
        # Get configuration
        config_manager = ABTestConfigManager()
        config = config_manager.get_config(config_id)
        
        if not config:
            console.print(f"[red]Configuration '{config_id}' not found.[/red]")
            raise typer.Exit(1)
        
        # Override sample size if provided
        if sample_size:
            config.sample_size = sample_size
        
        # Create framework and test
        framework = ABTestFramework()
        test = framework.create_test(config)
        
        console.print(f"[green]Created A/B test: {test.test_id}[/green]")
        console.print(f"[bold]Name:[/bold] {config.name}")
        console.print(f"[bold]Sample Size:[/bold] {config.sample_size}")
        console.print(f"[bold]Test Type:[/bold] {config.test_type.value}")
        
        # Generate sample data
        try:
            sample_profile = ABTestSampleProfile(profile)
        except ValueError:
            console.print(f"[red]Invalid profile: {profile}[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n[yellow]Generating sample data with profile: {profile}[/yellow]")
        sample_generator = ABTestSampleGenerator(seed=42)
        applications = sample_generator.generate_test_samples(sample_profile, config.sample_size)
        
        console.print(f"[green]Generated {len(applications)} sample applications[/green]")
        
        # Start test
        framework.start_test(test.test_id)
        console.print(f"[green]A/B test started successfully[/green]")
        
        # Store applications for later use (in a real system, this would be handled differently)
        test_data_file = f"ab_test_data/{test.test_id}_applications.json"
        import os
        os.makedirs("ab_test_data", exist_ok=True)
        
        with open(test_data_file, 'w') as f:
            import json
            json.dump([app.dict() for app in applications], f, indent=2, default=str)
        
        console.print(f"[blue]Sample applications saved to: {test_data_file}[/blue]")
        console.print(f"[yellow]Use 'ab-run-test {test.test_id}' to process applications[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error creating test: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-run-test")
def ab_run_test(
    test_id: str = typer.Argument(..., help="Test ID to run"),
    batch_size: int = typer.Option(100, "--batch-size", "-b", help="Batch size for processing"),
    max_applications: Optional[int] = typer.Option(None, "--max", "-m", help="Maximum applications to process"),
):
    """Run A/B test by processing applications."""
    try:
        from underwriting.ab_testing.framework import ABTestFramework
        from underwriting.core.models import Application
        import json
        import asyncio
        
        # Get framework and test
        framework = ABTestFramework()
        test = framework.get_test(test_id)
        
        if not test:
            console.print(f"[red]Test '{test_id}' not found.[/red]")
            raise typer.Exit(1)
        
        # Load applications
        test_data_file = f"ab_test_data/{test_id}_applications.json"
        
        if not os.path.exists(test_data_file):
            console.print(f"[red]Test data file not found: {test_data_file}[/red]")
            raise typer.Exit(1)
        
        with open(test_data_file, 'r') as f:
            app_data = json.load(f)
        
        applications = [Application(**data) for data in app_data]
        
        if max_applications:
            applications = applications[:max_applications]
        
        console.print(f"[yellow]Processing {len(applications)} applications in batches of {batch_size}[/yellow]")
        
        # Process applications in batches
        async def process_batch(batch_apps):
            results = []
            for app in batch_apps:
                try:
                    result = await framework.evaluate_application(test_id, app)
                    results.append(result)
                except Exception as e:
                    console.print(f"[red]Error processing application {app.id}: {e}[/red]")
            return results
        
        # Run processing
        async def run_test():
            total_processed = 0
            
            for i in range(0, len(applications), batch_size):
                batch = applications[i:i + batch_size]
                console.print(f"[blue]Processing batch {i//batch_size + 1}/{(len(applications) + batch_size - 1)//batch_size}[/blue]")
                
                batch_results = await process_batch(batch)
                total_processed += len(batch_results)
                
                console.print(f"[green]Processed {len(batch_results)} applications (Total: {total_processed})[/green]")
            
            return total_processed
        
        total_processed = asyncio.run(run_test())
        
        console.print(f"[green]A/B test processing completed: {total_processed} applications processed[/green]")
        console.print(f"[yellow]Use 'ab-test-status {test_id}' to view results[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error running test: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-test-status")
def ab_test_status(
    test_id: str = typer.Argument(..., help="Test ID to check"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed statistics"),
):
    """Check A/B test status and preliminary results."""
    try:
        from underwriting.ab_testing.framework import ABTestFramework
        
        framework = ABTestFramework()
        test = framework.get_test(test_id)
        
        if not test:
            console.print(f"[red]Test '{test_id}' not found.[/red]")
            raise typer.Exit(1)
        
        # Get test summary
        summary = test.get_summary()
        
        console.print(f"[bold]A/B Test Status: {test.config.name}[/bold]")
        console.print(f"[bold]Test ID:[/bold] {summary.test_id}")
        console.print(f"[bold]Status:[/bold] {summary.status.value}")
        console.print(f"[bold]Start Time:[/bold] {summary.start_time}")
        console.print(f"[bold]End Time:[/bold] {summary.end_time or 'Running'}")
        
        # Sample sizes
        console.print(f"\n[bold]Sample Sizes:[/bold]")
        console.print(f"[bold]Control:[/bold] {len(summary.control_results)}")
        console.print(f"[bold]Treatment:[/bold] {len(summary.treatment_results)}")
        console.print(f"[bold]Total:[/bold] {len(summary.control_results) + len(summary.treatment_results)}")
        console.print(f"[bold]Target:[/bold] {test.config.sample_size}")
        
        # Progress
        total_results = len(summary.control_results) + len(summary.treatment_results)
        progress = (total_results / test.config.sample_size) * 100 if test.config.sample_size > 0 else 0
        console.print(f"[bold]Progress:[/bold] {progress:.1f}%")
        
        # Statistical results (if available)
        if summary.statistical_analysis:
            console.print(f"\n[bold]Statistical Results:[/bold]")
            
            for metric, analysis in summary.statistical_analysis.items():
                if metric == "metadata":
                    continue
                
                significant = analysis.get("significant", False)
                effect_size = analysis.get("effect_size", 0)
                p_value = analysis.get("p_value", 1.0)
                
                sig_indicator = "[green]✓[/green]" if significant else "[red]✗[/red]"
                
                console.print(f"  {metric}: {sig_indicator} (effect: {effect_size:.4f}, p: {p_value:.4f})")
        
        # Conclusions and recommendations
        if summary.conclusions:
            console.print(f"\n[bold]Conclusions:[/bold]")
            for conclusion in summary.conclusions:
                console.print(f"  • {conclusion}")
        
        if summary.recommendations:
            console.print(f"\n[bold]Recommendations:[/bold]")
            for recommendation in summary.recommendations:
                console.print(f"  • {recommendation}")
        
        # Detailed statistics
        if detailed and summary.statistical_analysis:
            console.print(f"\n[bold]Detailed Statistics:[/bold]")
            for metric, analysis in summary.statistical_analysis.items():
                if metric == "metadata":
                    continue
                
                console.print(f"\n[bold]{metric}:[/bold]")
                for key, value in analysis.items():
                    if key not in ["test_result"]:
                        console.print(f"  {key}: {value}")
        
    except Exception as e:
        console.print(f"[red]Error checking test status: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-stop-test")
def ab_stop_test(
    test_id: str = typer.Argument(..., help="Test ID to stop"),
):
    """Stop a running A/B test."""
    try:
        from underwriting.ab_testing.framework import ABTestFramework
        
        framework = ABTestFramework()
        test = framework.get_test(test_id)
        
        if not test:
            console.print(f"[red]Test '{test_id}' not found.[/red]")
            raise typer.Exit(1)
        
        # Stop test
        framework.stop_test(test_id)
        
        console.print(f"[green]A/B test stopped: {test_id}[/green]")
        console.print(f"[yellow]Use 'ab-generate-report {test_id}' to generate final report[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error stopping test: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-generate-report")
def ab_generate_report(
    test_id: str = typer.Argument(..., help="Test ID to generate report for"),
    format: str = typer.Option("json", "--format", "-f", help="Report format (json, html, markdown)"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate comprehensive A/B test report."""
    try:
        from underwriting.ab_testing.results import ABTestResultsManager, ReportFormat
        
        # Validate format
        try:
            report_format = ReportFormat(format.lower())
        except ValueError:
            console.print(f"[red]Invalid format: {format}. Use json, html, or markdown.[/red]")
            raise typer.Exit(1)
        
        # Generate report
        results_manager = ABTestResultsManager()
        report = results_manager.generate_test_report(test_id, report_format)
        
        console.print(f"[green]Generated report for test: {test.config.name}[/green]")
        console.print(f"[bold]Test ID:[/bold] {report.test_id}")
        console.print(f"[bold]Generated:[/bold] {report.generated_at}")
        console.print(f"[bold]Duration:[/bold] {report.test_duration}")
        
        # Show sample sizes
        console.print(f"\n[bold]Sample Sizes:[/bold]")
        console.print(f"[bold]Control:[/bold] {report.sample_sizes.get('control', 0)}")
        console.print(f"[bold]Treatment:[/bold] {report.sample_sizes.get('treatment', 0)}")
        console.print(f"[bold]Total:[/bold] {report.sample_sizes.get('total', 0)}")
        
        # Show significance summary
        console.print(f"\n[bold]Significance Summary:[/bold]")
        for metric, significant in report.significance_summary.items():
            effect_size = report.effect_sizes.get(metric, 0)
            sig_indicator = "[green]✓[/green]" if significant else "[red]✗[/red]"
            console.print(f"  {metric}: {sig_indicator} (effect: {effect_size:.4f})")
        
        # Show business impact
        if report.business_impact:
            console.print(f"\n[bold]Business Impact:[/bold]")
            for metric, impact in report.business_impact.items():
                if isinstance(impact, dict) and "projected_impact" in impact:
                    console.print(f"  {metric}: {impact['projected_impact']}")
        
        # Show conclusions
        if report.conclusions:
            console.print(f"\n[bold]Conclusions:[/bold]")
            for conclusion in report.conclusions:
                console.print(f"  • {conclusion}")
        
        # Show recommendations
        if report.recommendations:
            console.print(f"\n[bold]Recommendations:[/bold]")
            for recommendation in report.recommendations:
                console.print(f"  • {recommendation}")
        
        # Show next steps
        if report.next_steps:
            console.print(f"\n[bold]Next Steps:[/bold]")
            for step in report.next_steps:
                console.print(f"  • {step}")
        
        # Copy to output file if specified
        if output_file:
            import shutil
            report_file = f"ab_test_data/reports/{test_id}_report.{format}"
            shutil.copy(report_file, output_file)
            console.print(f"[green]Report copied to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-list-tests")
def ab_list_tests():
    """List all A/B tests."""
    try:
        from underwriting.ab_testing.framework import ABTestFramework
        from underwriting.ab_testing.results import ABTestResultsManager
        
        framework = ABTestFramework()
        results_manager = ABTestResultsManager()
        
        # Get active tests
        active_tests = framework.list_tests()
        
        # Get completed tests
        completed_tests = results_manager.list_completed_tests()
        
        # Display active tests
        if active_tests:
            console.print(f"[bold]Active Tests:[/bold]")
            
            table = Table(title="Active A/B Tests")
            table.add_column("Test ID", style="cyan")
            table.add_column("Name", style="bold")
            table.add_column("Status", style="green")
            table.add_column("Progress", justify="right", style="yellow")
            table.add_column("Control", justify="right", style="blue")
            table.add_column("Treatment", justify="right", style="blue")
            
            for test in active_tests:
                progress = f"{test['control_results'] + test['treatment_results']}/{test['sample_size']}"
                
                table.add_row(
                    test["test_id"],
                    test["name"],
                    test["status"],
                    progress,
                    str(test["control_results"]),
                    str(test["treatment_results"])
                )
            
            console.print(table)
        
        # Display completed tests
        if completed_tests:
            console.print(f"\n[bold]Completed Tests:[/bold]")
            
            table = Table(title="Completed A/B Tests")
            table.add_column("Test ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Start Time", style="yellow")
            table.add_column("End Time", style="yellow")
            table.add_column("Control", justify="right", style="blue")
            table.add_column("Treatment", justify="right", style="blue")
            
            for test in completed_tests:
                table.add_row(
                    test["test_id"],
                    test["status"],
                    test.get("start_time", "")[:19] if test.get("start_time") else "",
                    test.get("end_time", "")[:19] if test.get("end_time") else "",
                    str(test["control_results"]),
                    str(test["treatment_results"])
                )
            
            console.print(table)
        
        if not active_tests and not completed_tests:
            console.print("[yellow]No A/B tests found.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error listing tests: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="ab-cleanup")
def ab_cleanup(
    days: int = typer.Option(30, "--days", "-d", help="Clean up tests older than N days"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Confirm cleanup without prompt"),
):
    """Clean up old A/B test data."""
    try:
        from underwriting.ab_testing.results import ABTestResultsManager
        
        if not confirm:
            response = typer.confirm(f"This will delete A/B test data older than {days} days. Continue?")
            if not response:
                console.print("[yellow]Cleanup cancelled.[/yellow]")
                return
        
        results_manager = ABTestResultsManager()
        cleaned_count = results_manager.cleanup_old_results(days)
        
        console.print(f"[green]Cleaned up {cleaned_count} old A/B tests[/green]")
        
    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()