# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Test Script': 'TestScript',
	}

def TestScript(config):
	seq = []
	seqTime = 0
	
	def pushSeqCmd(dt, cmd, arg, msg = ''):
		nonlocal seq, seqTime
		seqTime += dt
		seq.append({
			'time': round(seqTime, 2),
			'cmd': cmd,
			'arg': arg,
			'msg': msg,
		})
		
	def getLastSeqTime():
		nonlocal seq
		return float(seq[len(seq) - 1]['time'])

	dt = 0.3
	
	pushSeqCmd(dt, '', '', 'Test message')
	pushSeqCmd(dt, 'scriptSpeech', 'Test speech')
	pushSeqCmd(dt, '', '', 'Waiting 3 seconds')
	pushSeqCmd(3, '', '', 'End test script')
	return seq


def test():
	seq = []
	seqTime = 0
	
	def pushSeqCmd(dt, cmd, arg, msg = ''):
		nonlocal seq, seqTime
		seqTime += dt
		seq.append({
			'time': round(seqTime, 2),
			'cmd': cmd,
			'arg': arg,
			'msg': msg,
		})
		
	def getLastSeqTime():
		nonlocal seq
		return float(seq[len(seq) - 1]['time'])

	dt = 0.2
	
	pushSeqCmd(dt, 'scriptSpeech', 'Autostart complete')
	pushSeqCmd(dt, 'scriptSpeech', 'Autostop complete')
	pushSeqCmd(5, '', '', 'end')
	
	
	"""
	# Timing test:
	pushSeqCmd(dt, '', '', 'Starting seq')
	pushSeqCmd(3, '', '', '3 seconds in')
	
	timer1ProcessTime = 5
	timer1Start = getLastSeqTime()
	pushSeqCmd(dt, '', '', "started 5 second timer")
	
	pushSeqCmd(1, '', '', "doing stuff 1")
	pushSeqCmd(1, '', '', "doing stuff 2")
	pushSeqCmd(1, '', '', "doing stuff 3")
	
	timer2ProcessTime = 10
	timer2Start = getLastSeqTime()
	pushSeqCmd(dt, '', '', "started 10 second timer")
	
	timer1End = timer1ProcessTime - (getLastSeqTime() - timer1Start)
	
	pushSeqCmd(timer1End, '', '', 'stopping timer 1')
	
	pushSeqCmd(1, '', '', "doing stuff 4")
	pushSeqCmd(1, '', '', "doing stuff 5")
	pushSeqCmd(1, '', '', "doing stuff 6")
	
	timer2End = timer2ProcessTime - (getLastSeqTime() - timer2Start)
	pushSeqCmd(timer2End, '', '', 'stopping timer 2')
	# End timing test
	"""
	
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_LWIN}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_RWIN}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{RWIN}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{LWIN}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_RCONTROL}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_CONTROL}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_LSHIFT}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_SHIFT}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_RMENU}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_MENU}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_RMENU down}a{VK_RMENU up}')
	#pushSeqCmd(dt, 'scriptKeyboard', 'a')
	"""
	pushSeqCmd(dt, 'scriptKeyboard', '{SCROLLLOCK}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SPACE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LSHIFT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_PAUSE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_MODECHANGE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{BACK}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HOME}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F23}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F22}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F21}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F20}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HANGEUL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_KANJI}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RIGHT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{BS}')
	pushSeqCmd(dt, 'scriptKeyboard', '{HOME}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F4}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_ACCEPT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F18}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SNAPSHOT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_PA1}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NONAME}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{ZOOM}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_ATTN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F10}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F22}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F23}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F20}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F21}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SCROLL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{TAB}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F11}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_END}')
	pushSeqCmd(dt, 'scriptKeyboard', '{LEFT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_UP}')
	pushSeqCmd(dt, 'scriptKeyboard', '{NUMLOCK}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_APPS}')
	pushSeqCmd(dt, 'scriptKeyboard', '{PGUP}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_CONTROL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LEFT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{PRTSC}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD4}')
	pushSeqCmd(dt, 'scriptKeyboard', '{CAPSLOCK}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_CONVERT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_PROCESSKEY}')
	pushSeqCmd(dt, 'scriptKeyboard', '{ENTER}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SEPARATOR}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RWIN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NEXT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F1}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2},')
	pushSeqCmd(dt, 'scriptKeyboard', '{F3}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F4}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F5}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F6}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F7}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F9}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_ADD}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RCONTROL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RETURN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{BREAK}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD9}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{RWIN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_KANA},')
	pushSeqCmd(dt, 'scriptKeyboard', '{PGDN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD3}')
	pushSeqCmd(dt, 'scriptKeyboard', '{DEL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD1}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD0}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD7}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD6}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD5}')
	pushSeqCmd(dt, 'scriptKeyboard', '{DELETE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_PRIOR}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SUBTRACT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{HELP},')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_PRINT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_BACK}')
	pushSeqCmd(dt, 'scriptKeyboard', '{CAP}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RBUTTON}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LWIN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{DOWN},')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HELP}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NONCONVERT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{BACKSPACE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SELECT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_TAB}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HANJA},')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMPAD2}')
	pushSeqCmd(dt, 'scriptKeyboard', '{INSERT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F9}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_DECIMAL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_FINAL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_EXSEL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{RMENU}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F3}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F2}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F1}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F7}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F6}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F5}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_CRSEL},')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SHIFT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_EREOF}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_CANCEL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_DELETE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HANGUL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_MBUTTON}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_NUMLOCK}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_CLEAR}')
	pushSeqCmd(dt, 'scriptKeyboard', '{END}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_MENU}')
	pushSeqCmd(dt, 'scriptKeyboard', '{SPACE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{BKSP}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_INSERT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F18}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F19}')
	pushSeqCmd(dt, 'scriptKeyboard', '{ESC}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_MULTIPLY}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F12}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F13}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F10}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F11}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F16}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F17}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F14}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F15}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F24}')
	pushSeqCmd(dt, 'scriptKeyboard', '{RIGHT}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F24}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_CAPITAL}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LBUTTON}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_OEM_CLEAR}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_ESCAPE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{UP}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_DIVIDE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{INS}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_JUNJA}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F19}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_EXECUTE}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_PLAY}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RMENU}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F13}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F12}')
	pushSeqCmd(dt, 'scriptKeyboard', '{LWIN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_DOWN}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F17}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F16}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F15}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_F14}')
	"""
	
	#pushSeqCmd(dt, 'scriptKeyboard', '%a')
	
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_ADD down}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_ADD up}')
	#pushSeqCmd(dt, 'scriptKeyboard', '{VK_RWIN up}')
	return seq
