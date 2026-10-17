"""Pure parts of tools/publishRelease.py: which files are published, the release notes, and the personal-information scan.

The scan tests use a stand-in private term, as this file is itself published.
"""
import os
import sys

import pytest

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
toolsDir = os.path.join(projectRoot, 'tools')
for path in (projectRoot, toolsDir):
	if path not in sys.path:
		sys.path.insert(0, path)

from publishRelease import findPersonalInfo, printableStrings, publicFiles, releaseNotes


# -----------------------------------------------------------------------
# publicFiles — the allow-list of tracked files that go to the public repo
# -----------------------------------------------------------------------

def test_appSourceIsPublished():
	files = ['DCSAutoMate.py', 'DCSControlPanel.py', 'engine/DCSSeqExecute.py', 'network/DCSDirectManager.py', 'utils/version.py', 'DCSAutoMateScripts/FA-18C.py', 'Scripts/Hooks/DCSAutoMateHook.lua', 'config/controlMappings/FA-18C_hornet.json', 'README.md', 'LICENSE']
	assert publicFiles(files) == sorted(files)


def test_privateFoldersAreNotPublished():
	files = ['archive/DCSMonitor/DCSMonitor.py', 'archive/listener.py', 'keyboard tests/pywinauto-test.py']
	assert publicFiles(files) == []


def test_agentKnowledgeAndInstructionsArePublished():
	files = ['.agent/retros/a.md', '.agent/research/b.md', '.agent/decisions/c.md', '.agent/snippets/d.lua', 'todos/release-2.0.md', '.github/copilot-instructions.md', '.github/agents/module-control-extractor.agent.md', 'AGENTS.md', 'docs/AGENT_USAGE_GUIDE.md']
	assert publicFiles(files) == sorted(files)


def test_unlistedTopLevelFilesAreNotPublished():
	assert publicFiles(['baseline.json', 'DCS BIOS bugs.txt', 'newNotes.md', 'scratch/x.py', 'DCSAutoMate.code-workspace']) == []


def test_unfinishedScriptsAndManualTestsAreNotPublished():
	files = ['DCSAutoMateScripts/test.py', 'DCSAutoMateScripts/M-2000C -- WIP_dcsbios.py', 'tests/manual_test.py', 'tests/test_version.py']
	assert publicFiles(files) == ['tests/test_version.py']


def test_validationResultsAndMigrationToolsArePublished():
	files = ['tools/validation-scripts/validateControlMapping.py', 'tools/validation-scripts/validation_A10C.json', 'tools/validation-scripts/run.txt', 'tools/dcs-bios-migration/migrate.py']
	assert publicFiles(files) == sorted(files)


def test_bytecodeIsNeverPublished():
	assert publicFiles(['engine/__pycache__/x.pyc', 'tools/extraction-scripts/extract_A4EC.py']) == ['tools/extraction-scripts/extract_A4EC.py']


def test_privateTermsFileIsNeverPublished():
	assert publicFiles(['config/privateTerms.txt', 'config/simCommands.json']) == ['config/simCommands.json']


# -----------------------------------------------------------------------
# releaseNotes — one version's block from the README's release notes
# -----------------------------------------------------------------------

README = """# DCSAutoMate 2.1.0
Intro.

# Release notes:
* 2027/01/02 - Version 2.1.0
* Fixed a thing.

* 2026/10/20 - Version 2.0.0
* **Big feature**: Details.
* Another change.

* 2025/02/19 - Version 1.0
* First release.
"""


def test_releaseNotesForAMiddleVersion():
	assert releaseNotes(README, '2.0.0') == '* **Big feature**: Details.\n* Another change.'


def test_releaseNotesForTheLastVersionRunToTheEnd():
	assert releaseNotes(README, '1.0') == '* First release.'


def test_releaseNotesDontMatchAVersionPrefix():
	with pytest.raises(ValueError):
		releaseNotes(README, '2.0')


def test_releaseNotesForAMissingVersionIsAnError():
	with pytest.raises(ValueError):
		releaseNotes(README, '3.0.0')


