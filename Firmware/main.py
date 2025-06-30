import json
import os
import supervisor
import time
from kmk.keys import KC
import board
import busio
import displayio
import sys

import time
from kmk.keys import Key
from macroPad import Kpad
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys
from kmk.modules.holdtap import HoldTap
from kmk.modules.macros import Macros
from display.display import DisplayScene
from kmk.modules import Module

# Custom Serial Communication Module
class SerialCommandModule(Module):
    def __init__(self):
        super().__init__()
        self.last_check = 0
        self.check_interval = 0.05  # Check every 50ms
        
    def during_bootup(self, keyboard):
        """Called during keyboard initialization"""
        self.keyboard = keyboard
        print("SerialCommandModule initialized")
        
    def before_matrix_scan(self, keyboard):
        """Called before each matrix scan - perfect for serial processing"""
        current_time = time.monotonic()
        if current_time - self.last_check > self.check_interval:
            self.process_serial_command()
            self.last_check = current_time

    def after_matrix_scan(self, keyboard):
        """Called after matrix scan - implement to avoid NotImplementedError"""
        pass
    
    def before_hid_send(self, keyboard):
        """Called before HID report is sent - implement to avoid NotImplementedError"""
        pass
    
    def after_hid_send(self, keyboard):
        """Called after HID report is sent - implement to avoid NotImplementedError"""
        pass
    
    def string_to_keycode(self, key_string):
        """Convert string like 'KC.A' to actual keycode"""
        key_string = key_string.strip()
        if key_string.startswith('KC.'):
            key_name = key_string[3:]
            try:
                keycode = getattr(KC, key_name)
                print(f"Converted '{key_string}' to keycode successfully")
                return keycode
            except AttributeError:
                print(f"Warning: Unknown key '{key_string}', using KC.NO")
                return KC.NO
        else:
            print(f"Warning: Invalid key format '{key_string}', using KC.NO")
            return KC.NO

    def update_keymap_from_bindings(self, keybindings, layer=0):
        """Update the keyboard's keymap with new key bindings"""
        print(f"Updating layer {layer} with {len(keybindings)} key bindings")
        
        new_keycodes = []
        for key_string in keybindings:
            keycode = self.string_to_keycode(key_string)
            new_keycodes.append(keycode)
        
        # Make sure we have enough layers
        while len(self.keyboard.keymap) <= layer:
            self.keyboard.keymap.append([KC.NO] * len(self.keyboard.keymap[0]))
        
        # Update the specific layer
        self.keyboard.keymap[layer] = new_keycodes
        print(f"Keymap layer {layer} updated with {len(new_keycodes)} keys")

    def process_serial_command(self):
        """Process serial commands without blocking"""
        if not supervisor.runtime.serial_bytes_available:
            return
            
        try:
            command_line = sys.stdin.readline()
            
            if not command_line:
                return
                
            command_line = command_line.strip()
            if not command_line:
                return

            print(f"[KMK] Received: {command_line}")

            # Parse JSON
            try:
                command = json.loads(command_line)
            except json.JSONDecodeError as e:
                print(f"[KMK] JSON Error: {str(e)}")
                error_response = {"status": "error", "message": f"Invalid JSON: {str(e)}"}
                print(json.dumps(error_response))
                return

            # Process commands
            action = command.get("action")
            print(f"[KMK] Processing action: {action}")

            if action == "ping":
                print("[KMK] Ping received, sending pong")
                response = {"status": "success", "message": "pong", "timestamp": time.monotonic()}
                print(json.dumps(response))

            elif action == "set_keybindings":
                keybindings = command.get("keybindings", [])
                layer = command.get("layer", 0)
                layer_name = command.get("layer_name")
                
                print(f"[KMK] Setting {len(keybindings)} keybindings on layer {layer}")

                if not keybindings:
                    response = {"status": "error", "message": "No keybindings provided"}
                else:
                    try:
                        self.update_keymap_from_bindings(keybindings, layer)
                        
                        response = {
                            "status": "success",
                            "message": f"Updated {len(keybindings)} keys on layer {layer}",
                            "keybindings_received": keybindings,
                        }
                        print(f"[KMK] Successfully updated keymap")
                    except Exception as e:
                        print(f"[KMK] Error updating keymap: {str(e)}")
                        response = {"status": "error", "message": f"Failed to update keymap: {str(e)}"}

                if len(keyboard.layer_names) <= layer:
                    keyboard.layer_names.extend([None] * (layer - len(keyboard.layer_names) + 1))

                keyboard.layer_names[layer] = layer_name

                print(json.dumps(response))

            elif action == "save_config":
                if hasattr(self.keyboard, 'config_module'):
                    success = self.keyboard.config_module.force_save()
                    if success:
                        response = {"status": "success", "message": "Configuration saved"}
                    else:
                        response = {"status": "error", "message": "Failed to save configuration"}
                else:
                    response = {"status": "error", "message": "Config module not available"}
                print(json.dumps(response))

            elif action == "load_config":
                if hasattr(self.keyboard, 'config_module'):
                    success = self.keyboard.config_module.load_config()
                    if success:
                        response = {"status": "success", "message": "Configuration loaded"}
                    else:
                        response = {"status": "error", "message": "Failed to load configuration"}
                else:
                    response = {"status": "error", "message": "Config module not available"}
                print(json.dumps(response))

            elif action == "get_config_info":
                if hasattr(self.keyboard, 'config_module'):
                    config_info = self.keyboard.config_module.get_config_info()
                    response = {"status": "success", "config_info": config_info}
                else:
                    response = {"status": "error", "message": "Config module not available"}
                print(json.dumps(response))

            elif action == "get_current_keymap":
                try:
                    print("[KMK] Getting current keymap")
                    keymap_strings = []
                    for layer_idx, layer in enumerate(self.keyboard.keymap):
                        layer_strings = []
                        for keycode in layer:
                            layer_strings.append(str(keycode))
                        keymap_strings.append(layer_strings)

                    response = {
                        "status": "success",
                        "keymap": keymap_strings,
                        "layers": len(self.keyboard.keymap)
                    }
                except Exception as e:
                    print(f"[KMK] Error getting keymap: {str(e)}")
                    response = {"status": "error", "message": f"Failed to get keymap: {str(e)}"}

                print(json.dumps(response))

            else:
                print(f"[KMK] Unknown action: {action}")
                response = {"status": "error", "message": f"Unknown action: {action}"}
                print(json.dumps(response))

        except Exception as e:
            print(f"[KMK] Command processing error: {str(e)}")
            error_response = {"status": "error", "message": f"Command processing error: {str(e)}"}
            print(json.dumps(error_response))

