
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QGridLayout, QPushButton, QLineEdit, QLabel, QDialogButtonBox


class KeySelectorDialog(QDialog):
    """Dialog for selecting key codes"""
    
    def __init__(self, current_key: str = "KC.NO", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Key")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # Quick select buttons for common keys
        common_group = QGroupBox("Common Keys")
        common_layout = QGridLayout(common_group)
        
        common_keys = [
            "KC.A", "KC.B", "KC.C", "KC.D", "KC.E", "KC.F",
            "KC.G", "KC.H", "KC.I", "KC.J", "KC.K", "KC.L",
            "KC.M", "KC.N", "KC.O", "KC.P", "KC.Q", "KC.R",
            "KC.S", "KC.T", "KC.U", "KC.V", "KC.W", "KC.X",
            "KC.Y", "KC.Z", "KC.1", "KC.2", "KC.3", "KC.4",
            "KC.5", "KC.6", "KC.7", "KC.8", "KC.9", "KC.0"
        ]
        
        for i, key in enumerate(common_keys):
            btn = QPushButton(key.replace("KC.", ""))
            btn.clicked.connect(lambda checked, k=key: self.select_key(k))
            common_layout.addWidget(btn, i // 6, i % 6)
        
        layout.addWidget(common_group)
        
        # Special keys
        special_group = QGroupBox("Special Keys")
        special_layout = QGridLayout(special_group)
        
        special_keys = [
            "KC.ENTER", "KC.SPACE", "KC.TAB", "KC.ESC",
            "KC.BACKSPACE", "KC.DELETE", "KC.LEFT", "KC.RIGHT",
            "KC.UP", "KC.DOWN", "KC.CTRL", "KC.ALT",
            "KC.SHIFT", "KC.CMD", "KC.F1", "KC.F2"
        ]
        
        for i, key in enumerate(special_keys):
            btn = QPushButton(key.replace("KC.", ""))
            btn.clicked.connect(lambda checked, k=key: self.select_key(k))
            special_layout.addWidget(btn, i // 4, i % 4)
        
        layout.addWidget(special_group)
        
        # Custom key input
        custom_group = QGroupBox("Custom Key Code")
        custom_layout = QVBoxLayout(custom_group)
        
        self.custom_input = QLineEdit(current_key)
        custom_layout.addWidget(QLabel("Enter key code (e.g., KC.CTRL):"))
        custom_layout.addWidget(self.custom_input)
        
        layout.addWidget(custom_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.selected_key = current_key
    
    def select_key(self, key: str):
        """Select a key and update the custom input"""
        self.selected_key = key
        self.custom_input.setText(key)
    
    def accept(self):
        """Accept the dialog and return the selected key"""
        self.selected_key = self.custom_input.text().strip()
        if not self.selected_key:
            self.selected_key = "KC.NO"
        super().accept()