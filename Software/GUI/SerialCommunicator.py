import json
import threading
import time
import serial
from PyQt6.QtCore import QThread, pyqtSignal

class SerialCommunicator(QThread):
    """Handle serial communication with the macropad in a separate thread"""
    
    message_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False
        self.command_queue = []
        self.lock = threading.Lock()
        
    def connect_to_device(self, port_name: str) -> bool:
        """Connect to the specified serial port"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            self.serial_port = serial.Serial(
                port_name, 
                baudrate=115200, 
                timeout=0.1,
                write_timeout=1.0
            )
            time.sleep(2)  # Give device time to initialize
            self.running = True
            self.connection_status_changed.emit(True, port_name)
            return True
        except Exception as e:
            self.connection_status_changed.emit(False, f"Error: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from the device"""
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connection_status_changed.emit(False, "Disconnected")
    
    def send_command(self, command: dict):
        """Queue a command to be sent to the device"""
        with self.lock:
            self.command_queue.append(command)
    
    def run(self):
        """Main communication loop"""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                # Send queued commands
                with self.lock:
                    if self.command_queue:
                        command = self.command_queue.pop(0)
                        command_json = json.dumps(command) + '\n'
                        self.serial_port.write(command_json.encode())
                        self.serial_port.flush()
                
                # Read responses
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode().strip()
                    if line:
                        try:
                            response = json.loads(line)
                            self.message_received.emit(response)
                        except json.JSONDecodeError:
                            # Handle non-JSON debug messages
                            if line.startswith('[KMK]'):
                                debug_msg = {"type": "debug", "message": line}
                                self.message_received.emit(debug_msg)
                
                self.msleep(50)  # 50ms polling interval
                
            except Exception as e:
                if self.running:  # Only emit error if we're still supposed to be running
                    self.connection_status_changed.emit(False, f"Communication error: {str(e)}")
                break
