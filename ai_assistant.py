import sys
import os
import time
import asyncio
import threading
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import datetime
import tempfile
import json

import dotenv
import pyperclip

# Text-to-speech support
try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

# Windows clipboard support
try:
    import win32clipboard
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# PyQt imports - using direct imports to avoid linter errors
try:
    import PyQt5.QtWidgets as QtWidgets
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui
    HAS_PYQT = True
except ImportError:
    print("PyQt5 not found. Installing...")
    os.system("pip install PyQt5")
    import PyQt5.QtWidgets as QtWidgets
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui
    HAS_PYQT = True

# Define aliases for commonly used classes to maintain code readability
QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QLabel = QtWidgets.QLabel
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QPushButton = QtWidgets.QPushButton
QTextEdit = QtWidgets.QTextEdit
QMainWindow = QtWidgets.QMainWindow
QTabWidget = QtWidgets.QTabWidget
QFrame = QtWidgets.QFrame
QScrollArea = QtWidgets.QScrollArea
QSplitter = QtWidgets.QSplitter
QSystemTrayIcon = QtWidgets.QSystemTrayIcon
QMenu = QtWidgets.QMenu
QAction = QtWidgets.QAction
QMessageBox = QtWidgets.QMessageBox
QLineEdit = QtWidgets.QLineEdit

Qt = QtCore.Qt
pyqtSignal = QtCore.pyqtSignal
QObject = QtCore.QObject
QTimer = QtCore.QTimer
QSize = QtCore.QSize
QRectF = QtCore.QRectF

QFont = QtGui.QFont
QIcon = QtGui.QIcon
QColor = QtGui.QColor
QPalette = QtGui.QPalette
QPixmap = QtGui.QPixmap
QPainter = QtGui.QPainter
QPainterPath = QtGui.QPainterPath
QPen = QtGui.QPen

try:
    from pynput.keyboard import Key, GlobalHotKeys, Controller as KeyboardController
    from pynput import mouse
    HAS_PYNPUT = True
except ImportError:
    print("pynput not found. Installing...")
    os.system("pip install pynput")
    from pynput.keyboard import Key, GlobalHotKeys, Controller as KeyboardController
    from pynput import mouse
    HAS_PYNPUT = True

# AI agent imports
try:
    from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled
    from openai import AsyncOpenAI
    HAS_AI_AGENTS = True
except ImportError:
    HAS_AI_AGENTS = False
    print("AI agents not available. Please install openai and agents packages.")

# Configuration
# Look for .env file in the executable's directory when packaged
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = os.path.dirname(sys.executable)
    dotenv_path = os.path.join(bundle_dir, '.env')
    dotenv.load_dotenv(dotenv_path)
else:
    # Running in a normal Python environment
    dotenv.load_dotenv()

@dataclass
class Config:
    """Application configuration"""
    API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_NAME: str = "gemini-1.5-flash"
    BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    # API_KEY: str = '12345'
    # MODEL_NAME: str = "cognito-v1-3b"
    # BASE_URL: str = "http://127.0.0.1:1337/v1"
    MAX_DEFINITION_LENGTH: int = 150
    POPUP_WIDTH: int = 400
    COPY_ATTEMPTS: int = 3
    COPY_DELAY: float = 0.1
    FONT_SIZE: int = 11
    FONT_FAMILY: str = "Segoe UI"
    
    # UI Configuration
    WINDOW_WIDTH: int = 800
    WINDOW_HEIGHT: int = 600
    WINDOW_TITLE: str = "AI Assistant"

