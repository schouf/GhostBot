import os
import random
import time
import json
import glob
import requests
import urllib.parse
import base64
import numpy as np
import PIL.Image
from google import genai
from google.genai import types
from moviepy.editor import *
from moviepy.video.fx.all import colorx
from moviepy.audio.fx.all import audio_loop
from faster_whisper import WhisperModel
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from neural_voice import VoiceEngine
import meta_upload

# ================== CONFIG ==================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
YOUTUBE_TOKEN_VAL = os.environ.get("YOUTUBE_TOKEN_JSON")

# TITANIUM PIPELINE KEYS
CF_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

CHANNEL_HANDLE = "@TheGlitchArchive"
TOPICS_FILE = "topics.txt"

# Video Settings
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280
IMAGE_TRANSITION_TIME = 3.0

if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

SFX_MAP = {
    "knock": "knock.mp3",
    "bang": "knock.mp3",
    "scream": "scream.mp3",
    "yell": "scream.mp3",
    "step": "footsteps.mp3",
    "run": "footsteps.mp3",
    "static": "static.mp3",
    "glitch": "static.mp3",
    "breath": "whisper.mp3",
    "whisper": "whisper.mp3",
    "thud": "thud.mp3"
}

# ================== ANTI BAN ==================
def anti_ban_sleep():
    if os.environ.get("GITHUB_ACTIONS") == "true":
        sleep_seconds = random.randint(300, 600)
        print(f"🕵️ Anti-Ban Sleep: {sleep_seconds//60} minutes")
        time.sleep(sleep_seconds)

# ================== MEMORY SYSTEM ==================
def get_past_topics():
    if not os.path.exists(TOPICS_FILE):
        return ""
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = f.read().splitlines()
    return "\n".join(topics[-100:])

def save_new_topic(case_name):
    try:
        with open(TOPICS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{case_name}\n")
        print(f"💾 Saved '{case_name}' to memory bank.")
    except Exception as e:
        print(f"⚠️ Failed to save topic to memory: {e}")

# ================== GLOBAL SOTA INTELLIGENCE (CASCADE) ==================
def get_top_free_openrouter_models(limit=3):
    print("🔍 Scouting OpenRouter for the best creative & structured SOTA models...")
    default_models = ["meta-llama/llama-3.3-70b-instruct:free", "qwen/qwen-3.6-plus:free", "mistralai/mistral-large:free"]

    SOTA_REWARD_MATRIX = {
        "meta-llama/llama-3.3-70b-instruct:free": 99,
        "qwen/qwen-3.6-plus:free": 98,
        "mistralai/mistral-large:free": 97,
        "deepseek/deepseek-r1:free": 95,
        "nvidia/nemotron-3-super:free": 94,
        "google/gemma-4-31b-instruct:free": 90
    }

    if not OPENROUTER_KEY:
        print(f"⚠️ OPENROUTER_API_KEY missing. Defaulting to {default_models}.")
        return default_models

    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=15)
        if response.status_code != 200:
            return default_models

        models_data = response.json().get('data', [])
        free_models = [m['id'] for m in models_data if (m.get('pricing', {}).get('prompt') == '0' and m.get('pricing', {}).get('completion') == '0') or ':free' in m['id']]

        if not free_models: return default_models

        def get_model_reward(m_id):
            m_lower = m_id.lower()
            for known_model, score in SOTA_REWARD_MATRIX.items():
                if known_model in m_lower: return score
            score = 50
            if "instruct" in m_lower: score += 20
            if "chat" in m_lower: score += 10
            if "llama-3" in m_lower: score += 15
            elif "qwen" in m_lower: score += 15
            elif "mistral" in m_lower: score += 10
            if "preview" in m_lower or "experimental" in m_lower or "liquid" in m_lower or "test" in m_lower: score -= 40
            return score

        best_models = sorted(free_models, key=get_model_reward, reverse=True)[:limit]
        print(f"🌟 Task-Optimized SOTA Cascade Locked: {best_models}")
        return best_models

    except Exception as e:
        return default_models

# ================== LLM HELPER ==================
def ask_llm(system_instruction, prompt, sota_models):
    strict_prompt = prompt + "\n\nCRITICAL RULE: Return ONLY the exact requested text. No intro, no conversation, no explanation."

    if OPENROUTER_KEY:
        for sota_model in sota_models:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
            payload = {"model": sota_model, "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": strict_prompt}]}

            try:
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
                if r.status_code == 200:
                    return r.json()['choices'][0]['message']['content'].strip()
                else:
                    time.sleep(4)
            except Exception as e:
                time.sleep(4)

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=strict_prompt, config=config)
        return response.text.strip()
    except Exception as e:
        return ""

