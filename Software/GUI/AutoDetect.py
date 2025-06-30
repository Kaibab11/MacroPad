from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import serial.tools.list_ports


class AutoDetectSignals(QObject):
    """Signals for communicating between worker thread and main thread"""
    device_found = pyqtSignal(str)  # Emit port device when found
    detection_complete = pyqtSignal(list)  # Emit list of available ports when done
    log_message = pyqtSignal(str)  # Emit log messages


class AutoDetectWorker(QRunnable):
    """Worker thread for auto-detecting serial devices"""
    
    def __init__(self, get_custom_detection_rules_func, serial_comm_running):
        super().__init__()
        self.signals = AutoDetectSignals()
        self.get_custom_detection_rules = get_custom_detection_rules_func
        self.serial_comm_running = serial_comm_running
        
    @pyqtSlot()
    def run(self):
        """Main worker function - runs in separate thread"""
        try:
            if self.serial_comm_running:
                self.signals.log_message.emit("Auto-detect: Serial communication already running")
                return
                
            ports = serial.tools.list_ports.comports()
            self.signals.log_message.emit(f"Auto-detect: Checking {len(ports)} available ports...")

            # Get saved VID/PIDs
            saved_vid_pids = self.get_custom_detection_rules()

            # Check saved VID/PIDs first
            for port in ports:
                if hasattr(port, 'vid') and hasattr(port, 'pid'):
                    for vid, pid in saved_vid_pids:
                        if port.vid == vid and (pid is None or port.pid == pid):
                            message = f"Auto-detect: Found device by VID/PID: {port.device} - VID:0x{port.vid:04X} PID:0x{port.pid:04X}"
                            self.signals.log_message.emit(message)
                            self.signals.device_found.emit(port.device)
                            return
            
            # Strategy 1: Look for common CircuitPython/Arduino keywords
            circuitpython_keywords = [
                'circuitpython', 'feather', 'adafruit', 'micropython', 
                'arduino', 'trinket', 'itsy', 'qtpy', 'metro', 'gemma',
                'pico', 'raspberry pi pico', 'rp2040'
            ]
            
            for port in ports:
                description_lower = port.description.lower()
                manufacturer_lower = getattr(port, 'manufacturer', '').lower()
                
                # Check description, manufacturer
                all_text = f"{description_lower} {manufacturer_lower}"
                
                for keyword in circuitpython_keywords:
                    if keyword in all_text:
                        message = f"Auto-detect: Found potential device: {port.device} - {port.description}"
                        self.signals.log_message.emit(message)
                        self.signals.device_found.emit(port.device)
                        return
            
            # Strategy 2: Look for specific VID/PID combinations
            known_vid_pids = [
                (0x239A, None),  # Adafruit VID (any PID)
                (0x2E8A, 0x0005), # Raspberry Pi Pico
                (0x1B4F, 0x9206), # SparkFun Pro Micro
                (0x2341, None),   # Arduino VID (any PID)
            ]
            
            for port in ports:
                if hasattr(port, 'vid') and hasattr(port, 'pid'):
                    for vid, pid in known_vid_pids:
                        if port.vid == vid and (pid is None or port.port == pid):
                            message = f"Auto-detect: Found device by VID/PID: {port.device} - VID:0x{port.vid:04X} PID:0x{port.pid:04X}"
                            self.signals.log_message.emit(message)
                            self.signals.device_found.emit(port.device)
                            return
            
            # Strategy 3: Look for USB serial devices (as fallback)
            usb_serial_ports = []
            for port in ports:
                description_lower = port.description.lower()
                if any(term in description_lower for term in ['usb', 'serial', 'com']):
                    message = f"Auto-detect: Found USB serial device (not auto-connecting): {port.device} - {port.description}"
                    self.signals.log_message.emit(message)
                    usb_serial_ports.append(port)
            
            # Send completion signal with all available ports
            if len(ports) > 0:
                self.signals.log_message.emit("Auto-detect: No known devices found. Available ports:")
                for port in ports:
                    self.signals.log_message.emit(f"  {port.device} - {port.description}")
            else:
                self.signals.log_message.emit("Auto-detect: No serial ports found")
                
            self.signals.detection_complete.emit(ports)
            
        except Exception as e:
            self.signals.log_message.emit(f"Auto-detect error: {str(e)}")