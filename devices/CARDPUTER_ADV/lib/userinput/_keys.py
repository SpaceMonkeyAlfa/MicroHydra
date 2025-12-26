from machine import Pin, I2C
import micropython


KC_SHIFT = const(61)
KC_FN = const(65)

"""
The keymaps here looks very different from the one's used by other PR's by CarnitaShredder and TheOddCell that implement the I2C keyboard. 
This is because I've tried to base my I2C processing logic on the M5Stack Cardputer library for Arduino IDE
"""

KEYMAP = {
    0: 'OPT',
    1: 'SHIFT',
    2: 'q',
    3: '1',
    4: 'CTL',
    5: 'FN',
    6: 'TAB',
    7: '`',
    10: 'z',
    11: 's',
    12: 'e',
    13: '3',
    14: 'ALT',
    15: 'a',
    16: 'w',
    17: '2',
    20: 'c',
    21: 'f',
    22: 't',
    23: '5',
    24: 'x',
    25: 'd',
    26: 'r',
    27: '4',
    30: 'b',
    31: 'h',
    32: 'u',
    33: '7',
    34: 'v',
    35: 'g',
    36: 'y',
    37: '6',
    40: 'm',
    41: 'k',
    42: 'o',
    43: '9',
    44: 'n',
    45: 'j',
    46: 'i',
    47: '8',
    50: '.',
    51: ';',
    52: '[',
    53: '-',
    54: ',',
    55: 'l',
    56: 'p',
    57: '0',
    60: 'SPC',
    61: 'ENT',
    62: '\\',
    63: 'BSPC',
    64: '/',
    65: "'",
    66: ']',
    67: '=',
}

KEYMAP_SHIFT = {
    0: 'OPT',
    1: 'SHIFT',
    2: 'Q',
    3: '!',
    4: 'CTL',
    5: 'FN',
    6: 'TAB',
    7: '~',
    10: 'Z',
    11: 'S',
    12: 'E',
    13: '#',
    14: 'ALT',
    15: 'A',
    16: 'W',
    17: '@',
    20: 'C',
    21: 'F',
    22: 'T',
    23: '%',
    24: 'X',
    25: 'D',
    26: 'R',
    27: '$',
    30: 'B',
    31: 'H',
    32: 'U',
    33: '&',
    34: 'V',
    35: 'G',
    36: 'Y',
    37: '^',
    40: 'M',
    41: 'K',
    42: 'O',
    43: '(',
    44: 'N',
    45: 'J',
    46: 'I',
    47: '*',
    50: '>',
    51: ':',
    52: '{',
    53: '_',
    54: '<',
    55: 'L',
    56: 'P',
    57: ')',
    60: 'SPC',
    61: 'ENT',
    62: '|',
    63: 'BSPC',
    64: '?',
    65: '"',
    66: '}',
    67: '+',
}

KEYMAP_FN = {
    0: 'OPT',
    1: 'SHIFT',
    2: 'q',
    3: 'F1',
    4: 'CTL',
    5: 'FN',
    6: 'TAB',
    7: 'ESC',
    10: 'z',
    11: 's',
    12: 'e',
    13: 'F3',
    14: 'ALT',
    15: 'a',
    16: 'w',
    17: 'F2',
    20: 'c',
    21: 'f',
    22: 't',
    23: 'F5',
    24: 'x',
    25: 'd',
    26: 'r',
    27: 'F4',
    30: 'b',
    31: 'h',
    32: 'u',
    33: 'F7',
    34: 'v',
    35: 'g',
    36: 'y',
    37: 'F6',
    40: 'm',
    41: 'k',
    42: 'o',
    43: 'F9',
    44: 'n',
    45: 'j',
    46: 'i',
    47: 'F8',
    50: 'DOWN',
    51: 'UP',
    52: '[',
    53: '_',
    54: 'LEFT',
    55: 'l',
    56: 'p',
    57: 'F10',
    60: 'SPC',
    61: 'ENT',
    62: '\\',
    63: 'DEL',
    64: 'RIGHT',
    65: "'",
    66: ']',
    67: '=',
}

MOD_KEYS = const(('ALT', 'CTL', 'FN', 'SHIFT', 'OPT'))
ALWAYS_NEW_KEYS = const(())

# TCA8418 Hardware Configuration

KB_I2C_ADDR = 0x34
REG_CFG = 0x01
REG_INT_STAT = 0x02
REG_KEY_LCK_EC = 0x03
REG_KEY_EVENT_A = 0x04
REG_KP_GPIO1 = 0x1D
REG_KP_GPIO2 = 0x1E
REG_KP_GPIO3 = 0x1F

