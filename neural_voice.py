import os
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

class VoiceEngine:
    def __init__(self):
        print("🎚️ Initializing Google Cloud True Crime Voice Engine...")
        
        # We must initialize the client using the API key passed from GitHub Secrets
        api_key = os.environ.get("GOOGLE_TTS_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_TTS_API_KEY environment variable not set.")
            
        self.client = texttospeech.TextToSpeechClient(
            client_options={"api_key": api_key}
        )

        # "Journey" voices are Google's highest tier for realistic narration.
        # en-US-Journey-D is a deep, resonant male voice perfect for True Crime.
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-D"
        )
        
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=0.90, # Slightly slowed down for suspense
            pitch=-2.0 # Dropped slightly for a darker tone
        )

    def _podcast_mastering(self, sound):
        """Applies light mastering since Google Journey voices are already high quality."""
        # 1. Very slight bass boost
        sound = sound.low_pass_filter(10000) 
        
        # 2. Light Compression to keep volume consistent
        sound = compress_dynamic_range(sound, threshold=-15.0, ratio=4.0, attack=5.0, release=50.0)
        
        # 3. Maximize Volume
        sound = normalize(sound, headroom=0.1)
        
        # 4. Snappy pacing: Trim dead air faster so the cuts feel more urgent
        sound = sound.strip_silence(silence_len=100, silence_thresh=-45, padding=40)

        return sound

    def generate_acting_line(self, text, index, emotion="serious"):
        filename = f"temp_voice_{index}.wav"
        print(f"🎙️ Generating Google TTS: '{text}'")

        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)

            response = self.client.synthesize_speech(
                input=synthesis_input, voice=self.voice, audio_config=self.audio_config
            )

            temp_raw = f"temp_raw_{index}.wav"
            with open(temp_raw, "wb") as out:
                out.write(response.audio_content)

            sound = AudioSegment.from_file(temp_raw)

            # Master the audio
            sound = self._podcast_mastering(sound)
            sound.export(filename, format="wav")

            if os.path.exists(temp_raw):
                os.remove(temp_raw)

            return filename

        except Exception as e:
            print(f"⚠️ Google TTS Generation Failed: {e}")
            return None
