import board
import busio
import displayio

import time
from kmk.keys import Key
from macroPad import Kpad
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys
from kmk.modules.holdtap import HoldTap
from kmk.modules.macros import Macros, Press, Release, Tap, Delay
from display.display import Display, DisplayScene
from kmk.modules import Module

Kpad_oled = True
#layer_names = ['NumPad', 'Function', 'Macro']
layer_names = ['NumPad', 'Function']

displayio.release_displays()
i2c = busio.I2C(scl=board.SCL, sda=board.SDA, frequency=400000)

keyboard = Kpad(i2c, layer_names, Kpad_oled)
layers = Layers()
holdtap = HoldTap()
macros = Macros()
encoder_handler = EncoderHandler()
encoder_handler.divisor = 4
keyboard.modules = [layers, encoder_handler, holdtap, macros]
encoder_handler.pins = ((board.D9, board.D10, board.D8,),)
keyboard.extensions.append(MediaKeys())

class KeyDetector(Module):
    def __init__(self):
        pass

    def during_bootup(self, keyboard):
        pass
    
    def before_matrix_scan(self, keyboard):
        pass
    
    def after_matrix_scan(self, keyboard):
        pass
    
    def before_hid_send(self, keyboard):
        # This method is called before HID reports are sent
        pass
    
    def after_hid_send(self, keyboard):
        # This method is called after HID reports are sent  
        pass
    
    def process_key(self, keyboard, key, is_pressed, int_coord):
        if is_pressed:
            keyboard.oled.set_scene(1)
            
        # IMPORTANT: Return the key object, not True/False
        return key

# Usage
key_detector = KeyDetector()
keyboard.modules.append(key_detector)


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
            keyboard.oled.set_scene(2)  # sets the scene to end of the three scenes (Selection Scene)
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
            keyboard.oled.set_scene(2)  # sets the scene to end of the three scenes (Selection Scene)
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

# Define URL macros for Windows

# def open_URL(url):
#     return KC.MACRO(
#         Press(KC.LGUI),
#         Tap(KC.R),
#         Release(KC.LGUI),
#         Delay(200),
#         url,
#         Tap(KC.ENTER)
#     )

# # Create URL macros
# OPEN_GITHUB = open_URL("https://github.com")
# OPEN_GOOGLE = open_URL("https://google.com")
# OPEN_YOUTUBE = open_URL("https://youtube.com")
# OPEN_TC3 = open_URL("https://tompkinscortland.edu")

# ---------------- Main macropad maps ---------------- 

keyboard.keymap = [
    [
        KC.KP_7,    KC.KP_8,    KC.KP_9,    KC.NUMLOCK,
        KC.KP_4,    KC.KP_5,    KC.KP_6,    KC.KP_DOT,
        KC.KP_1,    KC.KP_2,    KC.KP_3,    KC.KP_0,
    ],   # NumPad layer

    [
        KC.F1,      KC.F2,      KC.F3,      KC.F4,
        KC.F5,      KC.F6,      KC.F7,      KC.F8,
        KC.F9,      KC.F10,     KC.F11,     KC.F12,
    ],   # Function layer
]

# keyboard.keymap = [
#     [
#         KC.KP_7,    KC.KP_8,    KC.KP_9,    KC.NUMLOCK,
#         KC.KP_4,    KC.KP_5,    KC.KP_6,    KC.KP_DOT,
#         KC.KP_1,    KC.KP_2,    KC.KP_3,    KC.KP_0,
#     ],   # NumPad layer

#     [
#         KC.F1,      KC.F2,      KC.F3,      KC.F4,
#         KC.F5,      KC.F6,      KC.F7,      KC.F8,
#         KC.F9,      KC.F10,     KC.F11,     KC.F12,
#     ],   # Function layer

#     [
#         KC.NO,     KC.NO,      KC.NO,      KC.NO,
#         KC.NO,     KC.NO,      KC.NO,      KC.NO,
#         OPEN_GOOGLE,     OPEN_GITHUB,       OPEN_TC3,       OPEN_YOUTUBE,
#     ]   # Macro layer
# ]


encoder_handler.map = [ 
    ((SEL_PRV, SEL_NXT, SELECT),), # NumPad
    ((SEL_PRV, SEL_NXT, SELECT),), # Function
]

# encoder_handler.map = [ 
#     ((SEL_PRV, SEL_NXT, SELECT),), # NumPad
#     ((SEL_PRV, SEL_NXT, SELECT),), # Function
#     ((SEL_PRV, SEL_NXT, SELECT),), # Macro
# ]

if __name__ == '__main__':
   keyboard.go()

