import board

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import ShiftRegisterKeys

class Kpad(KMKKeyboard):
    def __init__(
            self, 
            i2c, 
            layer_names, 
            Kpad_oled = False
        ):
        
        super().__init__()
        # create and register the scannerb
        self.matrix = ShiftRegisterKeys(
            # require arguments:
            clock=board.D1,
            data=board.D2,
            latch=board.D0,
            key_count=12,
            value_when_pressed=False,
            # optional arguments with defaults:
            value_to_latch=True, # 74HC165: True, CD4021: False
            interval=0.02, # Matrix sampling interval in ms
            debounce_threshold=1, # Number of samples needed to change state, values greater than 1 enable debouncing. Only applicable for CircuitPython >= 9.2.0
            max_events=64
        )


        self.i2c = i2c
        self.layer_names = layer_names
        self.set_oled(Kpad_oled)


    def set_oled(self, Kpad_oled):
        if Kpad_oled:
            from display.display import Display, BitmapLogoScene, StatusScene
            # Import the new Showcase class
            from display.display import ShowcaseScene  # Make sure to add this to your display.py file
            
            # Add all three scenes
            scenes = [
                BitmapLogoScene("/display/bmp/kpad_v1_0_kPad.bmp"),
                ShowcaseScene(),
                StatusScene(
                    layers_names=self.layer_names, 
                    separate_default_layer=False,
                ),
                
            ]
            for scene in scenes:
                scene.keyboard = self
            # Initialize display with all scenes
            self.oled = Display(self.i2c, scenes, width=128, height=32, rotation=180)
            self.extensions.append(self.oled)


    

    coord_mapping = [

        8,  9,  10, 11,
        4,  5,   6,  7,
        0,  1,   2,  3,
    ]
    
    
