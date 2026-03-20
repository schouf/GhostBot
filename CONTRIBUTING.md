# Contributing to GhostBot 👻🤖

First off, thank you for considering contributing to GhostBot! This project is designed to be a fully autonomous video generation pipeline, and community contributions are highly encouraged to make it smarter, faster, and more visually engaging.

## 💡 What We Are Looking For
We welcome pull requests (PRs) for absolutely anything that makes the bot better, but we are especially interested in:
* **Visual & Rendering Enhancements:** Do you have a better way to handle B-roll fetching, dynamic text overlays, or video transitions? We'd love to see your ideas for making the final videos look even more professional!
* **General Pipeline Upgrades:** If you see a way to make the bot smarter, cleaner, or more efficient—whether that is a major code refactor or a brand new feature—we welcome it all.
* **New AI Integrations:** Adding support for different LLMs (Claude, OpenAI) beyond Gemini/OpenRouter.
* **Voice Engine Tweaks:** Improvements to SSML parsing or adding new TTS providers in `neural_voice.py`.
* **Platform Expansions:** Code to support automated uploading to TikTok, X (Twitter), or YouTube Shorts.
* **Bug Fixes:** Specifically around API rate limits or timeout handling for the Meta/YouTube APIs.

## 🛠️ How to Contribute

### 1. Fork & Clone
Fork the repository to your own GitHub account, then clone it locally:
```bash
git clone [https://github.com/YOUR-USERNAME/GhostBot.git](https://github.com/YOUR-USERNAME/GhostBot.git)
cd GhostBot
```

### 2. Set Up Your Environment
Create a virtual environment and install the dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Create a Branch
Always create a new branch for your feature or bug fix:
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes
Write your code, ensuring it aligns with the existing architecture. If you are modifying the pipeline (`main.py`), please ensure you aren't breaking the GitHub Actions compatibility.

### 5. Submit a Pull Request
* Push your branch to your fork.
* Open a Pull Request against the `main` branch of this repository.
* Include a clear description of what your PR does and any testing you performed. (If you changed the visuals, attach a short video or screenshot of the new output!)

## 🐛 Found a Bug or Have a Big Idea?
If you find a bug or have a massive idea for a new feature but don't have the time to code it yourself, please open an Issue! Go to the "Issues" tab, click "New Issue," and provide as much detail as possible.

Happy coding!