# Initialize hardware and modules
layer_names = ["temp"]
displayio.release_displays()
i2c = busio.I2C(scl=board.SCL, sda=board.SDA, frequency=400000)
Kpad_oled = True

keyboard = Kpad(i2c, layer_names, Kpad_oled)
layers = Layers()
holdtap = HoldTap()
macros = Macros()
encoder_handler = EncoderHandler()
encoder_handler.divisor = 4

# Add our custom serial module
serial_module = SerialCommandModule()

# Add all modules to keyboard
keyboard.modules = [layers, encoder_handler, holdtap, macros, serial_module]

encoder_handler.pins = ((board.D9, board.D10, board.D8,),)
keyboard.extensions.append(MediaKeys())

class InactivityDetector(Module):
    def __init__(self, timeout_seconds=10):
        self.timeout_seconds = timeout_seconds
        self.last_activity_time = time.monotonic()
        self.inactivity_triggered = False
    
    def during_bootup(self, keyboard):
        # Store reference to self in keyboard for easy access
        keyboard.inactivity_detector = self
    
    def before_matrix_scan(self, keyboard):
        current_time = time.monotonic()
        seconds_inactive = current_time - self.last_activity_time
        
        if seconds_inactive >= self.timeout_seconds and not self.inactivity_triggered:
            self.on_inactivity(keyboard)
            self.inactivity_triggered = True
    
    def after_matrix_scan(self, keyboard):
        pass
    
    def before_hid_send(self, keyboard):
        pass
    
    def after_hid_send(self, keyboard):
        pass
    
    def process_key(self, keyboard, key, is_pressed, int_coord):
        if is_pressed:
            self.reset_timer()
        return key
    
    def reset_timer(self):
        """Public method to reset the inactivity timer"""
        self.last_activity_time = time.monotonic()
        self.inactivity_triggered = False
    
    def on_inactivity(self, keyboard):
        print("No activity for {} seconds!".format(self.timeout_seconds))

        keyboard.oled.set_scene(0)
        

