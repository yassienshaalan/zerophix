import click, os, json, sys
from .config import RedactionConfig
from .pipelines.redaction import RedactionPipeline
from rich import print

@click.group()
def app():
    """Redaction CLI and utilities for zerophi"""
    pass

@app.command()
@click.option("--text", type=str, help="Text to redact (use --infile for files)")
@click.option("--infile", type=click.Path(exists=True), help="Path to input text file")
@click.option("--country", default="AU", show_default=True)
@click.option("--company", default=None)
@click.option("--use-openmed", is_flag=True, default=False)
@click.option("--masking-style", default="hash", type=click.Choice(["hash","mask","replace","brackets"]))
def redact(text, infile, country, company, use_openmed, masking_style):
    """Redact a text string or file"""
    data = text or (open(infile, "r", encoding="utf-8").read() if infile else None)
    if not data:
        print("[red]Provide --text or --infile[/red]")
        sys.exit(2)
    cfg = RedactionConfig(country=country, company=company, use_openmed=use_openmed, masking_style=masking_style)
    pipe = RedactionPipeline.from_config(cfg)
    result = pipe.redact(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))

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