class LogLevel(Enum):
    """Log levels for the application"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ClipboardManager:
    """Manages clipboard operations with cross-platform support"""
    
    @staticmethod
    def get_clipboard_text() -> str:
        """Get text from clipboard"""
        try:
            return pyperclip.paste()
        except Exception as e:
            logger.error(f"Error getting clipboard text: {e}")
            return ""
    
    @staticmethod
    def set_clipboard_text(text: str) -> bool:
        """Set text to clipboard"""
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            logger.error(f"Error setting clipboard text: {e}")
            return False

class TTSManager:
    """Text-to-speech manager"""
    
    def __init__(self):
        self.engine = None
        if HAS_TTS:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 150)
                self.engine.setProperty('volume', 0.8)
            except Exception as e:
                logger.error(f"TTS initialization error: {e}")
                self.engine = None
    
    def speak(self, text: str):
        """Speak the given text"""
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS error: {e}")

class PopupWindow(QWidget):
    """Popup window for displaying AI responses"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(Config.POPUP_WIDTH, 200)
        
        # Setup UI
        layout = QVBoxLayout()
        
        # Text display
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 30, 30, 230);
                color: white;
                padding: 15px;
                border-radius: 10px;
                font-size: 12px;
                font-family: 'Segoe UI';
            }
        """)
        
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        
        # Auto-close timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.close)
        self.timer.start(5000)  # Close after 5 seconds
        
        # Position at cursor
        self.position_at_cursor()
    
    def position_at_cursor(self):
        """Position the popup near the cursor"""
        try:
            cursor_pos = QtGui.QCursor.pos()
            self.move(cursor_pos.x() + 10, cursor_pos.y() + 10)
        except Exception as e:
            logger.error(f"Error positioning popup: {e}")
            # Fallback to center of screen
            screen = QApplication.primaryScreen().geometry()
            self.move(screen.center() - self.rect().center())

class AIAssistant(QObject):
    """Main AI Assistant class"""
    
    response_ready = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.clipboard_manager = ClipboardManager()
        self.tts_manager = TTSManager()
        self.is_processing = False
        
        # Setup response signal
        self.response_ready.connect(self.show_response)
        
        logger.info("AI Assistant initialized")
    
    async def process_text_async(self, text: str) -> str:
        """Process text using AI (async version)"""
        if not text.strip():
            return "No text provided"
        
        try:
            if HAS_AI_AGENTS and self.config.API_KEY:
                # Use AI agents if available
                client = AsyncOpenAI(
                    api_key=self.config.API_KEY,
                    base_url=self.config.BASE_URL
                )
                
                response = await client.chat.completions.create(
                    model=self.config.MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise responses."},
                        {"role": "user", "content": f"Please explain or help with: {text}"}
                    ],
                    max_tokens=self.config.MAX_DEFINITION_LENGTH
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Fallback response when AI is not available
                return f"AI processing not available. Text received: {text[:50]}..."
                
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return f"Error processing text: {str(e)}"
    
    def process_text(self, text: str):
        """Process text using AI (sync wrapper)"""
        if self.is_processing:
            logger.info("Already processing, skipping...")
            return
        
        self.is_processing = True
        
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.process_text_async(text))
                self.response_ready.emit(result)
            except Exception as e:
                logger.error(f"Async processing error: {e}")
                self.response_ready.emit(f"Error: {str(e)}")
            finally:
                self.is_processing = False
                loop.close()
        
        # Run in separate thread
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def show_response(self, response: str):
        """Show AI response in popup"""
        try:
            popup = PopupWindow(response)
            popup.show()
            
            # Optional TTS
            if HAS_TTS:
                tts_thread = threading.Thread(
                    target=self.tts_manager.speak, 
                    args=(response,), 
                    daemon=True
                )
                tts_thread.start()
                
        except Exception as e:
            logger.error(f"Error showing response: {e}")

class HotkeyManager:
    """Manages global hotkeys"""
    
    def __init__(self, ai_assistant: AIAssistant):
        self.ai_assistant = ai_assistant
        self.hotkeys = None
        self.keyboard_controller = KeyboardController()
        
    def start_hotkey_listener(self):
        """Start listening for global hotkeys"""
        try:
            # Define hotkey mappings
            hotkey_mappings = {
                '<ctrl>+<f9>': self.handle_ctrl_f9,
                '<ctrl>+<shift>+a': self.handle_quick_assist
            }
            
            self.hotkeys = GlobalHotKeys(hotkey_mappings)
            self.hotkeys.start()
            logger.info("Hotkey listener started successfully")
            
        except Exception as e:
            logger.error(f"Error starting hotkey listener: {e}")
    
    def stop_hotkey_listener(self):
        """Stop the hotkey listener"""
        if self.hotkeys:
            try:
                self.hotkeys.stop()
                logger.info("Hotkey listener stopped")
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}")
    
    def handle_ctrl_f9(self):
        """Handle Ctrl+F9 hotkey"""
        logger.info("Ctrl+F9 detected")
        
        try:
            # Small delay to ensure the hotkey doesn't interfere
            time.sleep(0.1)
            
            # Method 1: Get selected text by copying to clipboard
            original_clipboard = self.ai_assistant.clipboard_manager.get_clipboard_text()
            
            # Simulate Ctrl+C to copy selected text
            self.keyboard_controller.press(Key.ctrl)
            self.keyboard_controller.press('c')
            self.keyboard_controller.release('c')
            self.keyboard_controller.release(Key.ctrl)
            
            # Wait a moment for clipboard to update
            time.sleep(0.2)
            
            # Get the copied text
            selected_text = self.ai_assistant.clipboard_manager.get_clipboard_text()
            
            # Restore original clipboard if nothing was selected
            if selected_text == original_clipboard:
                logger.info("No text selected, using clipboard content")
                selected_text = original_clipboard
            
            if selected_text.strip():
                logger.info(f"Processing text: {selected_text[:50]}...")
                self.ai_assistant.process_text(selected_text)
            else:
                logger.warning("No text found to process")
                popup = PopupWindow("No text selected or clipboard empty")
                popup.show()
                
        except Exception as e:
            logger.error(f"Error in Ctrl+F9 handler: {e}")
            popup = PopupWindow(f"Error: {str(e)}")
            popup.show()
    
    def handle_quick_assist(self):
        """Handle Ctrl+Shift+A hotkey for quick assistance"""
        logger.info("Ctrl+Shift+A detected")
        try:
            clipboard_text = self.ai_assistant.clipboard_manager.get_clipboard_text()
            if clipboard_text.strip():
                self.ai_assistant.process_text(f"Quick help: {clipboard_text}")
            else:
                popup = PopupWindow("Clipboard is empty")
                popup.show()
        except Exception as e:
            logger.error(f"Error in quick assist handler: {e}")

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.ai_assistant = AIAssistant()
        self.hotkey_manager = HotkeyManager(self.ai_assistant)
        
        self.init_ui()
        self.setup_system_tray()
        
        # Start hotkey listener
        self.hotkey_manager.start_hotkey_listener()
        
        logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(Config.WINDOW_TITLE)
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("AI Assistant")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                margin: 20px;
                color: #333;
            }
        """)
        
        # Instructions
        instructions = QLabel("""
        <h3>Global Hotkeys:</h3>
        <ul>
            <li><b>Ctrl + F9:</b> Process selected text or clipboard content</li>
            <li><b>Ctrl + Shift + A:</b> Quick assistance with clipboard content</li>
        </ul>
        
        <h3>Usage:</h3>
        <ol>
            <li>Select any text in any application</li>
            <li>Press Ctrl + F9</li>
            <li>View the AI response in a popup</li>
        </ol>
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            QLabel {
                font-size: 12px;
                margin: 20px;
                padding: 20px;
                background-color: #f5f5f5;
                border-radius: 10px;
            }
        """)
        
        # Test area
        test_label = QLabel("Test Area - Select this text and press Ctrl+F9:")
        test_text = QTextEdit()
        test_text.setPlainText("This is a sample text for testing the AI assistant. "
                              "Select this text and press Ctrl+F9 to see the AI response.")
        test_text.setMaximumHeight(100)
        
        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e8f5e8;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(instructions)
        layout.addWidget(test_label)
        layout.addWidget(test_text)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        central_widget.setLayout(layout)
        
        # Apply modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
        """)
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Create a simple icon
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(0, 100, 200))
            icon = QIcon(pixmap)
            
            self.tray_icon.setIcon(icon)
            self.tray_icon.setToolTip("AI Assistant")
            
            # Tray menu
            tray_menu = QMenu()
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            
            tray_menu.addAction(show_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # Double-click to show
            self.tray_icon.activated.connect(self.on_tray_activated)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def closeEvent(self, event):
        """Handle close event"""
        if QSystemTrayIcon.isSystemTrayAvailable() and hasattr(self, 'tray_icon'):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "AI Assistant",
                "Application minimized to tray. Use Ctrl+F9 for AI assistance.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.quit_application()
    
    def quit_application(self):
        """Quit the application"""
        logger.info("Quitting application")
        
        # Stop hotkey listener
        self.hotkey_manager.stop_hotkey_listener()
        
        # Close tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        QApplication.quit()

def main():
    """Main application entry point"""
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed
        
        # Set application properties
        app.setApplicationName("AI Assistant")
        app.setApplicationVersion("1.0")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run the application
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()