class Keys:
    """Keys class for Cardputer ADV (TCA8418 I2C)."""

    main_action = "ENT"
    secondary_action = "SPC"
    aux_action = "G0"
    ext_dir_dict = {';':'UP', ',':'LEFT', '.':'DOWN', '/':'RIGHT', '`':'ESC'}

    def __init__(self, **kwargs):
        self._key_list_buffer = []  
        self._pressed_keys_set = set() 
        
        # Setup G0 button
        self.G0 = Pin(0, Pin.IN, Pin.PULL_UP)

        # Initialize I2C (SDA=G8, SCL=G9 for StampS3). Uses the second controller (1) instead of (0) which seemed to help with stability
        self.i2c = I2C(1, scl=Pin(9), sda=Pin(8), freq=400000)
        self.kb_present = False

        try:
            self.i2c.writeto(KB_I2C_ADDR, b'')
            

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_KP_GPIO1, b'\x7F')

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_KP_GPIO2, b'\xFF')

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_KP_GPIO3, b'\x00')

            self.i2c.writeto_mem(KB_I2C_ADDR, REG_CFG, b'\x01')
            
            # clear any stuck interrupts
            self.i2c.writeto_mem(KB_I2C_ADDR, REG_INT_STAT, b'\x03')
            
            self.kb_present = True
        except Exception as e:
            print(f"Keyboard Init Error: {e}")

        self.key_state = []

    def _tca_to_address(self, tca_val):
        """
        Converts a TCA8418 raw key code into the Python 'key_address'.
        Logic from the C++ 'remap' and 'IOMatrix' logic from the M5Stack Cardputer library for Arduino IDE.
        """
        key_id = (tca_val & 0x7F) - 1
        tca_row = key_id // 10
        tca_col = key_id % 10

        # logical_x Cardputer columns (0..13)
        # logical_y:  Cardputer rows (0..3)
        lx = (tca_row * 2) + (1 if tca_col > 3 else 0)
        ly = tca_col % 4
        
        col_idx = lx // 2
        
        # If lx is even, Upper IO MUX (rows 4-7)
        # If lx is odd, Lower IO MUX (rows 0-3)
        is_upper = (lx % 2 == 0)
        i_base = 4 if is_upper else 0
        
        #The Arduino IDE library uses uses y = 3 - (i % 4)

        row_idx = i_base + (3 - ly)
        
        # Final Python Address: (Column * 10) + Row
        address = (col_idx * 10) + row_idx
        return address

    def scan(self):
        """Reads I2C events and updates the list of held keys."""
        if not self.kb_present:
            return []
            
        try:
            # Loop max 15 times, then give up if those fail.
            for _ in range(15):
                # Check INT_STAT 
                int_stat_buf = self.i2c.readfrom_mem(KB_I2C_ADDR, REG_INT_STAT, 1)
                int_stat = int_stat_buf[0]
                
                if not (int_stat & 0x01):
                    break 
                
                # Check how many events
                count_buf = self.i2c.readfrom_mem(KB_I2C_ADDR, REG_KEY_LCK_EC, 1)
                count = count_buf[0] & 0x0F
                
                if count == 0:
                    # Clear INT manually if count = 0
                    self.i2c.writeto_mem(KB_I2C_ADDR, REG_INT_STAT, b'\x01')
                    break
                
                # Read event from i2c
                evt_buf = self.i2c.readfrom_mem(KB_I2C_ADDR, REG_KEY_EVENT_A, 1)
                val = evt_buf[0]
                
                # Process the event
                is_press = (val & 0x80) > 0
                address = self._tca_to_address(val)
                
                if is_press:
                    self._pressed_keys_set.add(address)
                else:
                    if address in self._pressed_keys_set:
                        self._pressed_keys_set.remove(address)
            
                # Clear INT  flagg
                self.i2c.writeto_mem(KB_I2C_ADDR, REG_INT_STAT, b'\x01')

        except Exception:
            pass

        # Convert set to list
        self._key_list_buffer = list(self._pressed_keys_set)
        return self._key_list_buffer

    @staticmethod
    def ext_dir_keys(keylist) -> list:
        for idx, key in enumerate(keylist):
            if key in Keys.ext_dir_dict:
                keylist[idx] = Keys.ext_dir_dict[key]
        return keylist

    def get_pressed_keys(self, *, force_fn=False, force_shift=False) -> list:
        """
        Get a readable list of currently held keys.
        """
        self.scan()
        self.key_state = []

        if self.G0.value() == 0:
            self.key_state.append("G0")

        if not self._key_list_buffer and not self.key_state:
            return self.key_state

        #FN / Shift logic
        fn_active = force_fn
        shift_active = force_shift

        for code in self._key_list_buffer:
            base_char = KEYMAP.get(code)
            if base_char == 'SHIFT':
                shift_active = True
            elif base_char == 'FN':
                fn_active = True

        if fn_active:
            for keycode in self._key_list_buffer:
                if keycode in KEYMAP_FN:
                    self.key_state.append(KEYMAP_FN[keycode])
        elif shift_active:
            for keycode in self._key_list_buffer:
                if keycode in KEYMAP_SHIFT:
                    self.key_state.append(KEYMAP_SHIFT[keycode])
        else:
            for keycode in self._key_list_buffer:
                if keycode in KEYMAP:
                    self.key_state.append(KEYMAP[keycode])

        return self.key_state
