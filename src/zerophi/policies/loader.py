import os, yaml
from pathlib import Path

def _read_yaml(p: Path):
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_policy(country: str, company: str | None):
    base_dir = Path(__file__).parent
    base = _read_yaml(base_dir / f"{country.lower()}.yml")
    company_dir = Path(os.environ.get("ZEROPHI_COMPANY_CONFIG_DIR", Path.cwd() / "configs" / "company"))
    overlay = {}
    if company:
        overlay = _read_yaml(company_dir / f"{company.lower()}.yml")
    merged = {**base}
    for k in ("regex_patterns", "actions"):
        merged[k] = {**base.get(k, {}), **overlay.get(k, {})}
    return merged
