"""
While testing the _keys changes I made, I noticed that the "settings" app seemed to crash due to memory getting filled up. 
I guess I2C stuff is more memory intensive than the old methods of getting keyboard input.
Apps crashing / general instability seems to also be an issue with the other PR's. I tested a couple other apps from GetApps with my modified _keys.py file and they seemed to work fine.
My guess is that settings is more memory intenisve thanks to its more complex menus.

This settings script isn't really "production ready", but has some tweaks to memory management that got the settings app working for me. 
"""

import gc
import sys

# garbage Collection immediately
gc.collect()

# displayed initialised first, before other imports to ensure the 64KB Framebuffer gets priority
try:
    from lib.display import Display
    display = Display()
except Exception as e:
    # Logging if this fails
    print(f"CRITICAL: Display Init Failed - {e}")
    with open("crash_display.log", "w") as f:
        sys.print_exception(e, f)
    raise e

# Now, the rest of the imports
try:
    # another gc collect, to clear up any aditional RAM
    gc.collect()
    
    import json
    import os
    import time
    import machine

    # Import UserInput AFTER display is safe
    from lib import userinput
    from lib.hydra import config
    from lib.hydra import menu as hydramenu
    from lib.hydra.i18n import I18n
    from lib.hydra.popup import UIOverlay
    from lib.sdcard import SDCard

    # Speed up CPU
    machine.freq(240_000_000)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Globals ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    _TRANS = const("""[
      {"en": "language", "zh": "语言/Lang", "ja": "言語/Lang"},
      {"en": "volume", "zh": "音量", "ja": "音量"},
      {"en": "ui_color", "zh": "UI颜色", "ja": "UIの色"},
      {"en": "bg_color", "zh": "背景颜色", "ja": "背景色"},
      {"en": "wifi_ssid", "zh": "WiFi名称", "ja": "WiFi名前"},
      {"en": "wifi_pass", "zh": "WiFi密码", "ja": "WiFiパスワード"},
      {"en": "sync_clock", "zh": "同步时钟", "ja": "時計同期"},
      {"en": "24h_clock", "zh": "24小时制", "ja": "24時間制"},
      {"en": "timezone", "zh": "时区", "ja": "タイムゾーン"},
      {"en": "Confirm", "zh": "确认", "ja": "確認"}
    ]""")

    print("Init Input...")
    kb = userinput.UserInput()
    
    config = config.Config()
    I18N = I18n(_TRANS)
    overlay = UIOverlay(i18n=I18N)

    LANGS = ['en', 'zh', 'ja']
    LANGS.sort()

    try:
        sd = SDCard()
        sd.mount()
    except:
        sd = None

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def update_config(caller, value):
        config[caller.text] = value
        config.generate_palette()
        I18N.__init__(_TRANS)
        print(f"config['{caller.text}'] = {value}")

    def discard_conf(caller):
        print("Discard config.")
        display.fill(0)
        display.show()
        time.sleep_ms(10)
        machine.reset()

    def save_conf(caller):
        config.save()
        print("Save config: ", config.config)
        display.fill(0)
        display.show()
        time.sleep_ms(10)
        machine.reset()

    def export_config(caller):
        try:
            os.mkdir('sd/Hydra')
        except OSError: pass

        try:
            with open("sd/Hydra/config.json", "w") as file:
                file.write(json.dumps(config.config))
            overlay.popup("Config exported to 'sd/Hydra/config.json'")
        except OSError as e:
            overlay.error(e)

    def import_config(caller):
        global menu
        try:
            with open("sd/Hydra/config.json") as file:
                config.config.update(json.loads(file.read()))

            config.generate_palette()
            I18N.__init__(_TRANS)

            overlay.popup("Config loaded from 'sd/Hydra/config.json'")
            menu.exit()
            menu = build_menu()

        except Exception as e:
            overlay.error(e)

    def import_export(caller):
        choice = overlay.popup_options(
            ("Back...", "Export to SD", "Import from SD"),
            title="Import/Export config",
            depth=1,
            )
        if choice == "Export to SD":
            export_config(caller)
        elif choice == "Import from SD":
            import_config(caller)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Menu ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    def build_menu() -> hydramenu.Menu:
        menu = hydramenu.Menu(
            esc_callback=discard_conf,
            i18n=I18N,
            )

        menu_def = [
            (hydramenu.ChoiceItem, 'language', {'choices': LANGS, 'instant_callback': update_config}),
            (hydramenu.IntItem, 'volume', {'min_int': 0, 'max_int': 10, 'instant_callback': update_config}),
            (hydramenu.RGBItem, 'ui_color', {'instant_callback': update_config}),
            (hydramenu.RGBItem, 'bg_color', {'instant_callback': update_config}),
            (hydramenu.WriteItem, 'wifi_ssid', {}),
            (hydramenu.WriteItem, 'wifi_pass', {'hide': True}),
            (hydramenu.BoolItem, 'sync_clock', {}),
            (hydramenu.BoolItem, '24h_clock', {}),
            (hydramenu.IntItem, 'timezone', {'min_int': -13, 'max_int': 13}),
        ]

        for i_class, name, kwargs in menu_def:
            menu.append(
                i_class(
                    menu,
                    name,
                    config[name],
                    callback=update_config,
                    **kwargs,
                ))

        menu.append(hydramenu.DoItem(menu, "Import/Export", callback=import_export))
        menu.append(hydramenu.DoItem(menu, "Confirm", callback=save_conf))

        return menu

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    gc.collect()
    print("Starting Menu...")
    menu = build_menu()

    while True:
        menu.main()


except Exception as e:
    #Some extra logging in case settings crashes again
    print(f"\nCRASH DETECTED: {e}")
    try:
        with open("settings_crash.txt", "w") as f:
            sys.print_exception(e, f)
        print("Log saved to settings_crash.txt")
    except:
        print("Could not save log.")
    raise
