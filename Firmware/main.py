import board
import busio
import displayio

from kmk.keys import Key
from macroPad import Kpad
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys
from kmk.modules.holdtap import HoldTap
from kmk.modules.macros import Macros, Press, Release, Tap, Delay

Kpad_oled = True
layer_names = ['NumPad', 'Function', 'Macro']

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



# Custom Layer-with-OLED key class
# class OLEDLayerKey(Key):
#     def __init__(self, hold_layer, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.hold_layer = hold_layer
        
#     def on_press(self, keyboard, *args, **kwargs):
#         # Show next OLED scene
#         if hasattr(keyboard, 'oled'):
#             keyboard.oled._tb_next_scene(keyboard, *args, **kwargs)
#         # Change layer
#         KC.DF(self.hold_layer).on_press(keyboard, *args, **kwargs)
#         return False
        
#     def on_release(self, keyboard, *args, **kwargs):
#         # Show previous OLED scene (return to original)
#         if hasattr(keyboard, 'oled'):
#             keyboard.oled._tb_prev_scene(keyboard, *args, **kwargs)
#         return False


# class OLEDLayerKey(Key):
#     def __init__(self, hold_layer, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.hold_layer = hold_layer
        
#     def on_press(self, keyboard, *args, **kwargs):
#         # Save current scene and show a specific OLED scene
#         if hasattr(keyboard, 'oled'):
#             keyboard.oled._saved_scene = keyboard.oled._current_scene
#             keyboard.oled.set_scene(2)  # sets the scene to end of the three scenes
#         # Change layer
#         KC.DF(self.hold_layer).on_press(keyboard, *args, **kwargs)
#         return False
        
#     def on_release(self, keyboard, *args, **kwargs):
#         # Show previous OLED scene (return to original)
#         if hasattr(keyboard, 'oled'):
#             keyboard.oled.set_scene(keyboard.oled._saved_scene)
#         return False


class OLEDLayerKey(Key):
    def __init__(self, hold_layer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hold_layer = hold_layer
        
    def on_press(self, keyboard, *args, **kwargs):
        # Save current scene and show a specific OLED scene
        if hasattr(keyboard, 'oled'):
            keyboard.oled._saved_scene = keyboard.oled._current_scene
            keyboard.oled.set_scene(2)  # sets the scene to end of the three scenes
        # Change layer
        KC.DF(self.hold_layer).on_press(keyboard, *args, **kwargs)
        return False
        
    def on_release(self, keyboard, *args, **kwargs):
        # Show previous OLED scene (return to original)
        return False
    
# Layers
LYR_NUMPAD = 0
LYR_FUNCTION = 1
LYR_MACRO = 2

TO_NUMPAD = OLEDLayerKey(LYR_NUMPAD)
TO_FUNCTION = OLEDLayerKey(LYR_FUNCTION)
TO_MACRO = OLEDLayerKey(LYR_MACRO)


# Define URL macros for Windows

def open_URL(url):
    return KC.MACRO(
        Press(KC.LGUI),
        Tap(KC.R),
        Release(KC.LGUI),
        Delay(200),
        url,
        Tap(KC.ENTER)
    )

# Create URL macros
OPEN_GITHUB = open_URL("https://github.com")
OPEN_GOOGLE = open_URL("https://google.com")
OPEN_YOUTUBE = open_URL("https://youtube.com")
OPEN_TC3 = open_URL("https://tompkinscortland.edu")

# ---------------- Main macropad maps ---------------- 
# keyboard.keymap = [
#     [
#         KC.KP_7,    KC.KP_8,    KC.KP_9,    KC.NUMLOCK,
#         KC.KP_4,    KC.KP_5,    KC.KP_6,    KC.KP_DOT,
#         KC.KP_1,    KC.KP_2,    KC.KP_3,    KC.HT(KC.KP_0, TO_FUNCTION),
#     ],   # NumPad layer

#     [
#         KC.F1,      KC.F2,      KC.F3,      KC.F4,
#         KC.F5,      KC.F6,      KC.F7,      KC.F8,
#         KC.F9,      KC.F10,     KC.F11,     KC.HT(KC.F12, TO_MACRO),
#     ],   # Function layer

#     [
#         KC.NO,     KC.NO,      KC.NO,      KC.NO,
#         KC.NO,     KC.NO,      KC.NO,      KC.NO,
#         OPEN_GOOGLE,     OPEN_GITHUB,       OPEN_TC3,       KC.HT(OPEN_YOUTUBE, TO_NUMPAD),
#     ]   # Macro layer

# ]

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

    [
        KC.NO,     KC.NO,      KC.NO,      KC.NO,
        KC.NO,     KC.NO,      KC.NO,      KC.NO,
        OPEN_GOOGLE,     OPEN_GITHUB,       OPEN_TC3,       OPEN_YOUTUBE,
    ]   # Macro layer

]



# encoder_handler.map = [ 
#     ((KC.VOLD, KC.VOLU, KC.MUTE),), # NumPad
#     ((KC.UP, KC.DOWN, KC.KP_ENTER),), # Function
#     ((KC.NO, KC.NO, KC.NO),), # Macro
# ]
# ----------------

encoder_handler.map = [ 
    ((KC.OLED_PRV, KC.OLED_NXT, TO_FUNCTION),), # NumPad
    ((KC.OLED_PRV, KC.OLED_NXT, TO_MACRO),), # Function
    ((KC.OLED_PRV, KC.OLED_NXT, TO_NUMPAD),), # Macro
]



if __name__ == '__main__':
   keyboard.go()
