import json
import os
from pathlib import Path

import requests
import yaml

for env_path in [Path('/home/holo/.hermes/.env'), Path.home() / '.hermes' / '.env']:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

cfg = yaml.safe_load(Path('/home/holo/.hermes/config.yaml').read_text())
base_url = cfg.get('model', {}).get('base_url', '').rstrip('/')
model = cfg.get('model', {}).get('default')
api_key = (
    os.environ.get('OPENAI_API_KEY')
    or os.environ.get('CODEX_API_KEY')
    or os.environ.get('OPENROUTER_API_KEY')
    or os.environ.get('AI_GATEWAY_API_KEY')
    or ''
)
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}

payload = {
    'model': model,
    'input': 'Say only OK.',
    'max_output_tokens': 8,
}

out = []
for path in ['/responses', '/v1/responses', '/chat/completions', '/v1/chat/completions']:
    url = base_url + path
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        entry = {'path': path, 'status_code': r.status_code, 'content_type': r.headers.get('content-type', '')}
        try:
            entry['json'] = r.json()
        except Exception:
            entry['text_prefix'] = r.text[:500]
        out.append(entry)
    except Exception as e:
        out.append({'path': path, 'error': str(e)})
print(json.dumps(out, ensure_ascii=False))
