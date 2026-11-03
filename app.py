import sys
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

__version__ = "1.0.2"

# Set your GitHub repository details
REPO_OWNER = "cy4001"
REPO_NAME = "studio"

def parse_semver(tag: str):
    tag = tag.lstrip("vV")
    try:
        return [int(x) for x in tag.split(".")]
    except ValueError:
        return [0, 0, 0]

def check_for_updates():
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    try:
        res = requests.get(api_url, timeout=4)
        if res.status_code != 200:
            return None, None
        
        data = res.json()
        latest_tag = data.get("tag_name", "")
        
        if parse_semver(latest_tag) > parse_semver(__version__):
            # Look for an asset named 'app.exe'
            for asset in data.get("assets", []):
                if asset.get("name") == "app.exe":
                    return latest_tag, asset.get("browser_download_url")
    except Exception:
        pass
    return None, None

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Login Portal - v{__version__}")
        self.setFixedSize(340, 260)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel(f"Sign In (v{__version__})")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        btn_layout.addWidget(self.login_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def handle_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text().strip()
        if user == "admin" and pwd == "admin":
            QMessageBox.information(self, "Success", "Authentication successful!")
        else:
            QMessageBox.warning(self, "Failed", "Invalid credentials entered.")

def main():
    app = QApplication(sys.argv)
    
    # Check for update on launch
    latest_version, download_url = check_for_updates()
    if latest_version and download_url:
        reply = QMessageBox.question(
            None,
            "Update Available",
            f"Version {latest_version} is available (Current: v{__version__}).\nUpdate now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            updater_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "updater.exe")
            if os.path.exists(updater_path):
                # Pass PID, target exe path, and download URL to updater
                os.spawnv(
                    os.P_NOWAIT,
                    updater_path,
                    [
                        "updater.exe",
                        str(os.getpid()),
                        os.path.abspath(sys.argv[0]),
                        download_url
                    ]
                )
                sys.exit(0)
            else:
                QMessageBox.critical(None, "Error", "updater.exe not found in directory.")

    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()