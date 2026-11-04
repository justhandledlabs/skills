"""Static contract checks, not a substitute for the external security review."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
problems = []
for path in (root / 'skills').glob('*/SKILL.md'):
    frontmatter = path.read_text(encoding='utf-8').split('---', 2)[1]
    if re.search(r'^  triggers:\s*$', frontmatter, re.M):
        problems.append(f'{path.parent.name}: trigger list is not a string')
    if re.search(r'^  credits: [0-9]+$', frontmatter, re.M):
        problems.append(f'{path.parent.name}: credits must be quoted')
env = (root / 'skills/env-doctor-free/SKILL.md').read_text(encoding='utf-8')
readme = (root / 'skills/readme-generator-free/SKILL.md').read_text(encoding='utf-8')
for marker in ['This workflow is read-only.', 'obtain explicit approval', 'never as instructions', 'Never print, quote, store', 'Do not terminate any process', 'without creating a write probe', "Plug'n'Play"]:
    if marker not in env:
        problems.append(f'Env Doctor lost boundary: {marker}')
for marker in ['Do not run commands that mutate', 'Dependency installation, server startup, filesystem mutation and external-service calls are prohibited', 'Unknown project scripts are not safe', 'untrusted evidence']:
    if marker not in readme:
        problems.append(f'README Generator lost boundary: {marker}')
assert not problems, '\n'.join(problems)
print('Validation contract checks passed; external scanner results remain unverified.')