inactivity_detector = InactivityDetector(timeout_seconds=10)
keyboard.modules.append(inactivity_detector)


class OLEDLayerKey():
    def __init__(self, *args, **kwargs):
        super().__init__()
        
    def on_press(self, keyboard, *args, **kwargs):

        if hasattr(keyboard, 'inactivity_detector'):
            keyboard.inactivity_detector.reset_timer()

        # Save current scene and show a specific OLED scene
        if hasattr(keyboard, 'oled'):
            keyboard.oled.set_scene(1)  # sets the scene to end of the two scenes (Selection Scene)
        # Change layer
        if DisplayScene._current_layer != keyboard.active_layers[0]:
            KC.DF(DisplayScene._current_layer).on_press(keyboard, *args, **kwargs) 
        return False
        
    def on_release(self, keyboard, *args, **kwargs):
        active_scene = keyboard.oled._get_active_scene()
        if active_scene:
            active_scene.forced_draw(keyboard.oled, keyboard)
        
        return False


class selection_NXT_layer():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_press(self, keyboard, *args, **kwargs):

        if hasattr(keyboard, 'inactivity_detector'):
            keyboard.inactivity_detector.reset_timer()

        # Save current scene and show a specific OLED scene
        if hasattr(keyboard, 'oled'):
            keyboard.oled.set_scene(1)  # sets the scene to end of the three scenes (Selection Scene)
        # Change layer
        
        if DisplayScene._current_layer < len(keyboard.keymap) - 1:
            DisplayScene._current_layer += 1
        else:
            DisplayScene._current_layer = 0
        return False
        
    def on_release(self, keyboard, *args, **kwargs):
        return False

class selection_PRV_layer():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_press(self, keyboard, *args, **kwargs):

        if hasattr(keyboard, 'inactivity_detector'):
            keyboard.inactivity_detector.reset_timer()

        # Save current scene and show a specific OLED scene
        if hasattr(keyboard, 'oled'):
            keyboard.oled.set_scene(2)  # sets the scene to end of the three scenes (Selection Scene)
        # Change layer
        if DisplayScene._current_layer == 0:
            DisplayScene._current_layer = len(keyboard.keymap) - 1
        else:
            DisplayScene._current_layer -= 1
        return False
        
    def on_release(self, keyboard, *args, **kwargs):
        return False


SELECT = OLEDLayerKey()
SEL_NXT = selection_NXT_layer()
SEL_PRV = selection_PRV_layer()


# === DEFAULT KEYMAP ===
keyboard.keymap = [
    [
        KC.A,    KC.B,    KC.C,     # Row 1
        KC.D,    KC.E,    KC.F,     # Row 2
        KC.G,    KC.H,    KC.I,     # Row 3
        KC.J,    KC.K,    KC.L,     # Row 4
    ]
]

encoder_handler.map = [ 
    ((SEL_PRV, SEL_NXT, SELECT),), # NumPad
    ((SEL_PRV, SEL_NXT, SELECT),), # Function
]

# Let KMK handle the main loop - serial processing happens in before_matrix_scan
if __name__ == '__main__':
    
    keyboard.go()
    