# ================== PHASE 1: THE WRITER ==================
def generate_viral_script(fallback_sota_models):
    print("🧠 Phase 1: Generating Master Script (Writer)...")
    client = genai.Client(api_key=GEMINI_KEY)

    content_pool = [
        "True Crime: real murder cases, unsolved killings, serial killers",
        "Did You Know: mind-blowing scientific facts, impossible historical events, shocking statistics",
        "Scam: real frauds, financial crimes, con artists who stole millions",
        "Hacking: real cyberattacks, data breaches, hackers who broke into governments"
    ]

    niche = random.choice(content_pool)
    print(f"🎲 Selected Category: {niche}")

    past_topics = get_past_topics()
    avoid_instruction = f"CRITICAL: Do NOT write about these topics already covered:\n{past_topics}\n" if past_topics else ""

    json_template = '''
{
    "case_name": "The Somerton Man",
    "recommended_voice_model": "Charon",
    "lines": [
        {
            "style_instruction": "Hushed, terrified whisper.",
            "acting_text": "He walked into the room... <break time='1.5s'/> and <emphasis>vanished</emphasis>.",
            "clean_text": "He walked into the room and vanished."
        }
    ]
}
'''

    prompt = f"""
You are an elite viral YouTube Shorts writer and Award-Winning Voice Director.

Channel: "The Glitch Archive" — dark, gripping, real stories about crimes, conspiracies, scams, hacks, and mind-blowing facts.

CATEGORY: {niche}

MISSION:

Write a highly engaging script in ENGLISH about a REAL, documented, obscure case or fact.

DO NOT invent anything. Use only documented historical events, verified facts, or widely reported cases.

{avoid_instruction}

STRICT STORYTELLING RULES (FOR 100%+ RETENTION):

1. THE HOOK (0-3s): The first sentence MUST drop a bizarre paradox, an impossible fact, or a shocking statistic. Make it so wild the viewer HAS to keep watching.

2. THE OPEN LOOP: Second sentence introduces a mystery or question — but delays the answer until the very end.

3. THE PACING: Script must be exactly 130 to 160 words (roughly 45-55 seconds of audio). Maximum 10 lines.

4. THE PERFECT LOOP: The final sentence must end on a cliffhanger that flows perfectly back into the first sentence.

SSML EXPRESSION TAGS FOR VOICE ACTING:

- <break time="1s"/> or <break time="1.5s"/> for terrifying, suspenseful pauses before big reveals.
- <emphasis level="strong"> for shocking or violent words.
- <prosody rate="slow" pitch="-15%"> [creepy text here] </prosody> for dark, creeping details.

Return ONLY valid JSON exactly matching this format:

{json_template}

"""

    config = types.GenerateContentConfig(temperature=0.9, top_p=0.95, response_mime_type="application/json")

    try:
        response = client.models.generate_content(model="models/gemini-2.5-pro", contents=prompt, config=config)
        data = json.loads(response.text)
        print("✅ Script written successfully with Gemini Pro.")
        return data

    except Exception as e:
        print(f"⚠️ Gemini Pro Quota/Error: {e}")

        if OPENROUTER_KEY:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
            for fallback_model in fallback_sota_models:
                print(f"🔄 Activating Global SOTA Brain ({fallback_model}) for Script Generation...")
                payload = {"model": fallback_model, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}

                try:
                    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
                    if r.status_code == 200:
                        content = r.json()['choices'][0]['message']['content'].replace("```json", "").replace("```", "").strip()
                        print(f"✅ Script written successfully with SOTA Fallback ({fallback_model}).")
                        return json.loads(content)
                    else:
                        time.sleep(4)
                except Exception as sota_e:
                    time.sleep(4)

        print("🚨 Engaging Ultimate Fallback (Gemini Flash)...")

        try:
            flash_config = types.GenerateContentConfig(temperature=0.9, top_p=0.95, response_mime_type="application/json")
            response = client.models.generate_content(model="models/gemini-2.5-flash", contents=prompt, config=flash_config)
            data = json.loads(response.text)
            print("✅ Script written successfully with Gemini Flash.")
            return data

        except Exception as flash_e:
            print(f"❌ Ultimate Fallback also failed: {flash_e}")
            return None

