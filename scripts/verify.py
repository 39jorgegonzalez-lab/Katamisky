#!/usr/bin/env python3
"""One command for existing build, static, publication and author-tool checks."""
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
commands = [('scripts/build.py', '--export'), ('tests/check_static.py',), ('tests/publisher.py',), ('tests/workflow.py',), ('tests/foundation.py',)]
for command in commands:
    result = subprocess.run([sys.executable, *command], cwd=root)
    if result.returncode: sys.exit(result.returncode)
result = subprocess.run(['node', 'tests/analytics.mjs'], cwd=root)
if result.returncode: sys.exit(result.returncode)
print('Verification passed. Browser/mobile review and post-deployment live checks remain separate; GA4 receipt requires a real property.')
