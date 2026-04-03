import json
import os
from pathlib import Path

import requests
import yaml

# Load ~/.hermes/.env without printing secrets
for env_path in [Path('/home/holo/.hermes/.env'), Path.home() / '.hermes' / '.env']:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)

cfg = yaml.safe_load(Path('/home/holo/.hermes/config.yaml').read_text())
base_url = cfg.get('model', {}).get('base_url', '').rstrip('/')
model = cfg.get('model', {}).get('default')
api_mode = cfg.get('model', {}).get('api_mode')
provider = cfg.get('model', {}).get('provider')
api_key = (
    os.environ.get('OPENAI_API_KEY')
    or os.environ.get('CODEX_API_KEY')
    or os.environ.get('OPENROUTER_API_KEY')
    or os.environ.get('AI_GATEWAY_API_KEY')
    or ''
)

headers = {'Content-Type': 'application/json'}
if api_key:
    headers['Authorization'] = f'Bearer {api_key}'

results = {
    'base_url': base_url,
    'model': model,
    'provider': provider,
    'api_mode': api_mode,
    'api_key_present': bool(api_key),
    'metadata_checks': []
}

for path in ['/models', '/v1/models']:
    url = base_url + path
    try:
        r = requests.get(url, headers=headers, timeout=20)
        entry = {
            'path': path,
            'status_code': r.status_code,
            'content_type': r.headers.get('content-type', ''),
        }
        try:
            data = r.json()
            entry['json_keys'] = list(data.keys())[:20] if isinstance(data, dict) else None
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                # only keep matching model snippets / count
                entry['data_count'] = len(data['data'])
                matches = [m for m in data['data'] if isinstance(m, dict) and model in json.dumps(m, ensure_ascii=False)]
                entry['matching_models'] = matches[:3]
            else:
                entry['sample'] = data if isinstance(data, dict) else {'type': type(data).__name__}
        except Exception:
            entry['text_prefix'] = r.text[:500]
        results['metadata_checks'].append(entry)
    except Exception as e:
        results['metadata_checks'].append({'path': path, 'error': str(e)})

print(json.dumps(results, ensure_ascii=False))
