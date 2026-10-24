import os
import time
import subprocess
import urllib.parse
from typing import Dict, Any
import pyautogui
import pyperclip


def send_whatsapp_message(contact: str = "", text: str = "") -> Dict[str, Any]:
    """
    Directly dispatch a WhatsApp message on Windows without forward dialogs or manual selection.
    Automatically focuses WhatsApp, searches the contact, opens the chat, pastes the text,
    and presses Enter to send immediately.
    """
    clean_text = text.strip() or "Hi"
    clean_contact = contact.strip()

    # 1. If clean_contact is numeric phone number (e.g. +91... or digits)
    clean_digits = "".join(c for c in clean_contact if c.isdigit())
    if clean_digits and len(clean_digits) >= 7 and (len(clean_digits) == len(clean_contact) or clean_contact.startswith("+")):
        encoded_text = urllib.parse.quote(clean_text)
        protocol_url = f"whatsapp://send?phone={clean_digits}&text={encoded_text}"
        try:
            os.startfile(protocol_url)
        except Exception:
            subprocess.Popen(f'start "" "{protocol_url}"', shell=True)

        time.sleep(1.2)
        pyautogui.press('enter')
        return {
            "success": True,
            "contact": clean_digits,
            "text": clean_text,
            "message": f"Directly dispatched WhatsApp transmission to {clean_digits}: '{clean_text}'."
        }

    # 2. Contact Name Direct Dispatch (Zero Forward Dialog!)
    # Bring WhatsApp to foreground
    try:
        os.startfile("whatsapp:")
    except Exception:
        subprocess.Popen('start "" "whatsapp:"', shell=True)

    time.sleep(0.5)

    # In case the share / forward dialog is currently open on user screen, press Esc to close it
    pyautogui.press('esc')
    time.sleep(0.15)

    search_target = clean_contact
    if not search_target or any(kw in search_target.lower() for kw in ["any one", "anyone", "any contact", "someone", "any of my contacts"]):
        # Press Down arrow to select the first chat in recent list
        pyautogui.press('down')
        time.sleep(0.2)
        pyautogui.press('enter')
        time.sleep(0.4)
    else:
        # Press Ctrl+F to focus search bar
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.25)
        # Paste contact name via clipboard for 100% Unicode & emoji fidelity
        pyperclip.copy(search_target)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)  # Give WhatsApp time to filter results
        # Press Enter to open the top matched conversation
        pyautogui.press('enter')
        time.sleep(0.4)

    # Now focus is in the message input box at the bottom of the conversation!
    # Copy message text to clipboard and paste it
    pyperclip.copy(clean_text)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.2)
    # Press Enter to SEND the message directly!
    pyautogui.press('enter')

    recipient_desc = f"to {clean_contact}" if clean_contact else "to recent contact"
    return {
        "success": True,
        "contact": clean_contact or "Recent Contact",
        "text": clean_text,
        "message": f"Directly sent WhatsApp message {recipient_desc}: '{clean_text}'."
    }
