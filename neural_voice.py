import os
from google import genai
from google.genai import types
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

class VoiceEngine:
    def __init__(self):
        print("🎚️ Initializing Google AI Studio (Gemini) Voice Engine...")
        
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
            
        self.client = genai.Client(api_key=self.api_key)

    def _podcast_mastering(self, sound):
        """Applies true crime EQ to the Gemini audio output."""
        sound = sound.low_pass_filter(8000) 
        sound = compress_dynamic_range(sound, threshold=-15.0, ratio=5.0, attack=5.0, release=50.0)
        sound = normalize(sound, headroom=0.1)
        return sound

    def generate_acting_line(self, acting_text, index, voice_name="Charon"):
        filename = f"temp_voice_{index}.wav"
        print(f"🎙️ Gemini Casting '{voice_name}': '{acting_text}'")

        try:
            # Configure Gemini to output audio using the dynamically selected voice
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )

            # Prompting the LLM to act as a professional voice actor
            prompt = f"You are an elite True Crime documentary narrator. Read the following line verbatim. Apply the emotions and stage directions indicated in brackets. Use the ellipses for dramatic pauses. Do not add any conversational filler. Just perform the line: {acting_text}"

            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt,
                config=config
            )

            # Extract the raw WAV audio bytes from the Gemini response
            audio_bytes = None
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        audio_bytes = part.inline_data.data
                        break

            if not audio_bytes:
                print(f"⚠️ No audio data returned for line {index}")
                return None

            temp_raw = f"temp_raw_{index}.wav"
            with open(temp_raw, "wb") as f:
                f.write(audio_bytes)

            sound = AudioSegment.from_file(temp_raw)
            sound = self._podcast_mastering(sound)
            sound.export(filename, format="wav")

            if os.path.exists(temp_raw):
                os.remove(temp_raw)

            return filename

        except Exception as e:
            print(f"⚠️ Gemini Audio Generation Failed: {e}")
            return None
