import traceback
from honcho_integration.client import HonchoClientConfig, get_honcho_client
from honcho_integration.session import HonchoSessionManager

hcfg = HonchoClientConfig.from_global_config()
print('cfg', hcfg.enabled, hcfg.api_key, hcfg.base_url, hcfg.workspace_id)
client = get_honcho_client(hcfg)
print('client ok', client)
mgr = HonchoSessionManager(honcho=client, config=hcfg, context_tokens=hcfg.context_tokens)
print('manager ok')
try:
    sess = mgr.get_or_create('hermes-agent')
    print('session ok', sess)
    print('messages', len(getattr(sess, 'messages', []) or []))
except Exception as e:
    print('ERROR', repr(e))
    traceback.print_exc()
