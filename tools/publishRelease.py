"""Publish a DCSAutoMate release to the public repo, without the private development history.

Usage:
	python tools/publishRelease.py              Dry run: build, copy the public files into the public clone, scan, test, show the changes.
	python tools/publishRelease.py --publish    The same, then commit, tag, push and create the GitHub Release.

The public repo gets one commit per release, made from an allow-list of the files git tracks here (publicFiles), as committed at HEAD.
Nothing is published if the personal-information scan (findPersonalInfo) finds anything in the public files, the zip, or the files inside the exes.
The private terms to scan for are in config/privateTerms.txt (one per line), which git ignores so the list itself is never published.
"""
import argparse
import fnmatch
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repoRoot not in sys.path:
	sys.path.insert(0, repoRoot)

PUBLIC_REPO = 'SlipHavoc/DCSAutoMate'
DEFAULT_PUBLIC_DIR = os.path.join(os.path.dirname(repoRoot), 'DCSAutoMate-Public')
PRIVATE_TERMS_FILE = os.path.join(repoRoot, 'config', 'privateTerms.txt')
ALLOWED_EMAILS = {'sliphavoc@protonmail.com'}

# Top-level files and folders that are published; anything else stays private.
PUBLIC_ROOTS = (
	'DCSAutoMate.py', 'DCSAutoMate.bat', 'DCSAutoMate.spec',
	'DCSControlPanel.py', 'DCSControlPanel.bat', 'DCSControlPanel.spec',
	'README.md', 'DEVELOPMENT.md', 'ARCHITECTURE.md', 'AGENTS.md', 'LICENSE',
	'requirements.txt', 'pytest.ini', '.gitignore',
	'engine/', 'network/', 'utils/', 'DCSAutoMateScripts/', 'Scripts/', 'config/', 'docs/', 'tools/', 'tests/',
	'.agent/', '.github/', 'todos/',
)

# Files inside the published folders that stay private.
PRIVATE_PATTERNS = (
	'*/__pycache__/*', '*.pyc',
	'config/privateTerms.txt',
	'DCSAutoMateScripts/test.py', 'DCSAutoMateScripts/M-2000C*',
	'tests/manual_*',
)

_emailPattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
_versionLinePattern = re.compile(r'^(\*|#+) .* - Version (\S+)\s*$')
_headingPattern = re.compile(r'^(#+)\s')


def publicFiles(trackedFiles):
	"""The tracked files (repo-relative, forward slashes) that go to the public repo, sorted."""
	def isPublic(path):
		if not any(path == root or (root.endswith('/') and path.startswith(root)) for root in PUBLIC_ROOTS):
			return False
		return not any(fnmatch.fnmatchcase(path, pattern) for pattern in PRIVATE_PATTERNS)
	return sorted(path for path in trackedFiles if isPublic(path))


def releaseNotes(readmeText, version):
	"""The README's release notes for one version: the lines under its '## <date> - Version <version>' heading (or '* <date> - Version <version>' line),
	up to the next version, or a heading at the same or a higher level (any heading, for the '*' form)."""
	notes = None
	stopLevel = 0
	for line in readmeText.splitlines():
		versionLine = _versionLinePattern.match(line)
		if notes is None:
			if versionLine and versionLine.group(2) == version:
				notes = []
				marker = versionLine.group(1)
				stopLevel = len(marker) if marker.startswith('#') else 6
			continue
		heading = _headingPattern.match(line)
		if versionLine or (heading and len(heading.group(1)) <= stopLevel):
			break
		notes.append(line)
	if notes is None:
		raise ValueError(f'No release notes for version {version} in the README (expected a heading "## <date> - Version {version}").')
	return '\n'.join(notes).strip()


def _context(line, start, end, width=60):
	if len(line) <= 2 * width:
		return line.strip()
	return line[max(0, start - width):end + width].strip()


def _isReservedExampleEmail(address):
	"""Addresses at domains reserved for examples (RFC 2606), as used in tests and docs."""
	domain = address.rsplit('@', 1)[1].lower()
	return domain.split('.')[-1] in ('test', 'example', 'invalid', 'localhost') or any(domain == name or domain.endswith('.' + name) for name in ('example.com', 'example.org', 'example.net'))


def findPersonalInfo(text, privateTerms, userName, binary=False):
	"""Places in text that could identify the author, as 'line N: <text>'.

	privateTerms match case-sensitively as whole words (so a name doesn't also flag the same letters in capitals, e.g. an acronym).
	userName (this PC's Windows user name) matches in a Users folder path, in any case.
	Emails other than ALLOWED_EMAILS and reserved example domains match.
	binary is for text pulled out of binary files (the third-party DLLs inside the exes), which hold words like localized day names and their authors' emails:
	there, privateTerms only match as a folder in a path, in any case, and emails aren't checked.
	"""
	if binary:
		patterns = [re.compile(rf'(?i)[\\/]{re.escape(term)}(?=[\\/])') for term in privateTerms if term]
	else:
		patterns = [re.compile(rf'(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])') for term in privateTerms if term]
	if userName:
		patterns.append(re.compile(rf'(?i)users[\\/]+{re.escape(userName)}(?![A-Za-z0-9])'))
	hits = []
	for lineNumber, line in enumerate(text.splitlines(), 1):
		for pattern in patterns:
			for match in pattern.finditer(line):
				hits.append(f'line {lineNumber}: {_context(line, match.start(), match.end())}')
		if not binary:
			for match in _emailPattern.finditer(line):
				address = match.group(0)
				if address.lower() not in ALLOWED_EMAILS and not _isReservedExampleEmail(address):
					hits.append(f'line {lineNumber}: {_context(line, match.start(), match.end())}')
	return hits


