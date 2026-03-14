import os
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

class VoiceEngine:
    def __init__(self):
        print("🎚️ Initializing Dynamic Google Cloud Voice Engine...")
        
        api_key = os.environ.get("GOOGLE_TTS_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_TTS_API_KEY environment variable not set.")
            
        self.client = texttospeech.TextToSpeechClient(
            client_options={"api_key": api_key}
        )
        
        # AudioConfig is kept clean. We let the SSML dictate the pacing and pitch.
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

    def _podcast_mastering(self, sound):
        """Applies true crime EQ. Relies purely on SSML for pacing/pauses."""
        # Darker EQ: Cut off high frequencies to keep it bass-heavy
        sound = sound.low_pass_filter(8000) 
        
        # Aggressive Compression: Keeps whispers and loud tones at the same volume
        sound = compress_dynamic_range(sound, threshold=-15.0, ratio=5.0, attack=5.0, release=50.0)
        
        # Maximize Volume
        sound = normalize(sound, headroom=0.1)

        return sound

    def generate_acting_line(self, ssml_text, index, voice_name="en-US-Studio-Q"):
        filename = f"temp_voice_{index}.wav"
        
        try:
            # Dynamically set the voice based on Gemini's casting choice
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_name[:5], # Extracts 'en-US' or 'en-GB' from the model name
                name=voice_name
            )

            # Properly wrap the LLM's raw SSML in standard speak tags
            formatted_ssml = f"<speak>{ssml_text}</speak>"
            synthesis_input = texttospeech.SynthesisInput(ssml=formatted_ssml)

            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=self.audio_config
            )

            temp_raw = f"temp_raw_{index}.wav"
            with open(temp_raw, "wb") as out:
                out.write(response.audio_content)

            sound = AudioSegment.from_file(temp_raw)
            sound = self._podcast_mastering(sound)
            sound.export(filename, format="wav")

            if os.path.exists(temp_raw):
                os.remove(temp_raw)

            return filename

        except Exception as e:
            print(f"⚠️ Google TTS Generation Failed for {voice_name}: {e}")
            return None
