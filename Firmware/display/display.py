"""
This file is adapted from Tonasz's display.py in https://github.com/Tonasz/kmk_firmware/blob/display/kmk/extensions/display.py 
Modification is noted in the subclass below.

Thanks to Tonasz for their contribution.
"""
from supervisor import ticks_ms

import adafruit_displayio_ssd1306
import displayio
import terminalio   
from adafruit_display_text import label

from kmk.extensions import Extension
from kmk.handlers.stock import passthrough as handler_passthrough
from kmk.keys import make_key


class Display(Extension):
    I2C_ADDRESS = 0x3C

    def __init__(
        self, i2c, scenes, *, width=128, height=64, rotation=0, address=I2C_ADDRESS
    ):

        display_bus = displayio.I2CDisplay(i2c, device_address=address)
        self.width = width
        self.height = height
        self._display = adafruit_displayio_ssd1306.SSD1306(
            display_bus, width=width, height=height, rotation=rotation
        )
        self._scenes = scenes
        self._current_scene = 0
        self._saved_scene = 0
        self._redraw_forced = False
        self._asleep = False
        self.polling_interval = 100
        self._last_tick = ticks_ms()

        make_key(
            names=('OLED_NXT',),
            on_press=self._tb_next_scene,
            on_release=handler_passthrough,
        )

        make_key(
            names=('OLED_PRV',),
            on_press=self._tb_prev_scene,
            on_release=handler_passthrough,
        )

        make_key(
            names=('OLED_TOG',),
            on_press=self._tb_toggle,
            on_release=handler_passthrough,
        )

    def during_bootup(self, keyboard):
        self._redraw_forced = True
        for scene in self._scenes:
            scene.initialize(self, keyboard)
        self._display.root_group = self._get_active_scene().scene_group

    def before_matrix_scan(self, keyboard):
        pass

    def after_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        if self._asleep:
            return

        scene = self._get_active_scene()
        now = ticks_ms()
        ready = (
            now - self._last_tick >= scene.polling_interval
        ) and scene.is_redraw_needed(keyboard)
        if self._redraw_forced or ready:
            if self._redraw_forced:
                scene.forced_draw(self, keyboard)
            else:
                scene.draw(self, keyboard)
            self._redraw_forced = False
            self._last_tick = now
        return

    def on_runtime_enable(self, keyboard):
        pass

    def on_runtime_disable(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass

    def _get_active_scene(self):
        if len(self._scenes) > self._current_scene:
            return self._scenes[self._current_scene]

    def _tb_next_scene(self, *args, **kwargs):
        self._current_scene += 1
        if self._current_scene >= len(self._scenes):
            self._current_scene = 0
        self._redraw_forced = True
        self._display.root_group = self._get_active_scene().scene_group

    def _tb_prev_scene(self, *args, **kwargs):
        self._current_scene -= 1
        if self._current_scene < 0:
            self._current_scene = len(self._scenes) - 1
        self._redraw_forced = True
        self._display.root_group = self._get_active_scene().scene_group

    def _tb_toggle(self, *args, **kwargs):
        if self._asleep:
            self._asleep = False
            self._redraw_forced = True
            self._display.wake()
        else:
            self._asleep = True
            self._display.sleep()

    def set_scene(self, scene_num):
        """
        Set the current scene to a specific index number.
        
        Args:
            scene_num: The index of the scene to display.
                       If out of range, it will be clamped to valid values.
        """
        # Ensure scene_num is within valid range
        if scene_num < 0:
            scene_num = 0
        elif scene_num >= len(self._scenes):
            scene_num = len(self._scenes) - 1
            
        # Only change if needed
        if self._current_scene != scene_num:
            self._current_scene = scene_num
            self._redraw_forced = True
            self._display.root_group = self._get_active_scene().scene_group
            
        return self._current_scene  # Return the actual scene number used
    
    # Convenience method to make a key for setting a specific scene
    def make_scene_key(self, scene_num):
        """
        Create a key that will switch directly to the specified scene.
        
        Args:
            scene_num: The scene index to switch to when this key is pressed
            
        Returns:
            A key object that can be used in a keymap
        """
        return make_key(
            names=(f'OLED_SCN{scene_num}',),
            on_press=lambda *args, **kwargs: self.set_scene(scene_num),
            on_release=handler_passthrough,
        )

class DisplayScene:
    '''Abstract class, which all other scenes depends on'''

    polling_interval = 40

    def is_redraw_needed(self, sandbox):
        '''Obligatory check, if we can skip draw logic.
        It was more important when module was based on framebuf.'''
        raise NotImplementedError

    def initialize(self, oled, sandbox):
        '''Called once during_bootup'''
        self.scene_group = None

    def forced_draw(self, oled, sandbox):
        '''Method called when draw is forced, ie when scene is changed.
        It was more important when module was based on framebuf, now maybe obsolete.'''
        self.draw(oled, sandbox)

    def draw(self, oled, sandbox):
        '''Obligatory function, defines main scene logic. Happens not more often than polling_interval.'''
        raise NotImplementedError


class BitmapLogoScene(DisplayScene):
    '''Displays bitmap from storage'''

    def __init__(self, path):
        self._path = path

    def is_redraw_needed(self, sandbox):
        return False

    def initialize(self, oled, sandbox):
        self.scene_group = displayio.Group()

        bitmap = displayio.OnDiskBitmap(self._path)
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        self.scene_group.append(tile_grid)

    def draw(self, oled, sandbox):
        pass


from kmk.extensions.rgb import AnimationModes

class StatusScene(DisplayScene):
    '''Displays basic status info: current layer, default layer, rgb mode (optional) with larger font'''

    last_layer = 0
    last_rgb_mode = 0

    def __init__(
        self, *, layers_names=None, separate_default_layer=False, rgb_ext=None, font_path=None
    ):
        self.layers_names = layers_names
        self.separate_default_layer = separate_default_layer
        self.rgb_ext = rgb_ext
        self.font_path = font_path

    def is_redraw_needed(self, sandbox):
        if self.last_layer != sandbox.active_layers[0]:
            self.last_layer = sandbox.active_layers[0]
            return True
        if self.rgb_ext and self.last_rgb_mode != self.rgb_ext.animation_mode:
            self.last_rgb_mode = self.rgb_ext.animation_mode
            return True
        return False

    def initialize(self, oled, sandbox):
        import terminalio
        from adafruit_display_text import label
        import displayio
        
        # Try to load custom font if provided
        if self.font_path:
            try:
                from adafruit_bitmap_font import bitmap_font
                self.font = bitmap_font.load_font(self.font_path)
            except Exception:
                # Fall back to built-in font if loading fails
                self.font = terminalio.FONT
        else:
            self.font = terminalio.FONT
            
        # Adjust spacing for larger font
        scene_height = 30 if self.rgb_ext is None else 45
        y_pos = max(1, int((oled.height - scene_height) / 2))
        
        self.scene_group = displayio.Group(x=2, y=y_pos)
        
        # Use scale parameter to make font larger without needing a custom font file
        self.upper_layout_text = label.Label(
            terminalio.FONT, 
            text=" " * 20, 
            color=0xFFFFFF,
            scale=1  # Normal size for upper text
        )
        self.scene_group.append(self.upper_layout_text)
        
        self.lower_layout_text = label.Label(
            terminalio.FONT, 
            text=" " * 20, 
            color=0xFFFFFF,
            scale=2  # Double size for layer name
        )
        self.lower_layout_text.y = 12  # Adjusted for 32px height display
        self.scene_group.append(self.lower_layout_text)
        
        if self.rgb_ext is not None:
            self.rgb_text = label.Label(
                terminalio.FONT, 
                text=" " * 20, 
                color=0xFFFFFF,
                scale=1  # Normal size for RGB text
            )
            self.rgb_text.y = 28  # Adjusted for 32px height display
            self.scene_group.append(self.rgb_text)

    def forced_draw(self, oled, sandbox):
        self.draw(oled, sandbox)

    def draw(self, oled, sandbox):
        # add layer text
        if len(sandbox.active_layers) > 1:
            layout_def = sandbox.active_layers[len(sandbox.active_layers) - 1]
            if self.separate_default_layer:
                self.upper_layout_text.text = self._get_layer_name(self.last_layer)
                self.lower_layout_text.text = self._get_layer_name(layout_def)
            else:
                self.upper_layout_text.text = ""
                self.lower_layout_text.text = self._get_layer_name(self.last_layer)
        else:
            self.upper_layout_text.text = ""
            self.lower_layout_text.text = self._get_layer_name(self.last_layer)
        # add RGB mode text
        if self.rgb_ext is not None:
            self.rgb_text.text = f'RGB: {self._get_rgb_mode_name(self.last_rgb_mode)}'

    def _get_layer_name(self, layer_no):
        if self.layers_names is None or layer_no >= len(self.layers_names):
            return f"Layer {layer_no}"
        return self.layers_names[layer_no]

    def _get_rgb_mode_name(self, rgb_mode):
        from kmk.extensions.rgb import AnimationModes

        if rgb_mode == AnimationModes.OFF:
            return 'Off'
        if (
            rgb_mode == AnimationModes.STATIC
            or rgb_mode == AnimationModes.STATIC_STANDBY
        ):
            return 'Static'
        elif rgb_mode == AnimationModes.BREATHING:
            return 'Breathing'
        elif rgb_mode == AnimationModes.RAINBOW:
            return 'Rainbow'
        elif rgb_mode == AnimationModes.BREATHING_RAINBOW:
            return 'Brth.Rnbw'
        elif rgb_mode == AnimationModes.KNIGHT:
            return 'Knight'
        elif rgb_mode == AnimationModes.SWIRL:
            return 'Swirl'
        elif rgb_mode == AnimationModes.USER:
            return 'User'
        else:
            return 'other'



class ShowcaseScene(DisplayScene):
    '''Displays the last key(s) pressed'''

    def __init__(self):
        super().__init__()
        self.last_keys = set()
        self.last_display_text = "None"

    def is_redraw_needed(self, sandbox):
        current_keys = set(self.keyboard.keys_pressed)
        if current_keys != self.last_keys:
            self.last_keys = current_keys
            return True
        return False

    def initialize(self, oled, sandbox):
        from adafruit_display_text import label
        import displayio
        import terminalio

        self.scene_group = displayio.Group()

        # Key display text
        self.key_text = label.Label(
            terminalio.FONT, text="None", color=0xFFFFFF, scale=2
        )
        self.key_text.y = 16
        self.scene_group.append(self.key_text)

    def draw(self, oled, sandbox):
        keys = self.keyboard.keys_pressed
        if keys:
            key_names = [self._get_key_name(k) for k in keys]
            self.last_display_text = ', '.join(key_names)

        self.key_text.text = self.last_display_text

    def _get_key_name(self, key):
        """Extract a readable name from a key object"""

        if hasattr(key, 'code'):
            code = key.code

            # Map A-Z keys (HID codes 4–29)
            if 4 <= code <= 29:
                return chr(code - 4 + ord('A'))

            # Map 1-9, 0 keys (HID codes 30–39)
            if 30 <= code <= 38:
                return chr(code - 30 + ord('1'))
            if code == 39:
                return '0'

            # Map special keys
            special_keys = {
                40: "ENT",
                41: "ESC",
                42: "BSP",
                43: "TAB",
                44: "SPC",
                57: "CAP",
                58: "F1",
                59: "F2",
                60: "F3",
                61: "F4",
                62: "F5",
                63: "F6",
                64: "F7",
                65: "F8",
                66: "F9",
                67: "F10",
                68: "F11",
                69: "F12",
                79: "R→",
                80: "L←",
                81: "D↓",
                82: "U↑",
                83: "NUM",
                89: "1/END",
                90: "2/DOWN",
                91: "3/PG_DOWN",
                92: "4/LEFT",
                93: "5",
                94: "6/RIGHT",
                95: "7/HOME",
                96: "8/UP",
                97: "9/PG_UP",
                98: "0/INS",
                99: "./DEL",
            }

            return special_keys.get(code, f"K{code}")