def printableStrings(data, minLength=4):
	"""Runs of printable ASCII, and of UTF-16LE text, in binary data (like the 'strings' tool)."""
	for match in re.finditer(rb'[\x20-\x7e]{%d,}' % minLength, data):
		yield match.group(0).decode('ascii')
	for match in re.finditer(rb'(?:[\x20-\x7e]\x00){%d,}' % minLength, data):
		yield match.group(0).decode('utf-16-le')


def _git(*args, cwd=repoRoot):
	return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def _run(description, command, cwd=repoRoot, **kwargs):
	print(f'\n== {description}', flush=True)
	result = subprocess.run(command, cwd=cwd, **kwargs)
	if result.returncode != 0:
		sys.exit(f'Stopped: {description} failed (exit code {result.returncode}).')


def readPrivateTerms(path=PRIVATE_TERMS_FILE):
	if not os.path.isfile(path):
		sys.exit(f'Stopped: {path} is missing.  Create it with one private term (e.g. your name) per line; git ignores it.')
	with open(path, encoding='utf-8') as f:
		terms = [line.strip() for line in f if line.strip() and not line.startswith('#')]
	if not terms:
		sys.exit(f'Stopped: {path} has no terms in it.')
	return terms


def scanData(name, data, privateTerms, userName, binary=False):
	"""Personal-information hits in one file's contents, labelled with its name.  Data that isn't UTF-8 text is scanned as binary (its text runs)."""
	if not binary:
		try:
			text = data.decode('utf-8')
		except UnicodeDecodeError:
			binary = True
	if binary:
		text = '\n'.join(printableStrings(data))
	return [f'{name} {hit}' for hit in findPersonalInfo(text, privateTerms, userName, binary)]


def scanExe(name, data, privateTerms, userName):
	"""Hits in every file PyInstaller packed into an exe.  They're all scanned as binary: our own code is compiled, and the rest is third-party."""
	from PyInstaller.archive.readers import CArchiveReader
	hits = scanData(name, data, privateTerms, userName, binary=True)
	with tempfile.TemporaryDirectory() as tempDir:
		exePath = os.path.join(tempDir, 'scanned.exe')
		with open(exePath, 'wb') as f:
			f.write(data)
		archive = CArchiveReader(exePath)
		for entryName in archive.toc:
			entryData = archive.extract(entryName)
			if entryData:
				hits += scanData(f'{name}::{entryName}', entryData, privateTerms, userName, binary=True)
	return hits


def scanPublicDir(publicDir, privateTerms, userName):
	hits = []
	for folder, subfolders, fileNames in os.walk(publicDir):
		subfolders[:] = [subfolder for subfolder in subfolders if subfolder != '.git']
		for fileName in fileNames:
			path = os.path.join(folder, fileName)
			with open(path, 'rb') as f:
				hits += scanData(os.path.relpath(path, publicDir), f.read(), privateTerms, userName)
	return hits


def scanZip(zipPath, privateTerms, userName):
	hits = []
	with zipfile.ZipFile(zipPath) as archive:
		for member in archive.namelist():
			data = archive.read(member)
			label = f'{os.path.basename(zipPath)}::{member}'
			if member.lower().endswith('.exe'):
				hits += scanExe(label, data, privateTerms, userName)
			else:
				hits += scanData(label, data, privateTerms, userName)
	return hits


def exportPublicFiles(publicDir):
	"""Replace everything in the public clone (except .git) with the public files as committed at HEAD.  Returns the file list."""
	files = publicFiles(_git('ls-tree', '-r', '--name-only', '-z', 'HEAD').split('\0'))
	wanted = set(files)
	for entry in os.listdir(publicDir):
		if entry == '.git':
			continue
		path = os.path.join(publicDir, entry)
		if os.path.isdir(path):
			shutil.rmtree(path)
		else:
			os.remove(path)
	tarData = subprocess.run(['git', 'archive', '--format=tar', 'HEAD'], cwd=repoRoot, capture_output=True, check=True).stdout
	with tarfile.open(fileobj=io.BytesIO(tarData)) as archive:
		members = [member for member in archive.getmembers() if member.isfile() and member.name in wanted]
		archive.extractall(publicDir, members=members, filter='data')
	return files