# ================== PHASE 3: THE CINEMATOGRAPHER ==================
def generate_cinematographer_prompts(full_script_text, required_images, sota_models):
    json_template = '''
{
    "visuals": [
        {
            "search_query": "detective crime scene evidence",
            "ai_prompt": "A glowing CRT television in a pitch black 1970s living room, harsh static glow, eerie volumetric fog, cinematic 35mm photography, deep shadows, highly detailed, vertical composition"
        }
    ]
}
'''

    prompt = f"""
You are a Master Cinematographer and Visual Researcher for a viral YouTube Shorts channel covering true crime, scams, hacking, and mind-blowing facts.

Map sequential visual prompts to the voiceover script below.

SCRIPT:

"{full_script_text}"

We need EXACTLY {required_images} visual transitions.

RULE 1: 'search_query' (For Pexels stock image search)

- MUST be strictly 2 to 4 keywords in English.
- Use concrete nouns: objects, places, actions, people types.
- NEVER use adjectives like "creepy", "mysterious", "scary", "dark".
- Good: "hacker computer screen" or "courtroom judge gavel" or "vault robbery"
- Bad: "A mysterious shadowy figure doing something scary"

RULE 2: 'ai_prompt' (For FLUX.1 AI image generation fallback)

- Formula: [Subject/Action] + [Setting] + [Lighting] + cinematic 35mm photography, 8k resolution, vertical composition
- NEVER request text, numbers, letters, signs, or documents with writing.

Provide EXACTLY {required_images} items. Return ONLY valid JSON matching this format:

{json_template}

"""

    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}

    for sota_model in sota_models:
        print(f"🎬 Phase 3: Directing {required_images} perfectly-paced visuals using SOTA Brain ({sota_model})...")
        payload = {"model": sota_model, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].replace("```json", "").replace("```", "").strip()
                data = json.loads(content)
                visuals = data.get("visuals", [])

                while len(visuals) < required_images:
                    visuals.append({"search_query": "dark mystery crime", "ai_prompt": "Dark cinematic mystery background, true crime documentary style, volumetric lighting, 35mm photography, 8k resolution, highly detailed, vertical composition"})

                return visuals[:required_images]
            else:
                time.sleep(4)
        except Exception as e:
            time.sleep(4)

    print("🚨 Engaging Ultimate Fallback (Gemini Flash) for Visuals...")

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        flash_config = types.GenerateContentConfig(temperature=0.7, response_mime_type="application/json")
        response = client.models.generate_content(model="models/gemini-2.5-flash", contents=prompt, config=flash_config)
        content = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        visuals = data.get("visuals", [])

        while len(visuals) < required_images:
            visuals.append({"search_query": "dark mystery crime", "ai_prompt": "Dark cinematic mystery background, true crime documentary style, volumetric lighting, 35mm photography, 8k resolution, highly detailed, vertical composition"})

        print("✅ Cinematographer visuals generated with Gemini Flash.")
        return visuals[:required_images]

    except Exception as flash_e:
        print(f"❌ Ultimate Fallback failed: {flash_e}")
        return [{"search_query": "dark mystery crime", "ai_prompt": "dark cinematic eerie background, volumetric fog, 35mm photography, 8k resolution, vertical composition"} for _ in range(required_images)]

# ================== 4-LAYER TITANIUM PIPELINE ==================
def fetch_pexels_image(query, filename):
    print(f"📷 [1/4] Pexels (Stock): {query[:40]}...")

    if not PEXELS_KEY: return False

    url = "https://api.pexels.com/v1/search"
    params = {"query": query, "per_page": 5, "orientation": "portrait", "page": random.randint(1, 4)}

    try:
        response = requests.get(url, headers={"Authorization": PEXELS_KEY}, params=params, timeout=30)
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            if photos:
                photo = random.choice(photos)
                img_data = requests.get(photo["src"]["large2x"], timeout=20).content
                with open(filename, "wb") as f: f.write(img_data)
                if os.path.getsize(filename) > 1000:
                    print("✅ Pexels stock image successfully downloaded.")
                    return True
    except Exception:
        pass

    return False