def test_releaseNotesStopAtTheNextHeading():
	text = '# Release notes:\n* 2026/10/20 - Version 2.0.0\n* Change.\n\n# Appendix\nNot notes.\n'
	assert releaseNotes(text, '2.0.0') == '* Change.'


HEADING_README = """# Release notes:
## 2027/01/02 - Version 2.1.0
* Fixed a thing.

## 2026/10/20 - Version 2.0.0
* **Big feature**: Details.
### Script authors
* A change for them.

## 2025/02/19 - Version 1.0
* First release.

# Appendix
Not notes.
"""


def test_releaseNotesUnderVersionHeadings():
	assert releaseNotes(HEADING_README, '2.0.0') == '* **Big feature**: Details.\n### Script authors\n* A change for them.'


def test_releaseNotesUnderTheLastVersionHeadingStopAtAHigherHeading():
	assert releaseNotes(HEADING_README, '1.0') == '* First release.'


# -----------------------------------------------------------------------
# findPersonalInfo — what would identify the author
# -----------------------------------------------------------------------

TERMS = ['Zelda']


def test_privateTermIsFound():
	hits = findPersonalInfo('Thanks to Zelda for testing.', TERMS, 'link')
	assert len(hits) == 1 and 'Zelda' in hits[0]


def test_privateTermIsCaseSensitiveAndWholeWord():
	assert findPersonalInfo('ZELDA sites, Zeldas, zelda', TERMS, 'link') == []


def test_privateTermWithPossessiveIsFound():
	assert len(findPersonalInfo("Zelda's notes", TERMS, 'link')) == 1


def test_userNameInAPathIsFoundInAnyCase():
	text = r'C:\Users\LINK\AppData\Local and c:/users/link/Saved Games'
	assert len(findPersonalInfo(text, TERMS, 'link')) == 2


def test_otherUsersPathsAndLongerNamesAreNotFound():
	text = r'C:\Users\qt\work\qtbase and C:\Users\linkfan\x and %USERPROFILE%\Saved Games'
	assert findPersonalInfo(text, TERMS, 'link') == []


def test_emailOtherThanTheAllowedOneIsFound():
	# Built at run time, so this file doesn't contain a real-looking address for the scan to find.
	address = 'someone' + '@' + 'mailhost.net'
	hits = findPersonalInfo(f'Mail {address} or SlipHavoc@protonmail.com', TERMS, 'link')
	assert len(hits) == 1 and address in hits[0]


def test_reservedExampleDomainEmailsAreAllowed():
	assert findPersonalInfo('someone@example.com, a@b.example.org, x@mail.test', TERMS, 'link') == []


def test_binaryDataSkipsTheEmailCheck():
	assert findPersonalInfo('maintainer' + '@' + 'mailhost.net', TERMS, 'link', binary=True) == []


def test_binaryDataFlagsPrivateTermsOnlyAsPathFolders():
	assert findPersonalInfo('Fri;Zelda;Sun', TERMS, 'link', binary=True) == []
	assert len(findPersonalInfo(r'D:\builds\zelda\out.pdb', TERMS, 'link', binary=True)) == 1


def test_noTermsOrUserName():
	assert findPersonalInfo(r'C:\Users\link\x Zelda', [], '') == []


def test_hitShowsSurroundingText():
	hits = findPersonalInfo('line one\nwritten by Zelda in 2026\nline three', TERMS, 'link')
	assert hits == ['line 2: written by Zelda in 2026']


# -----------------------------------------------------------------------
# printableStrings — text runs inside binary data (the files inside an exe)
# -----------------------------------------------------------------------

def test_asciiRunsAreFound():
	data = b'\x00\x01C:\\Users\\link\\x\x00\xff\xfeok\x00'
	assert 'C:\\Users\\link\\x' in list(printableStrings(data))


def test_utf16RunsAreFound():
	data = b'\x00\x00' + 'C:\\Users\\link'.encode('utf-16-le') + b'\x00\x00'
	assert 'C:\\Users\\link' in list(printableStrings(data))


def test_shortRunsAreSkipped():
	assert list(printableStrings(b'\x00ab\x00cd\x00')) == []
