#!/usr/bin/env python3
"""
Minimal AI Assistant with Global Hotkeys
Works with standard Python libraries and focuses on Ctrl+F9 functionality
"""

import sys
import os
import time
import asyncio
import threading
import logging
import subprocess
import tempfile
from typing import Optional
from dataclasses import dataclass
import json

# Configuration
@dataclass
class Config:
    """Application configuration"""
    API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_NAME: str = "gemini-1.5-flash"
    BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    MAX_DEFINITION_LENGTH: int = 150
    LOG_LEVEL: str = "INFO"

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ClipboardManager:
    """Cross-platform clipboard manager using system commands"""
    
    @staticmethod
    def get_clipboard_text() -> str:
        """Get text from clipboard using system commands"""
        try:
            if sys.platform == "darwin":  # macOS
                result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                return result.stdout
            elif sys.platform == "win32":  # Windows
                result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], 
                                      capture_output=True, text=True)
                return result.stdout.strip()
            else:  # Linux
                # Try xclip first, then xsel
                try:
                    result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                          capture_output=True, text=True)
                    return result.stdout
                except FileNotFoundError:
                    try:
                        result = subprocess.run(['xsel', '--clipboard', '--output'], 
                                              capture_output=True, text=True)
                        return result.stdout
                    except FileNotFoundError:
                        logger.warning("Neither xclip nor xsel found. Install one for clipboard support.")
                        return ""
        except Exception as e:
            logger.error(f"Error getting clipboard text: {e}")
            return ""
    
    @staticmethod
    def set_clipboard_text(text: str) -> bool:
        """Set text to clipboard using system commands"""
        try:
            if sys.platform == "darwin":  # macOS
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(text.encode())
                return process.returncode == 0
            elif sys.platform == "win32":  # Windows
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
                process.communicate(text.encode())
                return process.returncode == 0
            else:  # Linux
                try:
                    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                             stdin=subprocess.PIPE)
                    process.communicate(text.encode())
                    return process.returncode == 0
                except FileNotFoundError:
                    try:
                        process = subprocess.Popen(['xsel', '--clipboard', '--input'], 
                                                 stdin=subprocess.PIPE)
                        process.communicate(text.encode())
                        return process.returncode == 0
                    except FileNotFoundError:
                        logger.warning("Neither xclip nor xsel found")
                        return False
        except Exception as e:
            logger.error(f"Error setting clipboard text: {e}")
            return False

class NotificationManager:
    """Cross-platform notification manager"""
    
    @staticmethod
    def show_notification(title: str, message: str, duration: int = 5):
        """Show a system notification"""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run([
                    'osascript', '-e', 
                    f'display notification "{message}" with title "{title}"'
                ])
            elif sys.platform == "win32":  # Windows
                subprocess.run([
                    'powershell', '-command',
                    f'Add-Type -AssemblyName System.Windows.Forms; '
                    f'[System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'
                ])
            else:  # Linux
                try:
                    subprocess.run(['notify-send', title, message])
                except FileNotFoundError:
                    # Fallback to console output
                    print(f"\n🔔 {title}: {message}\n")
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
            print(f"\n📢 {title}: {message}\n")

class AIAssistant:
    """AI Assistant class with minimal dependencies"""
    
    def __init__(self):
        self.config = Config()
        self.clipboard_manager = ClipboardManager()
        self.notification_manager = NotificationManager()
        self.is_processing = False
        logger.info("AI Assistant initialized")
    
    async def process_text_async(self, text: str) -> str:
        """Process text using AI (mock implementation)"""
        if not text.strip():
            return "No text provided"
        
        try:
            # Mock AI processing - replace with actual API call
            if self.config.API_KEY:
                # This is where you would make the actual API call
                # For now, return a mock response
                await asyncio.sleep(1)  # Simulate API call
                return f"AI Analysis: The text '{text[:30]}...' contains {len(text)} characters and appears to be discussing relevant topics."
            else:
                return f"AI not configured. Processed text: '{text[:50]}...'"
                
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
                self.show_response(result)
            except Exception as e:
                logger.error(f"Async processing error: {e}")
                self.show_response(f"Error: {str(e)}")
            finally:
                self.is_processing = False
                loop.close()
        
        # Run in separate thread
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def show_response(self, response: str):
        """Show AI response using notifications"""
        try:
            self.notification_manager.show_notification("AI Assistant", response)
            logger.info(f"Response shown: {response[:50]}...")
        except Exception as e:
            logger.error(f"Error showing response: {e}")

