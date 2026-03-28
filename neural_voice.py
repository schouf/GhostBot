import os
import wave
import time
import torchaudio as ta
from google import genai
from google.genai import types
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

class VoiceEngine:
    def __init__(self):
        print("🎚️ Initializing GhostBot Master-Director Engine...")
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=self.api_key)

        try:
            # THE FIX: Importing the flagship 1B parameter model, NOT the stripped-down Turbo version
            from chatterbox.tts import ChatterboxTTS
            print("🧠 Loading FULL Chatterbox 1B Model on CPU (Prioritizing Quality over Speed)...")
            self.chatterbox = ChatterboxTTS.from_pretrained(device="cpu")
        except Exception as e:
            print(f"⚠️ Chatterbox initialization failed: {e}. Will use Gemini TTS fallback.")
            self.chatterbox = None

    def _podcast_mastering(self, sound):
        """Applies true crime EQ. Pacing is now controlled naturally by Chatterbox tags."""
        sound = sound.low_pass_filter(8000) 
        sound = compress_dynamic_range(sound, threshold=-15.0, ratio=5.0, attack=5.0, release=50.0)
        sound = normalize(sound, headroom=0.1)
        
        # Add a 300ms cinematic pause buffer so the spooky scenes don't rush into each other
        silence = AudioSegment.silent(duration=300)
        sound = sound + silence
        return sound

    def generate_acting_line(self, acting_text, clean_text, style_instruction, index, voice_name="Charon"):
        filename = f"temp_voice_{index}.wav"
        print(f"🎙️ Rendering [{voice_name}] | Vibe: {style_instruction}")

        # ==========================================
        # ATTEMPT 1: FULL CHATTERBOX (Expressive Cloning)
        # ==========================================
        if self.chatterbox:
            try:
                voice_path = f"voices/{voice_name}.wav"
                
                if os.path.exists(voice_path):
                    wav = self.chatterbox.generate(acting_text, audio_prompt_path=voice_path)
                else:
                    print(f"⚠️ Warning: {voice_path} not found. Using default base voice.")
                    wav = self.chatterbox.generate(acting_text)
                
                temp_raw = f"temp_raw_cb_{index}.wav"
                ta.save(temp_raw, wav, self.chatterbox.sr)
                
                sound = AudioSegment.from_file(temp_raw)
                sound = self._podcast_mastering(sound)
                sound.export(filename, format="wav")
                
                if os.path.exists(temp_raw): 
                    os.remove(temp_raw)
                    
                return filename
            except Exception as e:
                print(f"⚠️ Chatterbox failed for line {index}: {e}. Falling back to Gemini TTS.")

        # ==========================================
        # ATTEMPT 2: GEMINI TTS FALLBACK (Safe)
        # ==========================================
        print("🔄 Using Gemini TTS Fallback...")

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            )
        )

        prompt = f"""You are an elite, award-winning voice actor narrating a gritty True Crime documentary. 
YOUR VOCAL STYLE/EMOTION FOR THIS LINE: "{style_instruction}"
Read the following text exactly as written:

{clean_text}"""

        models_to_try = ["gemini-2.5-flash-preview-tts", "gemini-2.5-pro"]

        for model_name in models_to_try:
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=model_name, contents=prompt, config=config
                    )

                    audio_bytes = None
                    if response.candidates and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                audio_bytes = part.inline_data.data
                                break

                    if not audio_bytes: continue 

                    temp_raw = f"temp_raw_{index}.wav"
                    with wave.open(temp_raw, "wb") as wf:
                        wf.setnchannels(1) 
                        wf.setsampwidth(2) 
                        wf.setframerate(24000) 
                        wf.writeframes(audio_bytes)

                    sound = AudioSegment.from_file(temp_raw)
                    sound = self._podcast_mastering(sound)
                    sound.export(filename, format="wav")
                    
                    if os.path.exists(temp_raw): 
                        os.remove(temp_raw)

                    return filename

                except Exception as e:
                    if "429" in str(e) or "503" in str(e): 
                        time.sleep(35 + (attempt * 10))
                    else: 
                        break 
        return None
