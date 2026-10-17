import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mappingDir = os.path.join(repoRoot, 'config', 'controlMappings')
scriptDir = os.path.join(repoRoot, 'tools', 'mapping-scripts')

backupDir = tempfile.mkdtemp(prefix='mapRegression')
for path in glob.glob(os.path.join(mappingDir, '*.json')):
	shutil.copy2(path, backupDir)

failures = 0
try:
	for script in sorted(glob.glob(os.path.join(scriptDir, 'map_*.py'))):
		before = {os.path.basename(p): os.path.getmtime(p) for p in glob.glob(os.path.join(mappingDir, '*.json'))}
		proc = subprocess.run([sys.executable, script], cwd=repoRoot, capture_output=True, text=True, encoding='utf-8', errors='replace')
		after = {os.path.basename(p): os.path.getmtime(p) for p in glob.glob(os.path.join(mappingDir, '*.json'))}
		written = sorted(name for name in after if after[name] != before.get(name))
		name = os.path.basename(script)
		if proc.returncode != 0 or not written:
			failures += 1
			print(f'FAIL {name}: exit={proc.returncode}, wrote={written}')
			print('\n'.join(proc.stderr.strip().splitlines()[-5:]))
			continue
		for fileName in written:
			oldPath = os.path.join(backupDir, fileName)
			newPath = os.path.join(mappingDir, fileName)
			if not os.path.exists(oldPath):
				failures += 1
				print(f'FAIL {name}: created new file {fileName}')
				continue
			with open(oldPath, encoding='utf-8') as f:
				oldData = json.load(f)
			with open(newPath, encoding='utf-8') as f:
				newData = json.load(f)
			oldControls = oldData.get('controls', {})
			newControls = newData.get('controls', {})
			sameBytes = open(oldPath, 'rb').read() == open(newPath, 'rb').read()
			if oldData == newData:
				print(f'OK   {name} -> {fileName} ({len(newControls)} controls, content identical, bytes {"identical" if sameBytes else "differ (key order only)"})')
				continue
			failures += 1
			added = sorted(set(newControls) - set(oldControls))
			removed = sorted(set(oldControls) - set(newControls))
			changed = sorted(k for k in set(oldControls) & set(newControls) if oldControls[k] != newControls[k])
			otherKeys = sorted(k for k in set(oldData) | set(newData) if k != 'controls' and oldData.get(k) != newData.get(k))
			print(f'DIFF {name} -> {fileName}: added={len(added)} removed={len(removed)} changed={len(changed)} otherTopLevel={otherKeys}')
			for k in (added + removed + changed)[:10]:
				print(f'     {k}')
finally:
	for path in glob.glob(os.path.join(backupDir, '*.json')):
		shutil.copy2(path, mappingDir)
	shutil.rmtree(backupDir)

print(f'\n{failures} failure(s)')
