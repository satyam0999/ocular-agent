# 🤖 Ocular Agent

An intelligent web automation agent that uses **vision AI** and **adaptive planning** to navigate and interact with websites autonomously.

## ✨ Features

- 🎯 **Adaptive Planning**: Creates plans and adjusts based on real-time feedback
- 👁️ **Vision-Based Navigation**: Uses Qwen2.5-VL to understand web pages visually
- 🔄 **Self-Correcting**: Verifies actions and replans if something goes wrong
- 🎨 **Set-of-Mark (SoM)**: Visual element identification with bounding boxes
- 🚀 **Natural Language Commands**: Just describe what you want in plain English

## 🎬 Demo

```bash
👉 Goal: open blinkit and add 5 small maggi packets to cart
```

The agent will:
1. Navigate to Blinkit
2. Find and click the search box
3. Type "maggi"
4. Click on the product
5. Increase quantity to 5
6. Verify each step and replan if needed

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- CUDA-capable GPU (GTX 1650 or better)
- 6GB+ VRAM

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ocular-agent.git
cd ocular-agent
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure API keys:
```bash
# Copy .env.example to .env and add your keys
cp .env.example .env
```

Edit `.env` and add your DeepSeek API key:
```
DEEPSEEK_API_KEY=sk-your-key-here
```

## 🚀 Usage

Run the agent:
```bash
python main.py
```

### Execution Modes

**Mode 3 - Adaptive (Recommended):**
- Creates initial plan
- Verifies each step
- Replans if actions fail

**Mode 2 - Reactive:**
- No initial plan
- Decides next action based on current screen

**Mode 1 - Pre-planned:**
- Creates full plan upfront
- Executes without verification

### Example Commands

```
search for football shoes on amazon
go to flipkart and find gaming mouse
open blinkit and add 5 maggi packets to cart
```

## 🏗️ Architecture

```
ocular-agent/
├── src/
│   ├── agent.py       # Task planning and adaptive logic
│   ├── browser.py     # Playwright browser control
│   ├── vision.py      # Qwen2.5-VL vision model
│   └── __init__.py
├── assets/            # Debug screenshots
├── main.py           # Main entry point
├── requirements.txt
└── .env
```

## 🧠 How It Works

1. **Planning**: DeepSeek creates a step-by-step plan
2. **Vision**: Qwen2.5-VL identifies elements on screen
3. **Execution**: Playwright performs browser actions
4. **Verification**: After each step, checks if it succeeded
5. **Adaptation**: If failed, creates new plan and retries

## 🔧 Configuration

### Vision Model
Default: `Qwen/Qwen2.5-VL-3B-Instruct` (6GB VRAM)

For better accuracy (needs more VRAM):
- Edit `src/vision.py` to use `Qwen2.5-VL-7B-Instruct`

### Planning Model
Default: DeepSeek API

Alternatives in `.env`:
```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Local LLM (Ollama)
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3
```

## 📝 Requirements

- torch>=2.4.0
- transformers>=4.46.0
- playwright>=1.48.0
- openai>=1.0.0
- python-dotenv

See `requirements.txt` for full list.

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2-VL) for vision capabilities
- [Playwright](https://playwright.dev/) for browser automation
- [DeepSeek](https://www.deepseek.com/) for planning intelligence

## ⚠️ Disclaimer

This tool is for educational and research purposes. Always respect website terms of service and rate limits.
