#!/usr/bin/env python3
"""
Simple test script for hotkey functionality
Run this to test if Ctrl+F9 detection works properly
"""

import sys
import time
import logging
from pynput.keyboard import Key, GlobalHotKeys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def on_ctrl_f9():
    """Test handler for Ctrl+F9"""
    print("✅ Ctrl+F9 detected successfully!")
    logger.info("Ctrl+F9 hotkey triggered")

def on_escape():
    """Exit on Escape key"""
    print("Exiting...")
    return False

def main():
    """Main test function"""
    print("Testing Ctrl+F9 hotkey detection...")
    print("Press Ctrl+F9 to test the hotkey")
    print("Press Escape to exit")
    
    # Setup hotkeys
    hotkeys = {
        '<ctrl>+<f9>': on_ctrl_f9,
        '<esc>': on_escape
    }
    
    try:
        # Start listening
        with GlobalHotKeys(hotkeys):
            print("Hotkey listener active. Waiting for Ctrl+F9...")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have the required permissions to capture global hotkeys")

if __name__ == "__main__":
    main()