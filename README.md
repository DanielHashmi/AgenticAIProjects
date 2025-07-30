# AI Assistant with Global Hotkeys

A cross-platform AI assistant application that responds to global hotkeys (Ctrl+F9) to process selected text or clipboard content using AI.

## Features

- **Global Hotkey Support**: Ctrl+F9 to process selected text
- **Cross-platform**: Works on Windows, macOS, and Linux
- **AI Integration**: Supports Gemini and OpenAI APIs
- **System Tray**: Runs in background with system tray icon
- **Text-to-Speech**: Optional audio responses
- **Modern UI**: Clean PyQt5 interface

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Run the Application

```bash
python ai_assistant.py
```

### 4. Test Hotkey

First, test if hotkeys work on your system:

```bash
python test_hotkeys.py
```

## Usage

1. **Start the application** - Run `python ai_assistant.py`
2. **Select any text** in any application
3. **Press Ctrl+F9** to process the text with AI
4. **View the response** in a popup window

### Additional Hotkeys

- **Ctrl+Shift+A**: Quick assistance with clipboard content

## Troubleshooting

### Ctrl+F9 Not Working

1. **Check permissions**: On some systems, you need to grant accessibility permissions
2. **Test hotkeys**: Run `python test_hotkeys.py` to verify hotkey detection
3. **Check logs**: Look at `ai_assistant.log` for error messages

### Linux Permissions

On Linux, you might need to run with elevated permissions:

```bash
sudo python ai_assistant.py
```

Or add your user to the input group:

```bash
sudo usermod -a -G input $USER
```

### macOS Permissions

On macOS, you need to grant accessibility permissions:

1. Go to System Preferences → Security & Privacy → Privacy
2. Select "Accessibility" from the left panel
3. Add Python or your terminal application
4. Restart the application

### Windows Issues

On Windows, make sure the application is not blocked by antivirus software.

## API Configuration

### Gemini API (Default)

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your `.env` file:
   ```
   GEMINI_API_KEY=your_key_here
   ```

### OpenAI API (Alternative)

1. Get your API key from [OpenAI](https://platform.openai.com/api-keys)
2. Modify the configuration in `ai_assistant.py`:
   ```python
   API_KEY: str = os.getenv("OPENAI_API_KEY", "")
   MODEL_NAME: str = "gpt-3.5-turbo"
   BASE_URL: str = "https://api.openai.com/v1/"
   ```

## Key Bug Fixes

The following issues have been resolved:

1. **Missing imports**: Added all required imports and proper error handling
2. **Hotkey registration**: Fixed GlobalHotKeys implementation with proper error handling
3. **Threading issues**: Implemented proper async/await patterns for AI calls
4. **UI responsiveness**: Separated AI processing into background threads
5. **Clipboard handling**: Robust clipboard operations with fallbacks
6. **Cross-platform compatibility**: Added platform-specific imports and fallbacks
7. **Error handling**: Comprehensive exception handling throughout
8. **Resource cleanup**: Proper cleanup of hotkey listeners and threads

## Architecture

- **HotkeyManager**: Handles global hotkey detection and registration
- **AIAssistant**: Manages AI API calls and response processing
- **PopupWindow**: Displays AI responses in attractive popups
- **ClipboardManager**: Cross-platform clipboard operations
- **TTSManager**: Optional text-to-speech functionality

## Dependencies

- PyQt5: GUI framework
- pynput: Global hotkey detection
- pyperclip: Clipboard operations
- python-dotenv: Environment configuration
- pyttsx3: Text-to-speech (optional)
- openai: AI API client (optional)

## License

MIT License - feel free to modify and distribute.