def fetch_cloudflare_image(prompt, filename):
    print(f"☁️ [2/4] Cloudflare (FLUX.1): {prompt[:40]}...")

    if not CF_ACCOUNT_ID or not CF_API_TOKEN: return False

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"prompt": prompt}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = response.json()
                image_b64 = data.get("result", {}).get("image")
                if image_b64:
                    with open(filename, "wb") as f: f.write(base64.b64decode(image_b64))
                    print("✅ Cloudflare JSON decoded and image saved!")
                    return True
            else:
                with open(filename, "wb") as f: f.write(response.content)
                if os.path.getsize(filename) > 1000:
                    print("✅ Cloudflare binary image generated successfully!")
                    return True
    except Exception as e:
        print(f"⚠️ Cloudflare connection error: {e}")

    return False

def fetch_archive_image(prompt, filename):
    """Layer 3: Dual-Archive Search (Wikipedia API + Internet Archive)"""
    print(f"🏛️ [3/4] Public Archives Search: {prompt[:40]}...")

    # 3A. Wikipedia API Attempt
    clean_query = " ".join(prompt.replace("photo", "").replace("archive", "").split()[:3])
    wiki_url = "https://en.wikipedia.org/w/api.php"
    wiki_params = {
        "action": "query", "format": "json", "prop": "pageimages",
        "generator": "search", "gsrsearch": clean_query, "gsrlimit": 3, "pithumbsize": 1000
    }
    headers = {'User-Agent': 'GhostBot/1.0 (Educational History Bot)'}

    try:
        response = requests.get(wiki_url, params=wiki_params, headers=headers, timeout=10)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for page_id, page_info in pages.items():
            if "thumbnail" in page_info:
                img_url = page_info["thumbnail"]["source"]
                img_data = requests.get(img_url, headers=headers, timeout=15).content
                with open(filename, "wb") as f:
                    f.write(img_data)
                if os.path.getsize(filename) > 1000:
                    print("✅ Wikipedia real historical evidence successfully downloaded!")
                    return True
    except Exception:
        pass

    # 3B. Internet Archive Attempt
    ia_url = "https://archive.org/advancedsearch.php"
    ia_params = {
        "q": f'"{clean_query}" AND mediatype:image',
        "fl": "identifier,format", "rows": 3, "output": "json"
    }

    try:
        response = requests.get(ia_url, params=ia_params, headers=headers, timeout=10)
        data = response.json()
        docs = data.get("response", {}).get("docs", [])

        for doc in docs:
            identifier = doc.get("identifier")
            if identifier:
                img_url = f"https://archive.org/download/{identifier}/{identifier}.jpg"
                img_data = requests.get(img_url, headers=headers, timeout=15).content
                if len(img_data) > 1000:
                    with open(filename, "wb") as f:
                        f.write(img_data)
                    print("✅ Internet Archive historical image successfully downloaded!")
                    return True
    except Exception as e:
        print(f"⚠️ Archive search failed: {e}")

    return False

def fetch_placeholder_image(keyword, filename):
    print(f"🚨 [4/4] EMERGENCY: Generating fallback placeholder image...")

    try:
        from PIL import Image
        img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(20, 20, 30))
        img.save(filename, "JPEG")
        return True
    except Exception:
        return False

def verify_and_convert_image(filename):
    try:
        with PIL.Image.open(filename) as img:
            img.load()
            if img.mode in ('RGBA', 'P', 'LA', 'L'): img = img.convert('RGB')
            img.save(filename, format='JPEG', quality=95)
        return True
    except Exception as e:
        return False

def get_image_clip(search_query, ai_prompt, duration, index):
    img_filename = f"temp_img_{index}.jpg"
    success = False

    success = fetch_pexels_image(search_query, img_filename)
    if not success: success = fetch_cloudflare_image(ai_prompt, img_filename)
    if not success: success = fetch_archive_image(search_query, img_filename)
    if not success: success = fetch_placeholder_image(search_query, img_filename)

    if not verify_and_convert_image(img_filename):
        fetch_placeholder_image(search_query, img_filename)

    try:
        clip = ImageClip(img_filename).set_duration(duration).resize(height=VIDEO_HEIGHT)
        if clip.w < VIDEO_WIDTH: clip = clip.resize(width=VIDEO_WIDTH)
        clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)

        zoom = (lambda t: 1 + 0.05 * (t / duration)) if index % 2 == 0 else (lambda t: 1.05 - 0.05 * (t / duration))
        clip = clip.resize(zoom).crop(x_center=VIDEO_WIDTH/2, y_center=VIDEO_HEIGHT/2, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)

        return clip

    except Exception:
        return ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(20, 20, 35), duration=duration)

