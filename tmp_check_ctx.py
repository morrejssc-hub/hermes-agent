import yaml, os, json
from pathlib import Path
from agent.model_metadata import get_model_context_length
cfg = yaml.safe_load(Path('/home/holo/.hermes/config.yaml').read_text())
model = cfg.get('model', {}).get('default')
provider = cfg.get('model', {}).get('provider')
base_url = cfg.get('model', {}).get('base_url')
api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('CODEX_API_KEY') or os.environ.get('OPENROUTER_API_KEY') or ''
ctx = get_model_context_length(model=model, base_url=base_url, api_key=api_key, provider=provider)
print(json.dumps({'model': model, 'provider': provider, 'base_url': base_url, 'context_length': ctx}, ensure_ascii=False))
