import json
import os
from pathlib import Path

import requests
import yaml

TARGET_TOKENS = 512_000
RESERVE_TOKENS = 1_000  # leave a little headroom for wrapper/instructions

# Load ~/.hermes/.env without printing secrets
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

if not api_key:
    raise SystemExit('No API key found in environment/.env')

# Prefer a real tokenizer estimate if available.
enc = None
enc_name = None
try:
    import tiktoken
    try:
        enc = tiktoken.encoding_for_model('gpt-4o')
        enc_name = 'tiktoken:gpt-4o'
    except Exception:
        enc = tiktoken.get_encoding('o200k_base')
        enc_name = 'tiktoken:o200k_base'
except Exception:
    enc = None
    enc_name = 'heuristic'

prefix = 'You will receive a large block of filler text. Ignore it all and answer with exactly OK.\n\n'
suffix = '\n\nAnswer with exactly OK.'

if enc is not None:
    words = []
    # Unique-ish tokens to avoid aggressive compression / merges.
    i = 0
    text = prefix + suffix
    token_count = len(enc.encode(text))
    while token_count < TARGET_TOKENS - RESERVE_TOKENS:
        chunk = ' '.join(f'w{i+j:07d}_zxqv' for j in range(1000))
        candidate = prefix + (' '.join(words + [chunk]) if words else chunk) + suffix
        token_count = len(enc.encode(candidate))
        words.append(chunk)
        i += 1000
    payload_text = prefix + ' '.join(words) + suffix
    estimated_tokens = len(enc.encode(payload_text))
else:
    # Fallback heuristic: ~4 chars/token is conservative enough for a first probe.
    payload_text = prefix + (' x7qv9m' * ((TARGET_TOKENS - RESERVE_TOKENS) * 4)) + suffix
    estimated_tokens = None

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
}
payload = {
    'model': model,
    'input': payload_text,
    'max_output_tokens': 8,
    'reasoning': {'effort': 'none'},
}

url = base_url + '/v1/responses'
r = requests.post(url, headers=headers, json=payload, timeout=300)
result = {
    'url': url,
    'model': model,
    'tokenizer': enc_name,
    'estimated_input_tokens': estimated_tokens,
    'status_code': r.status_code,
}
try:
    data = r.json()
    result['response'] = data
except Exception:
    result['text_prefix'] = r.text[:2000]

print(json.dumps(result, ensure_ascii=False))