# ================== META, SUBTITLES & YOUTUBE ==================
def add_sfx(audio_clip, text):
    text_lower = text.lower()
    for k, v in SFX_MAP.items():
        if k in text_lower:
            path = os.path.join("sfx", v)
            if os.path.exists(path):
                try:
                    sfx = AudioFileClip(path).volumex(0.20)
                    if sfx.duration > audio_clip.duration: sfx = sfx.subclip(0, audio_clip.duration)
                    return CompositeAudioClip([audio_clip, sfx])
                except Exception:
                    pass
    return audio_clip

def add_dynamic_subtitles(video_clip, audio_path):
    print("📝 Transcribing audio for word-level subtitles...")

    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, word_timestamps=True)
        subtitle_clips = []

        video_duration = video_clip.duration
        for segment in segments:
            for word in segment.words:
                clean = word.word.strip().upper()
                if not clean: continue
                if word.start >= video_duration: continue
                word_end = min(word.end, video_duration)
                if word_end - word.start < 0.05: continue
                try:
                    txt = TextClip(clean, fontsize=70, color='yellow', stroke_color='black', stroke_width=2, font='Impact', method='caption', size=(video_clip.w * 0.9, None))
                    txt = txt.set_start(word.start).set_end(word_end).set_position(('center', video_clip.h * 0.70))
                    subtitle_clips.append(txt)
                except Exception:
                    pass

        return CompositeVideoClip([video_clip] + subtitle_clips)

    except Exception:
        return video_clip

def upload_to_youtube(file_path, yt_metadata):
    if not file_path: return False

    print("🚀 Uploading to YouTube...")

    try:
        creds = Credentials.from_authorized_user_info(json.loads(YOUTUBE_TOKEN_VAL))
        youtube = build("youtube", "v3", credentials=creds)

        full_description = f"{yt_metadata['description']}\n\nWhat would be your first move? 👇"

        youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {"title": yt_metadata["title"], "description": full_description, "tags": yt_metadata["tags"], "categoryId": "24"},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
        ).execute()

        print("✅ YouTube Upload Successful!")
        return True

    except Exception:
        return False

# ================== PHASE 5: THE MARKETER ==================
def generate_youtube_metadata(full_script_text, sota_models):
    print("📈 Phase 5: Marketer - Generating YouTube SEO Chain...")

    sys_prompt = "You are an elite English-language YouTube Shorts SEO Strategist. You ONLY output the exact data requested."

    t_prompt = f"Read this script and write ONE click-bait YouTube Shorts title in ENGLISH (under 60 characters). No quotes, no hashtags.\nScript: {full_script_text}"
    title = ask_llm(sys_prompt, t_prompt, sota_models).strip('"').replace("'", "")

    if not title or len(title) > 80: title = "They found WHAT?"

    d_prompt = f"Write a compelling 3-sentence description in ENGLISH for a YouTube Short titled: '{title}'. No hashtags."
    description = ask_llm(sys_prompt, d_prompt, sota_models)

    if not description: description = "An unsolved mystery that will leave you speechless."

    tag_prompt = f"Title: '{title}'. Description: '{description}'. Provide exactly 8 highly-searched English SEO tags as a comma-separated list. No hashtags."
    tags_str = ask_llm(sys_prompt, tag_prompt, sota_models)

    tags = [t.strip().replace("#", "") for t in tags_str.split(',')] if tags_str else ["mystery", "shorts", "truecrime", "hacking", "scam", "didyouknow", "facts", "crime"]

    return {"title": f"{title} #shorts #mystery", "description": description, "tags": tags}

def generate_platform_captions(yt_metadata, platform, sota_models):
    sys_prompt = f"You are an elite English-language {platform} Social Media Manager. You ONLY output the final caption text."

    if platform == "Instagram":
        prompt = f"Convert to viral Instagram Reels caption in ENGLISH.\nTitle: {yt_metadata['title']}\nDescription: {yt_metadata['description']}\nREQUIREMENTS: Strong hook, call-to-action, 6 hashtags, emojis."
    else:
        prompt = f"Convert to engaging Facebook Reels caption in ENGLISH.\nTitle: {yt_metadata['title']}\nDescription: {yt_metadata['description']}\nREQUIREMENTS: Conversational, ask a question, 3 hashtags."

    caption = ask_llm(sys_prompt, prompt, sota_models)

    if not caption: caption = f"{yt_metadata['title']}\n\nWhat do you think happened? 👇\n\n#Mystery"

    return caption