class HotkeyManager:
    """Cross-platform hotkey manager"""
    
    def __init__(self, ai_assistant: AIAssistant):
        self.ai_assistant = ai_assistant
        self.is_running = False
        self.hotkey_thread = None
        
    def start_hotkey_listener(self):
        """Start listening for global hotkeys"""
        try:
            # Try to import pynput, install if not available
            try:
                from pynput.keyboard import Key, GlobalHotKeys, Controller as KeyboardController
                self.keyboard_controller = KeyboardController()
                
                # Define hotkey mappings
                hotkey_mappings = {
                    '<ctrl>+<f9>': self.handle_ctrl_f9,
                    '<ctrl>+<shift>+a': self.handle_quick_assist
                }
                
                self.hotkeys = GlobalHotKeys(hotkey_mappings)
                self.hotkeys.start()
                self.is_running = True
                logger.info("Hotkey listener started successfully with pynput")
                
            except ImportError:
                logger.warning("pynput not available, falling back to system-specific hotkey detection")
                self.start_system_hotkey_listener()
                
        except Exception as e:
            logger.error(f"Error starting hotkey listener: {e}")
            print(f"Hotkey listener failed: {e}")
            print("You can still use the application by running the manual commands.")
    
    def start_system_hotkey_listener(self):
        """Fallback hotkey listener using system-specific methods"""
        if sys.platform == "linux":
            self.start_linux_hotkey_listener()
        else:
            logger.warning("System-specific hotkey detection not implemented for this platform")
            print("Manual mode: Use 'process_clipboard' command to test functionality")
    
    def start_linux_hotkey_listener(self):
        """Linux-specific hotkey listener using xinput/xdotool"""
        def monitor_keys():
            try:
                # Create a simple key monitor script
                script_content = '''#!/bin/bash
while true; do
    # Monitor for Ctrl+F9 combination
    if xdotool getactivewindow key --clearmodifiers ctrl+F9 2>/dev/null; then
        echo "CTRL_F9_DETECTED"
    fi
    sleep 0.1
done
'''
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(script_content)
                    script_path = f.name
                
                os.chmod(script_path, 0o755)
                
                # Start monitoring
                process = subprocess.Popen([script_path], stdout=subprocess.PIPE, text=True)
                
                for line in iter(process.stdout.readline, ''):
                    if "CTRL_F9_DETECTED" in line:
                        self.handle_ctrl_f9()
                        
            except Exception as e:
                logger.error(f"Linux hotkey monitoring error: {e}")
            finally:
                if 'script_path' in locals():
                    os.unlink(script_path)
        
        self.hotkey_thread = threading.Thread(target=monitor_keys, daemon=True)
        self.hotkey_thread.start()
        logger.info("Linux hotkey monitoring started")
    
    def stop_hotkey_listener(self):
        """Stop the hotkey listener"""
        try:
            if hasattr(self, 'hotkeys'):
                self.hotkeys.stop()
            self.is_running = False
            logger.info("Hotkey listener stopped")
        except Exception as e:
            logger.error(f"Error stopping hotkey listener: {e}")
    
    def handle_ctrl_f9(self):
        """Handle Ctrl+F9 hotkey"""
        logger.info("Ctrl+F9 detected")
        
        try:
            # Small delay to ensure the hotkey doesn't interfere
            time.sleep(0.1)
            
            # Get clipboard content (assuming Ctrl+C was pressed before Ctrl+F9)
            original_clipboard = self.ai_assistant.clipboard_manager.get_clipboard_text()
            
            # Try to copy selected text using keyboard simulation
            if hasattr(self, 'keyboard_controller'):
                try:
                    from pynput.keyboard import Key
                    # Simulate Ctrl+C to copy selected text
                    self.keyboard_controller.press(Key.ctrl)
                    self.keyboard_controller.press('c')
                    self.keyboard_controller.release('c')
                    self.keyboard_controller.release(Key.ctrl)
                    
                    # Wait a moment for clipboard to update
                    time.sleep(0.2)
                    
                    # Get the copied text
                    selected_text = self.ai_assistant.clipboard_manager.get_clipboard_text()
                    
                    # If clipboard didn't change, use original content
                    if selected_text == original_clipboard:
                        logger.info("No new text selected, using existing clipboard content")
                        
                except Exception as e:
                    logger.warning(f"Could not simulate Ctrl+C: {e}")
                    selected_text = original_clipboard
            else:
                # Fallback: use current clipboard content
                selected_text = original_clipboard
            
            if selected_text.strip():
                logger.info(f"Processing text: {selected_text[:50]}...")
                self.ai_assistant.process_text(selected_text)
            else:
                logger.warning("No text found to process")
                self.ai_assistant.notification_manager.show_notification(
                    "AI Assistant", 
                    "No text selected or clipboard empty"
                )
                
        except Exception as e:
            logger.error(f"Error in Ctrl+F9 handler: {e}")
            self.ai_assistant.notification_manager.show_notification(
                "AI Assistant Error", 
                f"Error: {str(e)}"
            )
    
    def handle_quick_assist(self):
        """Handle Ctrl+Shift+A hotkey for quick assistance"""
        logger.info("Ctrl+Shift+A detected")
        try:
            clipboard_text = self.ai_assistant.clipboard_manager.get_clipboard_text()
            if clipboard_text.strip():
                self.ai_assistant.process_text(f"Quick help: {clipboard_text}")
            else:
                self.ai_assistant.notification_manager.show_notification(
                    "AI Assistant", 
                    "Clipboard is empty"
                )
        except Exception as e:
            logger.error(f"Error in quick assist handler: {e}")

