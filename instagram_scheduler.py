"""
Instagram Message Scheduler
A browser-based application to schedule and send messages on Instagram.
Uses Selenium for browser automation and threading for scheduling.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import threading
import time
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


@dataclass
class ScheduledMessage:
    """Represents a scheduled message."""
    recipient: str
    message: str
    scheduled_time: str  # ISO format string
    id: str
    status: str = "pending"  # pending, sent, failed, cancelled


class InstagramScheduler:
    """Main application class for Instagram message scheduling."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Message Scheduler")
        self.root.geometry("900x700")
        
        # Data storage
        self.scheduled_messages: List[ScheduledMessage] = []
        self.driver = None
        self.is_logged_in = False
        self.schedule_thread = None
        self.stop_scheduling = False
        
        # Load saved messages
        self.load_messages()
        
        # Setup UI
        self.setup_ui()
        
        # Start scheduling thread
        self.start_scheduling_thread()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Schedule Message
        schedule_frame = ttk.Frame(notebook)
        notebook.add(schedule_frame, text="Schedule Message")
        self.setup_schedule_tab(schedule_frame)
        
        # Tab 2: View Scheduled Messages
        messages_frame = ttk.Frame(notebook)
        notebook.add(messages_frame, text="Scheduled Messages")
        self.setup_messages_tab(messages_frame)
        
        # Tab 3: Browser Control
        browser_frame = ttk.Frame(notebook)
        notebook.add(browser_frame, text="Browser Control")
        self.setup_browser_tab(browser_frame)
    
    def setup_schedule_tab(self, parent):
        """Setup the schedule message tab."""
        # Title
        title_label = ttk.Label(parent, text="Schedule Instagram Message", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # Recipient
        recipient_frame = ttk.Frame(parent)
        recipient_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(recipient_frame, text="Recipient Username:", width=20).pack(side=tk.LEFT)
        self.recipient_entry = ttk.Entry(recipient_frame, width=40)
        self.recipient_entry.pack(side=tk.LEFT, padx=5)
        
        # Message
        message_frame = ttk.Frame(parent)
        message_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(message_frame, text="Message:", width=20).pack(side=tk.LEFT)
        self.message_text = scrolledtext.ScrolledText(message_frame, width=50, height=5)
        self.message_text.pack(padx=5, pady=5)
        
        # Date and Time
        datetime_frame = ttk.Frame(parent)
        datetime_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(datetime_frame, text="Scheduled Date (YYYY-MM-DD):", width=25).pack(side=tk.LEFT)
        self.date_entry = ttk.Entry(datetime_frame, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(datetime_frame, text="Time (HH:MM):", width=10).pack(side=tk.LEFT, padx=10)
        self.time_entry = ttk.Entry(datetime_frame, width=10)
        self.time_entry.pack(side=tk.LEFT, padx=5)
        self.time_entry.insert(0, datetime.now().strftime("%H:%M"))
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Schedule Message", 
                  command=self.schedule_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Form", 
                  command=self.clear_form).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(parent, text="", foreground="green")
        self.status_label.pack(pady=10)
    
    def setup_messages_tab(self, parent):
        """Setup the scheduled messages tab."""
        # Title
        title_label = ttk.Label(parent, text="Scheduled Messages", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # Messages list with scrollbar
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview for messages
        columns = ("id", "recipient", "message", "scheduled_time", "status")
        self.messages_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.messages_tree.heading("id", text="ID")
        self.messages_tree.heading("recipient", text="Recipient")
        self.messages_tree.heading("message", text="Message")
        self.messages_tree.heading("scheduled_time", text="Scheduled Time")
        self.messages_tree.heading("status", text="Status")
        
        self.messages_tree.column("id", width=50)
        self.messages_tree.column("recipient", width=120)
        self.messages_tree.column("message", width=300)
        self.messages_tree.column("scheduled_time", width=150)
        self.messages_tree.column("status", width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.messages_tree.yview)
        self.messages_tree.configure(yscroll=scrollbar.set)
        
        self.messages_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Refresh List", 
                  command=self.refresh_messages_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel Selected", 
                  command=self.cancel_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Send Now", 
                  command=self.send_selected_now).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export", 
                  command=self.export_messages).pack(side=tk.LEFT, padx=5)
        
        # Refresh the list
        self.refresh_messages_list()
    
    def setup_browser_tab(self, parent):
        """Setup the browser control tab."""
        # Title
        title_label = ttk.Label(parent, text="Browser Control", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # Browser status
        status_frame = ttk.LabelFrame(parent, text="Browser Status", padding=10)
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.browser_status_label = ttk.Label(status_frame, text="Browser: Not Started", 
                                             foreground="red")
        self.browser_status_label.pack()
        
        self.login_status_label = ttk.Label(status_frame, text="Login: Not Logged In", 
                                           foreground="red")
        self.login_status_label.pack()
        
        # Browser controls
        control_frame = ttk.Frame(parent)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="Start Browser", 
                  command=self.start_browser).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Go to Instagram", 
                  command=self.go_to_instagram).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Test Send Message", 
                  command=self.test_send_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Close Browser", 
                  command=self.close_browser).pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = ttk.LabelFrame(parent, text="Instructions", padding=10)
        instructions.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        instruction_text = """
1. Click "Start Browser" to launch Chrome with Instagram.
2. Log in to your Instagram account manually in the browser.
3. Click "Go to Instagram" to navigate to Instagram Direct Messages.
4. Schedule messages using the "Schedule Message" tab.
5. Messages will be sent automatically at the scheduled time.
6. You can also select a message and click "Send Now" to send immediately.

NOTE: Keep the browser window open and visible for automated sending to work.
The browser must remain logged in for scheduled messages to be sent.
        """
        ttk.Label(instructions, text=instruction_text, justify=tk.LEFT).pack()
    
    def schedule_message(self):
        """Schedule a new message."""
        recipient = self.recipient_entry.get().strip()
        message = self.message_text.get("1.0", tk.END).strip()
        date_str = self.date_entry.get().strip()
        time_str = self.time_entry.get().strip()
        
        if not recipient or not message or not date_str or not time_str:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            scheduled_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid date/time format. Use YYYY-MM-DD HH:MM")
            return
        
        if scheduled_datetime <= datetime.now():
            messagebox.showerror("Error", "Scheduled time must be in the future")
            return
        
        # Create scheduled message
        msg_id = f"msg_{len(self.scheduled_messages) + 1}_{int(time.time())}"
        scheduled_msg = ScheduledMessage(
            recipient=recipient,
            message=message,
            scheduled_time=scheduled_datetime.isoformat(),
            id=msg_id
        )
        
        self.scheduled_messages.append(scheduled_msg)
        self.save_messages()
        self.refresh_messages_list()
        self.clear_form()
        
        self.status_label.config(
            text=f"Message scheduled for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}",
            foreground="green"
        )
    
    def clear_form(self):
        """Clear the schedule form."""
        self.recipient_entry.delete(0, tk.END)
        self.message_text.delete("1.0", tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, datetime.now().strftime("%H:%M"))
    
    def refresh_messages_list(self):
        """Refresh the scheduled messages list."""
        # Clear existing items
        for item in self.messages_tree.get_children():
            self.messages_tree.delete(item)
        
        # Add current messages
        for msg in self.scheduled_messages:
            self.messages_tree.insert("", tk.END, values=(
                msg.id[:10] + "...",
                msg.recipient,
                msg.message[:50] + "..." if len(msg.message) > 50 else msg.message,
                datetime.fromisoformat(msg.scheduled_time).strftime("%Y-%m-%d %H:%M"),
                msg.status
            ))
    
    def cancel_selected(self):
        """Cancel the selected message."""
        selection = self.messages_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a message to cancel")
            return
        
        item = self.messages_tree.item(selection[0])
        msg_id_prefix = item["values"][0]
        
        # Find and cancel the message
        for msg in self.scheduled_messages:
            if msg.id.startswith(msg_id_prefix):
                msg.status = "cancelled"
                break
        
        self.save_messages()
        self.refresh_messages_list()
        messagebox.showinfo("Success", "Message cancelled")
    
    def send_selected_now(self):
        """Send the selected message immediately."""
        selection = self.messages_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a message to send")
            return
        
        item = self.messages_tree.item(selection[0])
        msg_id_prefix = item["values"][0]
        
        # Find the message
        target_msg = None
        for msg in self.scheduled_messages:
            if msg.id.startswith(msg_id_prefix):
                target_msg = msg
                break
        
        if target_msg:
            # Send in a separate thread
            thread = threading.Thread(target=self.send_message, args=(target_msg,))
            thread.start()
    
    def export_messages(self):
        """Export scheduled messages to a file."""
        if not self.scheduled_messages:
            messagebox.showwarning("Warning", "No messages to export")
            return
        
        filename = f"instagram_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump([asdict(msg) for msg in self.scheduled_messages], f, indent=2)
        
        messagebox.showinfo("Success", f"Messages exported to {filename}")
    
    def start_browser(self):
        """Start the Chrome browser."""
        if self.driver:
            messagebox.showwarning("Warning", "Browser is already running")
            return
        
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            
            # Start Chrome
            self.driver = webdriver.Chrome(options=chrome_options)
            self.browser_status_label.config(text="Browser: Running", foreground="green")
            
            # Navigate to Instagram
            self.driver.get("https://www.instagram.com/")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start browser: {str(e)}")
    
    def go_to_instagram(self):
        """Navigate to Instagram Direct Messages."""
        if not self.driver:
            messagebox.showerror("Error", "Browser is not started")
            return
        
        try:
            self.driver.get("https://www.instagram.com/direct/inbox/")
            self.login_status_label.config(text="Login: Please log in manually", foreground="orange")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to navigate: {str(e)}")
    
    def close_browser(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.browser_status_label.config(text="Browser: Closed", foreground="red")
                self.login_status_label.config(text="Login: Not Logged In", foreground="red")
                self.is_logged_in = False
            except:
                pass
    
    def test_send_message(self):
        """Test sending a message to verify the automation works."""
        if not self.driver:
            messagebox.showerror("Error", "Browser is not started")
            return
        
        recipient = self.recipient_entry.get().strip()
        message = self.message_text.get("1.0", tk.END).strip()
        
        if not recipient or not message:
            messagebox.showerror("Error", "Please enter recipient and message")
            return
        
        # Send in a separate thread
        thread = threading.Thread(target=self._send_test_message, args=(recipient, message))
        thread.start()
    
    def _send_test_message(self, recipient, message):
        """Actually send a test message using Selenium."""
        try:
            driver = self.driver
            
            # Go to Instagram Direct
            driver.get("https://www.instagram.com/direct/inbox/")
            time.sleep(3)
            
            # Wait for page to load
            wait = WebDriverWait(driver, 10)
            
            # Try to find and click on the search/message button
            try:
                # Look for the compose button
                compose_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(text(), 'Send message')]")
                ))
                compose_button.click()
                time.sleep(2)
            except:
                pass
            
            # Search for the recipient
            try:
                search_box = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='Search']")
                ))
                search_box.clear()
                search_box.send_keys(recipient)
                time.sleep(2)
                
                # Click on the first result
                first_result = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//span[contains(text(), '{recipient}')]")
                ))
                first_result.click()
                time.sleep(2)
            except Exception as e:
                print(f"Error finding recipient: {e}")
            
            # Type and send the message
            try:
                message_box = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//textarea[@aria-label='Message...']")
                ))
                message_box.clear()
                message_box.send_keys(message)
                time.sleep(1)
                message_box.send_keys(Keys.RETURN)
                time.sleep(2)
                
                messagebox.showinfo("Success", "Test message sent successfully!")
            except Exception as e:
                print(f"Error sending message: {e}")
                messagebox.showerror("Error", f"Failed to send message: {str(e)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Test failed: {str(e)}")
    
    def send_message(self, scheduled_msg: ScheduledMessage):
        """Send a scheduled message."""
        try:
            if not self.driver:
                # Auto-start browser if not running
                self.root.after(0, self.start_browser)
                time.sleep(5)
            
            driver = self.driver
            recipient = scheduled_msg.recipient
            message = scheduled_msg.message
            
            # Navigate to direct messages
            driver.get("https://www.instagram.com/direct/t/" + recipient)
            time.sleep(3)
            
            wait = WebDriverWait(driver, 10)
            
            # Type and send message
            try:
                message_box = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//textarea[@aria-label='Message...']")
                ))
                message_box.clear()
                message_box.send_keys(message)
                time.sleep(1)
                message_box.send_keys(Keys.RETURN)
                time.sleep(2)
                
                scheduled_msg.status = "sent"
                self.save_messages()
                self.root.after(0, self.refresh_messages_list)
                
            except Exception as e:
                scheduled_msg.status = "failed"
                self.save_messages()
                self.root.after(0, self.refresh_messages_list)
                print(f"Failed to send message: {e}")
                
        except Exception as e:
            scheduled_msg.status = "failed"
            self.save_messages()
            print(f"Error in send_message: {e}")
    
    def start_scheduling_thread(self):
        """Start the thread that checks for scheduled messages."""
        self.stop_scheduling = False
        self.schedule_thread = threading.Thread(target=self._check_scheduled_messages, daemon=True)
        self.schedule_thread.start()
    
    def _check_scheduled_messages(self):
        """Background thread that checks and sends scheduled messages."""
        while not self.stop_scheduling:
            try:
                now = datetime.now()
                for msg in self.scheduled_messages:
                    if msg.status == "pending":
                        scheduled_time = datetime.fromisoformat(msg.scheduled_time)
                        if scheduled_time <= now:
                            # Time to send
                            msg.status = "sending"
                            self.send_message(msg)
                
                # Check every 30 seconds
                time.sleep(30)
            except Exception as e:
                print(f"Error in scheduling thread: {e}")
                time.sleep(30)
    
    def save_messages(self):
        """Save scheduled messages to a file."""
        try:
            with open("scheduled_messages.json", "w") as f:
                json.dump([asdict(msg) for msg in self.scheduled_messages], f, indent=2)
        except Exception as e:
            print(f"Error saving messages: {e}")
    
    def load_messages(self):
        """Load scheduled messages from file."""
        try:
            if os.path.exists("scheduled_messages.json"):
                with open("scheduled_messages.json", "r") as f:
                    messages_data = json.load(f)
                    self.scheduled_messages = [
                        ScheduledMessage(**msg_data) for msg_data in messages_data
                    ]
        except Exception as e:
            print(f"Error loading messages: {e}")
            self.scheduled_messages = []
    
    def on_closing(self):
        """Handle window close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.stop_scheduling = True
            self.close_browser()
            self.save_messages()
            self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = InstagramScheduler(root)
    root.mainloop()


if __name__ == "__main__":
    main()