# ================== MASTER ORCHESTRATION ==================
def main_pipeline():
    anti_ban_sleep()

    try: voice_engine = VoiceEngine()
    except Exception: return None, None, None, None

    global_sota_models = get_top_free_openrouter_models()
    script = generate_viral_script(global_sota_models)

    if not script: return None, None, None, None

    # THE KILL SWITCH: Prevent 7-Minute Hallucinations — max 10 lines (~90 seconds)
    if len(script.get("lines", [])) > 10:
        print("⚠️ Script exceeded 10 lines! Truncating to prevent excessively long videos...")
        script["lines"] = script["lines"][:10]

    print(f"🎬 Case: {script.get('case_name', 'Unknown')}")

    audio_clips = []
    full_script_text = ""
    target_voice = script.get("recommended_voice_model", "Charon")

    for i, line in enumerate(script["lines"]):
        clean_text = line.get("clean_text", "")
        full_script_text += clean_text + " "

        try:
            wav_file = voice_engine.generate_acting_line(acting_text=line.get("acting_text", ""), clean_text=clean_text, style_instruction=line.get("style_instruction", ""), index=i, voice_name=target_voice)
            if wav_file:
                audio_clip = AudioFileClip(wav_file)
                if audio_clip.duration > 30:
                    print(f"⚠️ Skipping suspiciously long audio clip: {audio_clip.duration:.1f}s")
                    continue
                audio_clip = add_sfx(audio_clip, clean_text)
                audio_clips.append(audio_clip)
        except Exception: pass

    if not audio_clips: return None, None, None, None

    master_voice_clip = concatenate_audioclips(audio_clips)
    total_duration = master_voice_clip.duration

    # Hard cap: never exceed 3 minutes
    if total_duration > 180:
        print(f"⚠️ Total audio too long ({total_duration:.0f}s)! Capping at 3 minutes...")
        master_voice_clip = master_voice_clip.subclip(0, 180)
        total_duration = 180

    required_images = int(total_duration / IMAGE_TRANSITION_TIME)
    if required_images < 1: required_images = 1

    print(f"⏱️ Master Audio Duration: {total_duration:.2f}s | Images Needed: {required_images}")

    visual_directions = generate_cinematographer_prompts(full_script_text, required_images, global_sota_models)

    duration_per_image = total_duration / len(visual_directions)

    visual_clips = []
    for i, vis in enumerate(visual_directions):
        img_clip = get_image_clip(vis.get("search_query", ""), vis.get("ai_prompt", ""), duration_per_image, i)
        visual_clips.append(img_clip)

    print("✂️ Rendering Final Video with Transitions & Subtitles...")

    try:
        final_video = concatenate_videoclips(visual_clips, method="compose").set_duration(total_duration)
        final_video = final_video.set_audio(master_voice_clip).fx(colorx, 0.85)
    except Exception: return None, None, None, None

    temp_voice_track = "temp_master_voice.wav"
    master_voice_clip.write_audiofile(temp_voice_track, fps=24000, logger=None)

    final_video = add_dynamic_subtitles(final_video, temp_voice_track)

    try:
        watermark = TextClip(CHANNEL_HANDLE, fontsize=30, color='white', font='Impact', stroke_color='black', stroke_width=2).set_opacity(0.4).set_position(('center', 150)).set_duration(final_video.duration)
        final_video = CompositeVideoClip([final_video, watermark])
    except Exception: pass

    output_file = "final_video.mp4"

    try: final_video.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=24, preset="fast", threads=2, logger=None)
    except Exception: return None, None, None, None

    try:
        for f in glob.glob("temp_*.wav") + glob.glob("temp_*.jpg"): os.remove(f)
    except Exception: pass

    return output_file, script, full_script_text, global_sota_models

if __name__ == "__main__":
    video_path, script_data, full_script_text, global_sota_models = main_pipeline()

    if video_path and script_data and global_sota_models:
        yt_metadata = generate_youtube_metadata(full_script_text, global_sota_models)

        if upload_to_youtube(video_path, yt_metadata):
            save_new_topic(script_data.get('case_name', 'Unknown Case'))

            fb_caption = generate_platform_captions(yt_metadata, "Facebook", global_sota_models)
            meta_upload.upload_to_facebook(video_path, fb_caption)

            ig_caption = generate_platform_captions(yt_metadata, "Instagram", global_sota_models)
            temp_url = meta_upload.get_temp_public_url(video_path)

            if temp_url: meta_upload.upload_to_instagram(temp_url, ig_caption)

    print("🎉 Daily GhostBot execution finished!")