def main():
    """Main application entry point"""
    print("🤖 AI Assistant with Ctrl+F9 Hotkey")
    print("=" * 40)
    
    try:
        # Create AI assistant
        assistant = AIAssistant()
        
        # Create and start hotkey manager
        hotkey_manager = HotkeyManager(assistant)
        hotkey_manager.start_hotkey_listener()
        
        print("✅ AI Assistant started successfully!")
        print("\n📋 Usage:")
        print("1. Select any text in any application")
        print("2. Press Ctrl+F9 to process with AI")
        print("3. Or press Ctrl+Shift+A for quick clipboard assistance")
        print("\n🧪 Manual testing:")
        print("- Type 'test' to test clipboard functionality")
        print("- Type 'quit' to exit")
        print("\n💡 Tip: Copy some text to clipboard first, then press Ctrl+F9")
        
        # Interactive loop for testing
        while True:
            try:
                user_input = input("\n> ").strip().lower()
                
                if user_input == 'quit':
                    break
                elif user_input == 'test':
                    # Test clipboard functionality
                    clipboard_content = assistant.clipboard_manager.get_clipboard_text()
                    if clipboard_content:
                        print(f"📋 Clipboard content: {clipboard_content[:100]}...")
                        assistant.process_text(clipboard_content)
                    else:
                        print("📋 Clipboard is empty")
                elif user_input == 'status':
                    print(f"🔧 Hotkey listener running: {hotkey_manager.is_running}")
                    print(f"🤖 Processing: {assistant.is_processing}")
                elif user_input.startswith('process '):
                    # Process custom text
                    text = user_input[8:]
                    assistant.process_text(text)
                elif user_input:
                    print("Commands: test, status, process <text>, quit")
                    
            except KeyboardInterrupt:
                break
        
        print("\n🛑 Shutting down...")
        hotkey_manager.stop_hotkey_listener()
        print("✅ AI Assistant stopped")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()