import os
import wave
import time
from google import genai
from google.genai import types
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

class VoiceEngine:
    def __init__(self):
        print("🎚️ Initializing Gemini Master-Director Engine...")
        
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
            
        self.client = genai.Client(api_key=self.api_key)

    def _podcast_mastering(self, sound):
        """Applies true crime EQ. Pacing is controlled strictly by SSML."""
        sound = sound.low_pass_filter(8000) 
        sound = compress_dynamic_range(sound, threshold=-15.0, ratio=5.0, attack=5.0, release=50.0)
        sound = normalize(sound, headroom=0.1)
        
        # Add a 300ms cinematic pause buffer so the scenes don't rush into each other
        silence = AudioSegment.silent(duration=300)
        sound = sound + silence
        
        return sound

    def generate_acting_line(self, acting_text, style_instruction, index, voice_name="Charon"):
        filename = f"temp_voice_{index}.wav"
        print(f"🎙️ Gemini Rendering [{voice_name}] | Style: {style_instruction}")

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

        # The Ultimate Fusion Prompt: Macro-Style + Micro-SSML
        prompt = f"""You are an elite, award-winning voice actor narrating a gritty True Crime documentary. 

YOUR VOCAL STYLE/EMOTION FOR THIS LINE: 
"{style_instruction}"

CRITICAL INSTRUCTIONS:
Process the following SSML markup and render the audio performance exactly as tagged. 
Pay strict attention to the <prosody>, <emphasis>, and <break> tags to control speed, pitch, emotion, and dramatic pauses, while maintaining your requested Vocal Style above.

<speak>
{acting_text}
</speak>"""

        # The Waterfall Fallback Architecture
        models_to_try = ["gemini-2.5-pro", "gemini-2.5-flash"]

        for model_name in models_to_try:
            print(f"🔄 Attempting TTS with model: {model_name}")
            
            # 3 Attempts per model to handle temporary 503 overloads or 429 quota hits
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )

                    audio_bytes = None
                    if response.candidates and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                audio_bytes = part.inline_data.data
                                break

                    if not audio_bytes:
                        print(f"⚠️ No audio data returned for line {index} on {model_name}. Retrying...")
                        continue # Skip to the next attempt in the loop

                    temp_raw = f"temp_raw_{index}.wav"
                    
                    # Gemini returns RAW PCM data. We construct the WAV headers manually.
                    with wave.open(temp_raw, "wb") as wf:
                        wf.setnchannels(1) # Mono
                        wf.setsampwidth(2) # 16-bit
                        wf.setframerate(24000) # 24kHz
                        wf.writeframes(audio_bytes)

                    sound = AudioSegment.from_file(temp_raw)
                    sound = self._podcast_mastering(sound)
                    sound.export(filename, format="wav")

                    if os.path.exists(temp_raw):
                        os.remove(temp_raw)

                    print(f"✅ Audio generated successfully with {model_name}")
                    return filename

                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "resource_exhausted" in error_str or "503" in error_str or "unavailable" in error_str:
                        # Escalating sleep timer: 35s, then 45s, then 55s
                        wait_time = 35 + (attempt * 10) 
                        print(f"⏳ Rate limit/Overload ({model_name}). Sleeping {wait_time}s... (Attempt {attempt+1}/3)")
                        time.sleep(wait_time)
                    else:
                        print(f"⚠️ {model_name} Fatal Error: {e}")
                        break # Break the attempt loop for this model and move to the next model
            
            print(f"⏭️ Exhausted attempts for {model_name}, falling back to next available model...")

        print(f"❌ Failed to generate audio for line {index} after exhausting all models and retries.")
        return None
