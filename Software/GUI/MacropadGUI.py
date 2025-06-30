import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QComboBox,
    QGroupBox, QMessageBox,QFrame, QDialog,
    QListWidget, QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import QTimer, QSettings, QThreadPool, pyqtSlot
from PyQt6.QtGui import QAction, QFont

from ConfigManager import ConfigManager
from KeyButton import KeyButton
from KeySelectorDialog import KeySelectorDialog
from SerialCommunicator import SerialCommunicator
from AutoDetect import AutoDetectWorker

class MacropadGUI(QMainWindow):
    """Main GUI application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macropad Configuration Tool")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize components
        self.serial_comm = SerialCommunicator()
        self.config_manager = ConfigManager()
        self.settings = QSettings("MacropadGUI", "Settings")
        
        # State variables
        self.current_layers = [{"name": "Default", "keys": ["KC.NO"] * 12}]
        self.current_layer_index = 0
        self.connected_port = None
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        
        # Auto-detect and connect
        self.thread_pool = QThreadPool()
        self.auto_detect_device()
        
        # Load last used configuration
        self.load_last_config()

        #self.add_custom_device_detection(vid_pid_pairs=[(0x2886, 0x0042)])  # Replace with your actual VID/PID
    
    def setup_ui(self):
        """Setup the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Layer management
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        # Connection status
        connection_group = QGroupBox("Connection")
        connection_layout = QVBoxLayout(connection_group)
        
        self.connection_status = QLabel("Not connected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        connection_layout.addWidget(self.connection_status)
        
        self.port_combo = QComboBox()
        self.refresh_ports_btn = QPushButton("Refresh Ports")
        self.connect_btn = QPushButton("Connect")
        
        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(self.refresh_ports_btn)
        connection_layout.addWidget(self.connect_btn)
        
        left_layout.addWidget(connection_group)
        
        # Layer management
        layer_group = QGroupBox("Layers")
        layer_layout = QVBoxLayout(layer_group)
        
        self.layer_list = QListWidget()
        layer_layout.addWidget(self.layer_list)
        
        layer_buttons = QHBoxLayout()
        self.add_layer_btn = QPushButton("Add")
        self.rename_layer_btn = QPushButton("Rename")
        self.delete_layer_btn = QPushButton("Delete")
        
        layer_buttons.addWidget(self.add_layer_btn)
        layer_buttons.addWidget(self.rename_layer_btn)
        layer_buttons.addWidget(self.delete_layer_btn)
        layer_layout.addLayout(layer_buttons)
        
        left_layout.addWidget(layer_group)
        
        # Configuration management
        config_group = QGroupBox("Configurations")
        config_layout = QVBoxLayout(config_group)
        
        self.config_combo = QComboBox()
        config_layout.addWidget(QLabel("Saved Configs:"))
        config_layout.addWidget(self.config_combo)
        
        config_buttons = QVBoxLayout()
        self.load_config_btn = QPushButton("Load")
        self.save_config_btn = QPushButton("Save As...")
        self.delete_config_btn = QPushButton("Delete")
        
        config_buttons.addWidget(self.load_config_btn)
        config_buttons.addWidget(self.save_config_btn)
        config_buttons.addWidget(self.delete_config_btn)
        config_layout.addLayout(config_buttons)
        
        left_layout.addWidget(config_group)
        left_layout.addStretch()
        
        # Right panel - Key layout
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)
        
        # Current layer info
        layer_info = QHBoxLayout()
        self.current_layer_label = QLabel("Layer: Default")
        self.current_layer_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layer_info.addWidget(self.current_layer_label)
        layer_info.addStretch()
        
        self.send_to_device_btn = QPushButton("Send Current Layer")
        self.send_to_device_btn.setEnabled(False)
        layer_info.addWidget(self.send_to_device_btn)

        self.send_all_layers_to_device_btn = QPushButton("Send All Layers")
        self.send_all_layers_to_device_btn.setEnabled(False)
        layer_info.addWidget(self.send_all_layers_to_device_btn)
        
        right_layout.addLayout(layer_info)
        
        # 4x3 key grid (4 columns, 3 rows)
        key_grid_widget = QWidget()
        key_grid = QGridLayout(key_grid_widget)
        key_grid.setSpacing(10)
        
        self.key_buttons = []
        for row in range(3):  # 3 rows
            for col in range(4):  # 4 columns
                key_index = row * 4 + col
                key_btn = KeyButton(key_index)
                key_btn.clicked.connect(lambda checked, idx=key_index: self.edit_key(idx))
                key_grid.addWidget(key_btn, row, col)
                self.key_buttons.append(key_btn)
        
        right_layout.addWidget(key_grid_widget)
        right_layout.addStretch()
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initialize layer list
        self.update_layer_list()
        self.update_config_list()
    
    def setup_menu(self):
        """Setup the menu bar with debug options"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Configuration", self)
        new_action.triggered.connect(self.new_configuration)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Device menu
        device_menu = menubar.addMenu("Device")
        
        ping_action = QAction("Ping Device", self)
        ping_action.triggered.connect(self.ping_device)
        device_menu.addAction(ping_action)
        
        get_keymap_action = QAction("Get Current Keymap", self)
        get_keymap_action.triggered.connect(self.get_current_keymap)
        device_menu.addAction(get_keymap_action)
        
        # Debug menu
        debug_menu = menubar.addMenu("Debug")
        
        list_devices_action = QAction("List All Devices", self)
        list_devices_action.triggered.connect(self.debug_list_all_devices)
        debug_menu.addAction(list_devices_action)
        
        force_connect_action = QAction("Force Connect to Selected Port", self)
        force_connect_action.triggered.connect(self.force_connect_selected)
        debug_menu.addAction(force_connect_action)
        
        test_auto_detect_action = QAction("Test Auto-Detect", self)
        test_auto_detect_action.triggered.connect(self.auto_detect_device)
        debug_menu.addAction(test_auto_detect_action)

    def setup_debug_menu(self):
        """Add debug menu to help with device detection"""
        # Add this to your setup_menu method
        debug_menu = self.menuBar().addMenu("Debug")
        
        list_devices_action = QAction("List All Devices", self)
        list_devices_action.triggered.connect(self.debug_list_all_devices)
        debug_menu.addAction(list_devices_action)
        
        force_connect_action = QAction("Force Connect to Selected Port", self)
        force_connect_action.triggered.connect(self.force_connect_selected)
        debug_menu.addAction(force_connect_action)
        
        test_auto_detect_action = QAction("Test Auto-Detect", self)
        test_auto_detect_action.triggered.connect(self.auto_detect_device)
        debug_menu.addAction(test_auto_detect_action)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Serial communication
        self.serial_comm.message_received.connect(self.handle_device_message)
        self.serial_comm.connection_status_changed.connect(self.handle_connection_status)
        
        # UI connections
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        # Layer management
        self.layer_list.currentRowChanged.connect(self.switch_layer)
        self.add_layer_btn.clicked.connect(self.add_layer)
        self.rename_layer_btn.clicked.connect(self.rename_layer)
        self.delete_layer_btn.clicked.connect(self.delete_layer)
        
        # Configuration management
        self.load_config_btn.clicked.connect(self.load_configuration)
        self.save_config_btn.clicked.connect(self.save_configuration)
        self.delete_config_btn.clicked.connect(self.delete_configuration)
        
        # Device communication
        self.send_to_device_btn.clicked.connect(self.send_current_layer_to_device)
        self.send_all_layers_to_device_btn.clicked.connect(self.send_all_layers_to_device)
        
        self.refresh_ports()
    
    def refresh_ports(self):
        """Refresh the list of available serial ports with detailed info"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        print("\n=== Available Serial Ports ===")
        for i, port in enumerate(ports):
            print(f"Port {i+1}:")
            print(f"  Device: {port.device}")
            print(f"  Description: {port.description}")
            print(f"  Hardware ID: {port.hwid}")
            print(f"  Manufacturer: {getattr(port, 'manufacturer', 'Unknown')}")
            print(f"  Product: {getattr(port, 'product', 'Unknown')}")
            print(f"  Serial Number: {getattr(port, 'serial_number', 'Unknown')}")
            print(f"  VID:PID: {getattr(port, 'vid', 'Unknown')}:{getattr(port, 'pid', 'Unknown')}")
            print("-" * 40)
            
            # Add to combo box with detailed description
            combo_text = f"{port.device} - {port.description}"
            if hasattr(port, 'manufacturer') and port.manufacturer:
                combo_text += f" ({port.manufacturer})"
            self.port_combo.addItem(combo_text)
        
        print(f"Total ports found: {len(ports)}\n")

    
    def toggle_connection(self):
        """Connect or disconnect from the device"""
        if self.serial_comm.running:
            self.disconnect_device()
        else:
            self.connect_device()
    
    def connect_device(self):
        """Connect to the selected device"""
        if self.port_combo.currentText():
            port_name = self.port_combo.currentText().split(" - ")[0]
            if self.serial_comm.connect_to_device(port_name):
                self.serial_comm.start()
    
    def disconnect_device(self):
        """Disconnect from the device"""
        self.serial_comm.disconnect()
        if self.serial_comm.isRunning():
            self.serial_comm.wait()
    
    def handle_connection_status(self, connected: bool, message: str):
        """Handle connection status changes"""
        if connected:
            self.connection_status.setText(f"Connected: {message}")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setText("Disconnect")
            self.send_to_device_btn.setEnabled(True)
            self.send_all_layers_to_device_btn.setEnabled(True)
            self.connected_port = message
            
            print(f"Connected to device: {message}")
            
            # Show config storage location in status
            config_path = self.config_manager.config_dir
            print(f"Config files stored in: {config_path}")
            
            # Add delay before auto-sending to ensure device is ready
            QTimer.singleShot(250, self.auto_send_config)  # 0.25 second delay
            
        else:
            self.connection_status.setText("Not connected")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setText("Connect")
            self.send_to_device_btn.setEnabled(False)
            self.send_all_layers_to_device_btn.setEnabled(False)
            self.connected_port = None
            print("Disconnected from device")
    
    def handle_device_message(self, message: dict):
        """Handle messages received from the device"""
        if message.get("type") == "debug":
            self.statusBar().showMessage(f"Device: {message['message']}")
        else:
            status = message.get("status", "unknown")
            msg = message.get("message", "No message")
            self.statusBar().showMessage(f"Device response: {status} - {msg}")

    def auto_detect_device(self):
        """Start auto-detection in a separate thread"""
        if not self.serial_comm.running:
            # Create worker
            worker = AutoDetectWorker(
                self.get_custom_detection_rules, 
                self.serial_comm.running
            )
            
            # Connect signals
            worker.signals.device_found.connect(self.on_device_found)
            worker.signals.detection_complete.connect(self.on_detection_complete)
            worker.signals.log_message.connect(self.on_log_message)
            
            # Start the worker
            self.thread_pool.start(worker)
        else:
            print("Auto-detect: Serial communication already running")
    
    @pyqtSlot(str)
    def on_device_found(self, port_device):
        """Called when a device is found - runs on main thread"""
        self.select_and_connect_port(port_device)
    
    @pyqtSlot(list)
    def on_detection_complete(self, ports):
        """Called when detection completes - runs on main thread"""
        # Handle completion if needed (update UI, etc.)
        print(f"Detection complete. Found {len(ports)} total ports.")
    
    @pyqtSlot(str)
    def on_log_message(self, message):
        """Called for log messages - runs on main thread"""
        print(message)

    def select_and_connect_port(self, device_name):
        """Select a specific port in the combo box and connect"""
        for i in range(self.port_combo.count()):
            if device_name in self.port_combo.itemText(i):
                self.port_combo.setCurrentIndex(i)
                print(f"Auto-connecting to: {device_name}")
                self.connect_device()
                return True
        return False
        
    def ping_device(self):
        """Send a ping command to the device"""
        if self.serial_comm.running:
            self.serial_comm.send_command({"action": "ping"})
    
    def get_current_keymap(self):
        """Get the current keymap from the device"""
        if self.serial_comm.running:
            self.serial_comm.send_command({"action": "get_current_keymap"})
    
    def edit_key(self, key_index: int):
        """Open dialog to edit a key"""
        current_key = self.current_layers[self.current_layer_index]["keys"][key_index]
        
        dialog = KeySelectorDialog(current_key, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = dialog.selected_key
            self.current_layers[self.current_layer_index]["keys"][key_index] = new_key
            self.key_buttons[key_index].set_key(new_key)
    
    def update_layer_list(self):
        """Update the layer list widget"""
        self.layer_list.clear()
        for i, layer in enumerate(self.current_layers):
            item = QListWidgetItem(layer["name"])
            self.layer_list.addItem(item)
        
        if self.current_layer_index < self.layer_list.count():
            self.layer_list.setCurrentRow(self.current_layer_index)
    
    def switch_layer(self, layer_index: int):
        """Switch to a different layer"""
        if 0 <= layer_index < len(self.current_layers):
            self.current_layer_index = layer_index
            layer = self.current_layers[layer_index]
            
            self.current_layer_label.setText(f"Layer: {layer['name']}")
            
            # Update key buttons
            for i, key in enumerate(layer["keys"]):
                if i < len(self.key_buttons):
                    self.key_buttons[i].set_key(key)
    
    def add_layer(self):
        """Add a new layer"""
        name, ok = QInputDialog.getText(self, "Add Layer", "Layer name:")
        if ok and name:
            new_layer = {"name": name, "keys": ["KC.NO"] * 12}
            self.current_layers.append(new_layer)
            self.update_layer_list()
            self.layer_list.setCurrentRow(len(self.current_layers) - 1)
    
    def rename_layer(self):
        """Rename the current layer"""
        if self.current_layer_index < len(self.current_layers):
            current_name = self.current_layers[self.current_layer_index]["name"]
            name, ok = QInputDialog.getText(self, "Rename Layer", "Layer name:", text=current_name)
            if ok and name:
                self.current_layers[self.current_layer_index]["name"] = name
                self.update_layer_list()
                self.current_layer_label.setText(f"Layer: {name}")
    
    def delete_layer(self):
        """Delete the current layer"""
        if len(self.current_layers) > 1 and self.current_layer_index < len(self.current_layers):
            reply = QMessageBox.question(
                self, "Delete Layer", 
                f"Delete layer '{self.current_layers[self.current_layer_index]['name']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.current_layers[self.current_layer_index]
                if self.current_layer_index >= len(self.current_layers):
                    self.current_layer_index = len(self.current_layers) - 1
                self.update_layer_list()
                self.switch_layer(self.current_layer_index)
    
    def send_current_layer_to_device(self):
        """Send the current layer configuration to the device"""
        if self.serial_comm.running and self.current_layer_index < len(self.current_layers):
            layer = self.current_layers[self.current_layer_index]
            command = {
                "action": "set_keybindings",
                "keybindings": layer["keys"],
                "layer": self.current_layer_index,
                "layer_name": layer["name"]
            }
            self.serial_comm.send_command(command)
            self.statusBar().showMessage(f"Sent layer '{layer['name']}' to device")
            
            # Auto-save current configuration as "default"
            self.auto_save()

    def send_all_layers_to_device(self):
        """Send the all of the layers of the configuration to the device"""
        for i in range(len(self.current_layers)):

            if self.serial_comm.running:
                layer = self.current_layers[i]
                command = {
                    "action": "set_keybindings",
                    "keybindings": layer["keys"],
                    "layer": i,
                    "layer_name": layer["name"]
                }
                self.serial_comm.send_command(command)
                self.statusBar().showMessage(f"Sent layer '{layer['name']}' to device")

    def auto_save(self):
        """Automatically save current configuration"""
        config_name = self.config_combo.currentText()
        config = {
            "layers": self.current_layers,
            "current_layer": self.current_layer_index
        }
        if self.config_manager.save_config(config_name, config):
            # Update the config list
            self.update_config_list()
            # Set the combo box
            if self.config_combo.currentText() != config_name:
                index = self.config_combo.findText(config_name)
                if index >= 0:
                    self.config_combo.setCurrentIndex(index)
    
    def auto_send_config(self):
        """Automatically send default configuration when device connects"""
        print("Sending config to Device")
        if len(self.current_layers) > 0:
            self.send_all_layers_to_device()
        else:
            self.send_current_layer_to_device()

    def update_config_list(self):
        """Update the configuration dropdown"""
        self.config_combo.clear()
        configs = self.config_manager.list_configs()
        self.config_combo.addItems(configs)
    
    def save_configuration(self):
        """Save current configuration"""
        name, ok = QInputDialog.getText(self, "Save Configuration", "Configuration name:")
        if ok and name:
            config = {
                "layers": self.current_layers,
                "current_layer": self.current_layer_index
            }
            if self.config_manager.save_config(name, config):
                self.update_config_list()
                # Set the saved config as current
                index = self.config_combo.findText(name)
                if index >= 0:
                    self.config_combo.setCurrentIndex(index)
                self.statusBar().showMessage(f"Configuration '{name}' saved")
            else:
                QMessageBox.warning(self, "Error", "Failed to save configuration")
    
    def load_configuration(self):
        """Load selected configuration"""
        config_name = self.config_combo.currentText()
        if config_name:
            config = self.config_manager.load_config(config_name)
            if config:
                self.current_layers = config.get("layers", [{"name": "Default", "keys": ["KC.NO"] * 12}])
                self.current_layer_index = config.get("current_layer", 0)
                
                # Ensure current_layer_index is valid
                if self.current_layer_index >= len(self.current_layers):
                    self.current_layer_index = 0
                
                self.update_layer_list()
                self.switch_layer(self.current_layer_index)
                self.statusBar().showMessage(f"Configuration '{config_name}' loaded")
            else:
                QMessageBox.warning(self, "Error", "Failed to load configuration")
    
    def delete_configuration(self):
        """Delete selected configuration"""
        config_name = self.config_combo.currentText()
        if config_name:
            reply = QMessageBox.question(
                self, "Delete Configuration", 
                f"Delete configuration '{config_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.config_manager.delete_config(config_name):
                    self.update_config_list()
                    self.statusBar().showMessage(f"Configuration '{config_name}' deleted")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete configuration")
    
    def new_configuration(self):
        """Create a new configuration"""
        self.current_layers = [{"name": "Default", "keys": ["KC.NO"] * 12}]
        self.current_layer_index = 0
        self.update_layer_list()
        self.switch_layer(0)
        self.statusBar().showMessage("New configuration created")
    
    def load_last_config(self):
        """Load the last used configuration"""
        last_config = self.settings.value("last_config", "")
        if last_config and last_config in self.config_manager.list_configs():
            config = self.config_manager.load_config(last_config)
            if config:
                self.current_layers = config.get("layers", self.current_layers)
                self.current_layer_index = config.get("current_layer", 0)
                
                if self.current_layer_index >= len(self.current_layers):
                    self.current_layer_index = 0
                
                self.update_layer_list()
                self.switch_layer(self.current_layer_index)
                
                # Set the combo box to show the loaded config
                index = self.config_combo.findText(last_config)
                if index >= 0:
                    self.config_combo.setCurrentIndex(index)
        else:
            # Create a default configuration with common keys
            default_layers = [{
                "name": "Default 1", 
                "keys": [
                    "KC.A", "KC.B", "KC.C", "KC.D",
                    "KC.E", "KC.F", "KC.G", "KC.H", 
                    "KC.I", "KC.J", "KC.K", "KC.L"
                ]},
                {
                "name": "Default 2", 
                "keys": [
                    "KC.0", "KC.1", "KC.2", "KC.3",
                    "KC.4", "KC.5", "KC.6", "KC.7", 
                    "KC.8", "KC.9", "KC.ENTER", "KC.BACKSPACE"
                ]
            }]
            
            # Save as default
            default_config = {
                "layers": default_layers,
                "current_layer": 0
            }
            
            if self.config_manager.save_config("default", default_config):
                print("Created and saved default configuration")
                # Apply the newly created config
                self.current_layers = default_layers
                self.current_layer_index = 0
                
                # Update UI
                self.update_layer_list()
                self.switch_layer(self.current_layer_index)
                self.update_config_list()
                
                # Set combo to default
                index = self.config_combo.findText("default")
                if index >= 0:
                    self.config_combo.setCurrentIndex(index)
                

    def debug_list_all_devices(self):
        """Debug method to list all devices with full details"""
        ports = serial.tools.list_ports.comports()
        
        print("\n" + "="*60)
        print("COMPLETE DEVICE LISTING FOR DEBUGGING")
        print("="*60)
        
        if not ports:
            print("No serial ports found!")
            return
        
        for i, port in enumerate(ports):
            print(f"\nDevice {i+1}:")
            print(f"  Port Name: {port.device}")
            print(f"  Description: {port.description}")
            print(f"  Hardware ID: {port.hwid}")
            
            # Try to get additional attributes
            attrs = ['manufacturer', 'product', 'serial_number', 'vid', 'pid', 
                    'location', 'interface', 'subsystem']
            
            for attr in attrs:
                try:
                    value = getattr(port, attr, None)
                    if value is not None:
                        if attr in ['vid', 'pid']:
                            print(f"  {attr.upper()}: 0x{value:04X} ({value})")
                        else:
                            print(f"  {attr.title().replace('_', ' ')}: {value}")
                except:
                    pass
            
            # Check what keywords would match
            description_lower = port.description.lower()
            manufacturer_lower = getattr(port, 'manufacturer', '').lower()
            all_text = f"{description_lower} {manufacturer_lower}"
            
            circuitpython_keywords = [
                'circuitpython', 'feather', 'adafruit', 'micropython', 
                'arduino', 'trinket', 'itsy', 'qtpy', 'metro', 'gemma',
                'pico', 'raspberry pi pico', 'rp2040'
            ]
            
            matching_keywords = [kw for kw in circuitpython_keywords if kw in all_text]
            if matching_keywords:
                print(f"  *** WOULD AUTO-DETECT (matches: {', '.join(matching_keywords)}) ***")
            else:
                print(f"  (No auto-detect keywords found)")
            
            print("-" * 40)
        
        print(f"\nTotal devices: {len(ports)}")
        print("="*60 + "\n")

    def force_connect_selected(self):
        """Force connection to the currently selected port"""
        if self.port_combo.currentText():
            port_name = self.port_combo.currentText().split(" - ")[0]
            print(f"Force connecting to: {port_name}")
            self.connect_device()

    def add_custom_device_detection(self, vid_pid_pairs=None):
        """Add custom device detection rules
        
        Args:
            vid_pid_pairs: List of (VID, PID) tuples for hardware identification
        """

        if vid_pid_pairs:
            print(f"Adding custom VID/PID pairs: {vid_pid_pairs}")
            self.settings.setValue("custom_vid_pids", vid_pid_pairs)

    def get_custom_detection_rules(self):
        """Get custom detection rules from settings"""
        custom_vid_pids = self.settings.value("custom_vid_pids", [])
        return custom_vid_pids
    
    def closeEvent(self, event):
        """Handle application close event"""
        
        # Save last used configuration
        current_config = self.config_combo.currentText()
        if current_config:
            self.settings.setValue("last_config", current_config)
        
        # Disconnect from device
        if self.serial_comm.running:
            self.disconnect_device()
        
        event.accept()


