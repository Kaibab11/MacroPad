from PyQt6.QtWidgets import QPushButton


class KeyButton(QPushButton):
    """Custom button representing a key on the macropad"""
    
    def __init__(self, key_index: int, initial_key: str = "KC.NO"):
        super().__init__(initial_key)
        self.key_index = key_index
        self.current_key = initial_key
        self.setMinimumSize(80, 60)
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #555;
                border-radius: 5px;
                background-color: #f0f0f0;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
    
    def set_key(self, key_code: str):
        """Update the key assignment"""
        self.current_key = key_code
        display_text = key_code.replace("KC.", "") if key_code.startswith("KC.") else key_code
        self.setText(display_text)