def main():
	from utils.version import APP_VERSION

	parser = argparse.ArgumentParser(description='Publish a DCSAutoMate release to the public repo.  Without --publish this is a dry run.')
	parser.add_argument('--publish', action='store_true', help='Commit, tag and push the public repo, and create the GitHub Release.')
	parser.add_argument('--public-dir', default=DEFAULT_PUBLIC_DIR, help=f'Clone of the public repo (default: {DEFAULT_PUBLIC_DIR}).')
	parser.add_argument('--skip-build', action='store_true', help="Use the exes and zip already built (dry runs only).")
	args = parser.parse_args()

	version = APP_VERSION
	tag = f'v{version}'
	zipPath = os.path.join(repoRoot, f'DCSAutoMate-{version}.zip')
	with open(os.path.join(repoRoot, 'README.md'), encoding='utf-8') as f:
		notes = releaseNotes(f.read(), version)
	privateTerms = readPrivateTerms()
	userName = os.environ.get('USERNAME', '')
	publicDir = os.path.abspath(args.public_dir)
	if not os.path.isdir(os.path.join(publicDir, '.git')):
		sys.exit(f'Stopped: {publicDir} is not a clone of the public repo.  Run: gh repo clone {PUBLIC_REPO} "{publicDir}"')

	print(f'DCSAutoMate {version}: {"PUBLISH" if args.publish else "dry run"} to {publicDir}')
	dirty = _git('status', '--porcelain', '--untracked-files=no').strip()
	if dirty:
		if args.publish:
			sys.exit('Stopped: commit or stash the changes first; the release must be built from committed code.')
		print('Warning: uncommitted changes.  The public files come from HEAD, but the exes are built from the working tree.')
	if args.publish and args.skip_build:
		sys.exit('Stopped: --skip-build is for dry runs; a release is always built fresh.')
	if args.publish and not shutil.which('gh'):
		sys.exit('Stopped: the GitHub CLI (gh) is not on the PATH.  Install it (winget install GitHub.cli), or open a new terminal if you just did.')
	if args.publish:
		if _git('tag', '--list', tag).strip() or _git('ls-remote', '--tags', 'origin', tag, cwd=publicDir).strip():
			sys.exit(f'Stopped: tag {tag} already exists.  Bump APP_VERSION in utils/version.py.')

	if not args.skip_build:
		_run('Tests', [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'])
		buildEnv = dict(os.environ, DCSAUTOMATE_NO_PAUSE='1')
		for script in ('Build_DCSAutoMate.bat', 'Build_DCSControlPanel.bat'):
			_run(f'Build ({script})', ['cmd', '/c', os.path.join('tools', script)], env=buildEnv, input=b'y\n')
		_run('Zip', ['cmd', '/c', os.path.join('tools', 'Make Zip Distribution.bat'), 'nopause'])
	if not os.path.isfile(zipPath):
		sys.exit(f'Stopped: {zipPath} not found.')

	print('\n== Copying the public files into the public clone', flush=True)
	files = exportPublicFiles(publicDir)
	print(f'{len(files)} files.')

	print('\n== Scanning for personal information', flush=True)
	identity = f"author: {_git('config', 'user.name', cwd=publicDir).strip()} <{_git('config', 'user.email', cwd=publicDir).strip()}>"
	hits = scanData('public commit', identity.encode('utf-8'), privateTerms, userName)
	hits += scanPublicDir(publicDir, privateTerms, userName)
	hits += scanZip(zipPath, privateTerms, userName)
	if hits:
		print('\n'.join(hits))
		sys.exit(f'Stopped: {len(hits)} possible personal-information hits (above).  Nothing was published.')
	print('No personal information found.')

	_run('Tests in the public copy', [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'], cwd=publicDir, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))

	_git('add', '-A', cwd=publicDir)
	print('\n== Changes in the public repo')
	print(_git('diff', '--cached', '--stat', cwd=publicDir) or 'None.')
	print(f'== Release notes for {tag}\n{notes}\n')
	if not args.publish:
		_git('reset', '-q', cwd=publicDir)
		print('Dry run done; nothing was committed or pushed.  Run again with --publish to release.')
		return

	if input(f'Publish {tag} to github.com/{PUBLIC_REPO}?  Type the version to confirm: ').strip() != version:
		sys.exit('Not published.')
	_run('Commit', ['git', 'commit', '-q', '-m', f'DCSAutoMate {version}'], cwd=publicDir)
	_run('Tag', ['git', 'tag', tag], cwd=publicDir)
	_run('Push', ['git', 'push', 'origin', 'HEAD', tag], cwd=publicDir)
	with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
		f.write(notes)
		notesFile = f.name
	try:
		_run('GitHub Release', ['gh', 'release', 'create', tag, zipPath, '--repo', PUBLIC_REPO, '--title', f'DCSAutoMate {version}', '--notes-file', notesFile])
	finally:
		os.remove(notesFile)
	_run('Tag the private repo', ['git', 'tag', tag])
	_run('Push the private tag', ['git', 'push', 'origin', tag])
	print(f'\nPublished: https://github.com/{PUBLIC_REPO}/releases/tag/{tag}')


if __name__ == '__main__':
	main()