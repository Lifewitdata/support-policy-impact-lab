from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parents[2]

def config(name):
    return yaml.safe_load((ROOT / 'config' / f'{name}.yaml').read_text())

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False))
