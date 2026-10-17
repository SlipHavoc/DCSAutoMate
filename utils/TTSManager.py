import win32com.client

class TTSManager:
	def __init__(self, config):
		self.config = config
		self.speakerId = self.config.get('ttsVoiceId', 1)
		self.rate = self.config.get('ttsRate', 3)
		self.volume = self.config.get('ttsVolume', 75)
		self.speaker = self.getTtsSpeaker()

	# speakerId indexes the installed SAPI voices, so the voice it picks depends on the machine.
	# This code adapted from: https://stackoverflow.com/questions/31167967/python-3-4-text-to-speech-with-sapi
	# For more docs, see: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723609(v=vs.85)
	def getTtsSpeaker(self):
		try:
			speaker = win32com.client.Dispatch("SAPI.SpVoice")
			voices = speaker.GetVoices()
			# for voice in voices:
			# 	print(voice.GetAttribute("Name"))
			# print(voices.Item(speakerId).GetAttribute("Name")) # speaker name

			# Check if the requested speakerId is valid
			if self.speakerId < voices.Count:
				speaker.Voice = voices.Item(self.speakerId) # set voice (see Windows Text-to-Speech settings)

			speaker.Rate = self.rate # -10 is slowest, 10 is fastest, 0 is default.
			speaker.Volume = self.volume # 0-100, 0 is quietest, 100 is default.
			return speaker
		except Exception as e:
			print(f"Error initializing TTS: {e}")
			return None

	# If asyncFlag is false, program execution will stop while speaking.
	def speak(self, string, asyncFlag=True):
		if not self.config.get('disableSpeech', False) and self.speaker:
			try:
				SVSFlag = 1 if asyncFlag is True else 0 # Makes the speaking asyncronous so it doesn't hold up the script.  See https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms720892(v=vs.85)
				# SAPI only autodetects XML when the string starts with a tag, so force it (SVSFIsXML) for mid-sentence tags like <pron>.
				if '<' in string:
					SVSFlag |= 8
				self.speaker.Speak(string, SVSFlag)
			except Exception as e:
				print(f"Error speaking text '{string}': {e}")

	def updateSettings(self, config):
		self.config = config
		self.speakerId = self.config.get('ttsVoiceId', 1)
		self.rate = self.config.get('ttsRate', 3)
		self.volume = self.config.get('ttsVolume', 75)
		self.speaker = self.getTtsSpeaker()  # Recreate speaker with new settings
