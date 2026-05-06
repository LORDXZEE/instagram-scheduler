# Instagram Message Scheduler

A Python application that uses browser automation to schedule and send messages on Instagram Direct Messages.

## Features

- **Schedule Messages**: Set up messages to be sent at specific dates and times
- **Browser Automation**: Uses Selenium to control Chrome browser and interact with Instagram
- **Message Management**: View, cancel, or send messages immediately
- **Persistent Storage**: Messages are saved to a JSON file and persist between sessions
- **Export Functionality**: Export your scheduled messages to a file

## Requirements

- Python 3.8 or higher
- Google Chrome browser installed
- Instagram account

## Installation

1. Clone or download this repository

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure Google Chrome is installed on your system

## Usage

1. Run the application:
```bash
python instagram_scheduler.py
```

2. **First Time Setup**:
   - Click on the "Browser Control" tab
   - Click "Start Browser" to launch Chrome
   - Log in to your Instagram account manually in the browser window
   - The browser will navigate to Instagram

3. **Schedule a Message**:
   - Go to the "Schedule Message" tab
   - Enter the recipient's Instagram username
   - Type your message
   - Set the date and time for sending
   - Click "Schedule Message"

4. **Manage Scheduled Messages**:
   - Go to the "Scheduled Messages" tab to see all your scheduled messages
   - You can:
     - **Refresh List**: Update the display
     - **Cancel Selected**: Cancel a pending message
     - **Send Now**: Send a message immediately
     - **Export**: Save messages to a JSON file

5. **Test Sending**:
   - In the "Browser Control" tab, you can test sending a message
   - Enter recipient and message in the Schedule tab first
   - Then click "Test Send Message" to verify automation works

## Important Notes

- **Keep the browser open**: For automated sending to work, the Chrome browser must remain open
- **Stay logged in**: Make sure you remain logged in to Instagram in the browser
- **Visible browser**: The browser window should be visible (not minimized) for best results
- **Instagram limitations**: Instagram may have rate limits and anti-automation measures. Use responsibly.
- **Personal use only**: This tool is intended for personal use. Respect Instagram's Terms of Service.

## How It Works

1. The application creates a Tkinter GUI with three tabs
2. When you schedule a message, it's stored in memory and saved to a JSON file
3. A background thread checks every 30 seconds for messages that need to be sent
4. When it's time to send a message, Selenium automates the browser to:
   - Navigate to the recipient's chat
   - Type the message
   - Send it
5. The message status is updated to "sent" or "failed"

## Troubleshooting

### Browser doesn't start
- Make sure Google Chrome is installed
- Check if ChromeDriver is compatible with your Chrome version
- Try running the application as administrator

### Cannot find recipient
- Make sure the username is correct
- The recipient must be someone you can message (follows you or you follow them)
- Instagram's interface may have changed, requiring updates to the selectors

### Messages not sending automatically
- Ensure the browser is still open and logged in
- Check the console for error messages
- The browser window should not be minimized

### Login issues
- You may need to verify your identity with Instagram
- Two-factor authentication might interfere
- Try logging in manually first, then use the app

## Disclaimer

This tool is for educational purposes and personal use only. 

- Respect Instagram's Terms of Service
- Do not use for spam or unsolicited messages
- Instagram may detect automated behavior and restrict your account
- Use at your own risk

## License

MIT License - Feel free to modify and distribute as needed.

## Contributing

Feel free to submit issues and enhancement requests!