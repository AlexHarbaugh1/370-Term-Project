import sys
import socket
import threading
import random
import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QListWidget, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

class ChatClient(QWidget):
    new_message_signal = pyqtSignal(str)
    
    def __init__(self, host='127.0.0.1', port=65432):
        super().__init__()
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = None
        self.user_colors = {}  # To assign each user a distinct color
        self.typing_sent = False  # Flag to avoid spamming typing notifications
        self.initUI()
        self.apply_dark_theme()
        self.new_message_signal.connect(self.process_message)
        self.connect_to_server()

    def initUI(self):
        self.setWindowTitle("Chat Client")
        self.setGeometry(100, 100, 600, 500)  # A wider window to show the user list

        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left side: chat messages and input
        left_layout = QVBoxLayout()
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        left_layout.addWidget(self.chat_display)
        
        # Typing indicator label (shows who is typing)
        self.typing_indicator = QLabel("")
        self.typing_indicator.setStyleSheet("font-style: italic; color: #AAAAAA;")
        left_layout.addWidget(self.typing_indicator)

        # Message input field
        self.message_input = QLineEdit(self)
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.textChanged.connect(self.handle_typing)
        # Connect pressing Enter (returnPressed) to send the message
        self.message_input.returnPressed.connect(self.send_message)
        left_layout.addWidget(self.message_input)

        # Buttons: Send and Clear Chat
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)
        
        self.clear_button = QPushButton("Clear Chat", self)
        self.clear_button.clicked.connect(lambda: self.chat_display.clear())
        button_layout.addWidget(self.clear_button)
        
        left_layout.addLayout(button_layout)
        main_layout.addLayout(left_layout)

        # Right side: Active users list
        self.user_list_widget = QListWidget(self)
        self.user_list_widget.setFixedWidth(150)
        main_layout.addWidget(self.user_list_widget)

        self.setLayout(main_layout)

        # Timer to clear the typing indicator after 3 seconds
        self.typing_timer = QTimer()
        self.typing_timer.setInterval(3000)
        self.typing_timer.timeout.connect(self.clear_typing_indicator)

    def apply_dark_theme(self):
        """Apply a dark theme to the UI."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #F2F2F2;
                font-family: Arial;
            }
            QTextEdit, QLineEdit {
                background-color: #3E3E3E;
                border: 1px solid #555;
                color: #F2F2F2;
            }
            QPushButton {
                background-color: #555;
                border: none;
                padding: 5px;
                color: #F2F2F2;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QListWidget {
                background-color: #3E3E3E;
                border: 1px solid #555;
                color: #F2F2F2;
            }
            QLabel {
                color: #AAAAAA;
            }
        """)

    def connect_to_server(self):
        """Establish connection to the server and start the receiver thread."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            self.username = self.get_username()
            self.client_socket.sendall(self.username.encode())

            # Start thread for receiving messages
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.chat_display.append(f"Error: {e}")

    def get_username(self):
        """Prompt for a username in the console."""
        return input("Enter your username: ")

    def receive_messages(self):
        """Continuously receive messages from the server."""
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                self.new_message_signal.emit(message)
            except Exception as e:
                print("Receive error:", e)
                break

    def process_message(self, message):
        """Update the UI based on the incoming message."""
        if message.startswith("[USERS]"):
            # Update active user list
            users_str = message[len("[USERS]"):]
            users = users_str.split(",") if users_str else []
            self.user_list_widget.clear()
            self.user_list_widget.addItems(users)
        elif message.startswith("[TYPING]"):
            # Update typing indicator (exclude own typing notifications)
            typers = message[len("[TYPING]"):].split(",")
            typers = [t for t in typers if t != self.username]
            if typers:
                self.typing_indicator.setText(", ".join(typers) + " is typing...")
                self.typing_timer.start()  # Clear after delay
            else:
                self.typing_indicator.clear()
        else:
            # Regular chat message: display with colored username and a timestamp
            if ":" in message:
                parts = message.split(":", 1)
                user = parts[0].strip()
                text = parts[1].strip()
                if user not in self.user_colors:
                    color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                    self.user_colors[user] = color
                else:
                    color = self.user_colors[user]
                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                formatted_message = f'<span style="color:{color}; font-weight: bold;">{user}</span> [{timestamp}]: {text}'
                self.chat_display.append(formatted_message)
            else:
                self.chat_display.append(message)

    def handle_typing(self):
        """Send a typing notification when the user is typing."""
        if not self.typing_sent:
            try:
                self.client_socket.sendall("[TYPING]".encode())
            except Exception as e:
                print("Typing notification error:", e)
            self.typing_sent = True
            QTimer.singleShot(3000, self.reset_typing_flag)

    def reset_typing_flag(self):
        self.typing_sent = False

    def clear_typing_indicator(self):
        self.typing_indicator.clear()
        self.typing_timer.stop()

    def send_message(self):
        """Send the message and update your own chat window immediately."""
        message = self.message_input.text()
        if message:
            full_message = f"{self.username}: {message}"
            try:
                self.client_socket.sendall(message.encode())
            except Exception as e:
                self.chat_display.append(f"Error sending message: {e}")
            self.process_message(full_message)
            self.message_input.clear()

    def closeEvent(self, event):
        """Cleanly disconnect from the server on window close."""
        if self.client_socket:
            try:
                self.client_socket.sendall("exit".encode())
                self.client_socket.close()
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    chat_client = ChatClient()
    chat_client.show()
    sys.exit(app.exec_())
