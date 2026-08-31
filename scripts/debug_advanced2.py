import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from diverge.output import advanced_mode
from diverge import config

print('DB_PATH:', config.DB_PATH)

# Test with empty window (latest)
result = advanced_mode.get_advanced_view('AAPL', '', db_path=config.DB_PATH)
print('Result with empty window:', result)

# Test with explicit window
result2 = advanced_mode.get_advanced_view('AAPL', None, db_path=config.DB_PATH)
print('Result with None window:', {k: v for k, v in (result2 or {}).items() if k not in ['trace']} if result2 else None)

# Also test what mode_api does
from diverge.output import mode_api
status, data = mode_api.handle_get_advanced('AAPL', '', db_path=config.DB_PATH)
print('mode_api status:', status)
print('mode_api composite_score:', data.get('composite_score'))
