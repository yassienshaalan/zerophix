import click, os, json, sys
from pathlib import Path
from .config import RedactionConfig
from .pipelines.redaction import RedactionPipeline
from .reporting import ReportGenerator
from rich import print
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
@click.version_option(version="0.2.0", prog_name="zerophix")
def app():
    """ZeroPhix - Enterprise PII/PSI/PHI Redaction"""
    pass

@app.command()
@click.argument("text", required=False)
@click.option("--text", "text_opt", type=str, help="Text to redact (alternative to positional arg)")
@click.option("--infile", type=click.Path(exists=True), help="Path to input text file")
@click.option("--country", default="AU", show_default=True)
@click.option("--company", default=None)
@click.option("--use-openmed", is_flag=True, default=False)
@click.option("--masking-style", default="hash", type=click.Choice(["hash","mask","replace","brackets"]))
@click.option("--report", type=click.Choice(["json","markdown","html","csv","text"]), default=None, help="Generate a report in the specified format")
@click.option("--report-output", type=str, default=None, help="Save report to file (default: print to stdout)")
def redact(text, text_opt, infile, country, company, use_openmed, masking_style, report, report_output):
    """Redact a text string or file"""
    data = text or text_opt or (open(infile, "r", encoding="utf-8").read() if infile else None)
    if not data:
        print("[red]Provide --text or --infile[/red]")
        sys.exit(2)
    cfg = RedactionConfig(country=country, company=company, use_openmed=use_openmed, masking_style=masking_style)
    pipe = RedactionPipeline.from_config(cfg)
    result = pipe.redact(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Generate report if requested
    if report:
        scan_result = pipe.scan(data)
        report_content = ReportGenerator.generate(scan_result, format=report)
        
        if report_output:
            with open(report_output, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"\n[green]Report saved to: {report_output}[/green]")
        else:
            print("\n" + "="*60)
            print("DETECTION REPORT")
            print("="*60)
            print(report_content)

@app.command()
@click.argument("text", required=False)
@click.option("--text", "text_opt", type=str, help="Text to scan (alternative to positional arg)")
@click.option("--infile", type=click.Path(exists=True), help="Path to input text file")
@click.option("--country", default="AU", show_default=True)
@click.option("--company", default=None)
@click.option("--use-openmed", is_flag=True, default=False)
@click.option("--format", "output_format", default="text", type=click.Choice(["json","markdown","html","csv","text"]), show_default=True, help="Report output format")
@click.option("--output", "output_file", default=None, help="Save report to file (default: print to stdout)")
@click.option("--stats-only", is_flag=True, default=False, help="Show only statistics summary")
@click.option("--verbose", is_flag=True, default=False, help="Show detailed detection information")
def scan(text, text_opt, infile, country, company, use_openmed, output_format, output_file, stats_only, verbose):
    data = text or text_opt or (open(infile, "r", encoding="utf-8").read() if infile else None)
    data = text or (open(infile, "r", encoding="utf-8").read() if infile else None)
    if not data:
        print("[red]Provide --text or --infile[/red]")
        sys.exit(2)
    
    cfg = RedactionConfig(country=country, company=company, use_openmed=use_openmed)
    pipe = RedactionPipeline.from_config(cfg)
    scan_result = pipe.scan(data)
    
    # Stats-only mode
    if stats_only:
        table = Table(title="PII/PHI Scan Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Detections", str(scan_result['total_detections']))
        table.add_row("Has PII/PHI", "Yes" if scan_result['has_pii'] else "No")
        table.add_row("Entity Types", str(len(scan_result['entity_counts'])))
        
        console.print(table)
        
        if scan_result['entity_counts']:
            entity_table = Table(title="Detections by Entity Type")
            entity_table.add_column("Entity Type", style="cyan")
            entity_table.add_column("Count", style="magenta")
            
            for entity, count in sorted(scan_result['entity_counts'].items(), key=lambda x: -x[1]):
                entity_table.add_row(entity, str(count))
            
            console.print(entity_table)
        return
    
    # Generate full report
    report_content = ReportGenerator.generate(scan_result, format=output_format)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[green]Scan report saved to: {output_file}[/green]")
        print(f"[cyan]Total detections: {scan_result['total_detections']}[/cyan]")
    else:
        if verbose:
            console.print(f"[yellow]Scanning text ({len(data)} characters)...[/yellow]")
        print(report_content)

@app.command("download-model")
@click.option("--name", default="openmed-base", show_default=True)
@click.option("--models-dir", default=None)
def download_model(name, models_dir):
    """Download an optional model into the local cache"""
    from .models.manager import ensure_model
    path = ensure_model(name, models_dir)
    print(path)

@app.command("show-policy")
@click.option("--country", default="AU", show_default=True)
@click.option("--company", default=None)
def show_policy(country, company):
    """Show the active policy (country + company overlay)"""
    from .policies.loader import load_policy
    import yaml
    pol = load_policy(country, company)
    print(yaml.safe_dump(pol, sort_keys=True))
