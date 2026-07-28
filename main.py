import sys, os
import pygame
import numpy as np
from cpu import Chip8
import tkinter as tk
from tkinter import filedialog

# CONFIGUREATION i dont know how to spell
scale = 15                          # scale pixel size up (64x32 -> 960x480 resolution)
width, height = 64 * scale, 32 * scale
bgColor = (15, 15, 15)            # background color(when pixels are off)
fgColor = (0, 255, 128)           # color when pixel is on
instructionsPerFrame = 10         # cpu instructions per frame. around 10 on the actual chip8

# use a 4x4 grid of users keyboard to replicate the chip8's keypad. o yea, convert to hex since chip8 = hex =0
KEY_MAP = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF,
}

def generateBeep(sample_rate=44100, frequency=440):
    # generate a simple 440 hz beep for stuff
    n_samples = int(sample_rate * 0.1)
    buf = np.zeros((n_samples, 2), dtype=np.int16)
    max_val = 2000
    period = sample_rate // frequency
    for i in range(n_samples):
        val = max_val if (i // (period // 2)) % 2 == 0 else -max_val
        buf[i][0] = val
        buf[i][1] = val
    return pygame.sndarray.make_sound(buf)

def open_file_dialog():
    root = tk.Tk()
    root.withdraw() # Hide empty Tkinter window
    root.attributes("-topmost", True)
    filepath = filedialog.askopenfilename(
        title="Select chip-8 ROM",
        filetypes=[("xhip-8 ROMs", "*.ch8"), ("All Files", "*.*")]
    )
    root.destroy()
    return filepath

def get_example_roms():
    # check in the roms folder for roms. not including testroms in there just yet.
    rom_folder = "roms"
    if not os.path.exists(rom_folder):
        os.makedirs(rom_folder)
    
    return [os.path.join(rom_folder, f) for f in os.listdir(rom_folder) if f.endswith(".ch8")]

def get_test_roms():
    # get test roms for testing emu, keeps them nice and seperate
    test_folder = "testroms"
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)
    
    return [os.path.join(test_folder, f) for f in os.listdir(test_folder) if f.endswith(".ch8")]

def run_menu(screen, font, cycles_per_frame):
    # le menu
    examples = get_example_roms()
    test_roms = get_test_roms()
    
    # build a flat list for smooth arrow-key navigation
    menu_items = []
    for path in examples:
        menu_items.append({'type': 'example', 'path': path, 'label': os.path.basename(path)})
    menu_items.append({'type': 'custom', 'label': 'Open Custom File...'})
    for path in test_roms:
        menu_items.append({'type': 'test', 'path': path, 'label': os.path.basename(path)})
    menu_items.append({'type': 'config', 'label': 'Configuration'})

    selected_idx = 0
    total_options = len(menu_items)

    while True:
        screen.fill((20, 20, 30))
        
        # header
        title = font.render("--- OctoPy MAIN MENU ---", True, (255, 255, 255))
        screen.blit(title, (width // 2 - title.get_width() // 2, 20))

        sub = font.render("UP/DOWN: Navigate | ENTER: Select | ESC: Pause/Menu", True, (180, 180, 180))
        screen.blit(sub, (width // 2 - sub.get_width() // 2, 50))

        # le roms and config
        x_left = 50
        y = 90

        # roms
        screen.blit(font.render("Example ROMs:", True, (0, 255, 128)), (x_left, y))
        y += 25

        if not examples:
            screen.blit(font.render("  (No .ch8 in 'roms/')", True, (140, 140, 140)), (x_left + 15, y))
            y += 25
        else:
            for idx, item in enumerate(menu_items):
                if item['type'] == 'example':
                    color = (255, 200, 0) if idx == selected_idx else (255, 255, 255)
                    prefix = "> " if idx == selected_idx else "  "
                    screen.blit(font.render(f"{prefix}{item['label']}", True, color), (x_left + 15, y))
                    y += 25
        
        # custom rom file 
        custom_idx = [i for i, item in enumerate(menu_items) if item['type'] == 'custom'][0]
        color = (255, 200, 0) if selected_idx == custom_idx else (200, 200, 255)
        prefix = "> " if selected_idx == custom_idx else "  "
        screen.blit(font.render(f"{prefix}{menu_items[custom_idx]['label']}", True, color), (x_left, y))
        y += 26
        y += 10

        # test roms
        screen.blit(font.render("Emulator test ROMS:", True, (0, 200, 255)), (x_left, y))
        y += 25

        if not test_roms:
            screen.blit(font.render("  (No .ch8 in 'testroms/')", True, (140, 140, 140)), (x_left + 15, y))
            y += 25
        else:
            for idx, item in enumerate(menu_items):
                if item['type'] == 'test':
                    color = (255, 200, 0) if idx == selected_idx else (255, 255, 255)
                    prefix = "> " if idx == selected_idx else "  "
                    screen.blit(font.render(f"{prefix}{item['label']}", True, color), (x_left + 15, y))
                    y += 25

        y += 10

        # config
        screen.blit(font.render("Configuration:", True, (255, 128, 0)), (x_left, y))
        y += 25

        config_idx = len(menu_items) - 1
        is_config_selected = (selected_idx == config_idx)
        color = (255, 200, 0) if is_config_selected else (255, 255, 255)
        prefix = "> " if is_config_selected else "  "
        
        cfg_text = font.render(
            f"{prefix}Speed: < {cycles_per_frame} > per frame", 
            True, 
            color
        )
        screen.blit(cfg_text, (x_left + 15, y))

        #tuff keyboard panel
        x_right = 530
        y_ctrl = 90

        # draw a vertical divider line down the middle
        pygame.draw.line(screen, (60, 60, 80), (500, 85), (500, height - 30), 2)

        screen.blit(font.render("KEYPAD MAPPING", True, (255, 200, 0)), (x_right, y_ctrl))
        y_ctrl += 30

        # display kets
        keypad_layout = [
            " CHIP-8      Keyboard",
            "┌───┬───┬───┬───┐",
            "│ 1 │ 2 │ 3 │ C │ -> 1 2 3 4",
            "├───┼───┼───┼───┤",
            "│ 4 │ 5 │ 6 │ D │ -> Q W E R",
            "├───┼───┼───┼───┤",
            "│ 7 │ 8 │ 9 │ E │ -> A S D F",
            "├───┼───┼───┼───┤",
            "│ A │ 0 │ B │ F │ -> Z X C V",
            "└───┴───┴───┴───┘"
        ]

        for line in keypad_layout:
            line_surface = font.render(line, True, (200, 200, 220))
            screen.blit(line_surface, (x_right, y_ctrl))
            y_ctrl += 22

        pygame.display.flip()

        # menu event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_idx = (selected_idx - 1) % total_options
                elif event.key == pygame.K_DOWN:
                    selected_idx = (selected_idx + 1) % total_options
                
                # adjust speed with left right if on that thing
                elif is_config_selected:
                    if event.key == pygame.K_LEFT:
                        cycles_per_frame = max(1, cycles_per_frame - 1)
                    elif event.key == pygame.K_RIGHT:
                        cycles_per_frame = min(100, cycles_per_frame + 1)

                # launch with the selected ROM
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    current_item = menu_items[selected_idx]

                    if current_item['type'] in ('example', 'test'):
                        return current_item['path'], cycles_per_frame

                    elif current_item['type'] == 'custom':
                        filepath = open_file_dialog()
                        if filepath:  # user didn't cancel
                            return filepath, cycles_per_frame


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("OctoPy")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16, bold=True)
    beep = generateBeep()

    # Default speed setting
    cycles_per_frame = 10  

    # Load initial ROM and configuration
    if len(sys.argv) > 1:
        rom_path = sys.argv[1]
    else:
        rom_path, cycles_per_frame = run_menu(screen, font, cycles_per_frame)

    cpu = Chip8()
    cpu.load_rom(rom_path)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # main.py inside the running loop event handling:

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_F1):
                    rom_path, cycles_per_frame = run_menu(screen, font, cycles_per_frame)
                    cpu = Chip8()
                    cpu.load_rom(rom_path)

                elif event.key in KEY_MAP:
                    key = KEY_MAP[event.key]
                    cpu.keypad[key] = True
                    
                    # if waiting for key input, record which key was pressed down
                    if cpu.waiting_for_key and cpu.released_key_wait is None:
                        cpu.released_key_wait = key

            elif event.type == pygame.KEYUP:
                if event.key in KEY_MAP:
                    key = KEY_MAP[event.key]
                    cpu.keypad[key] = False

                    # Only unblock execution when the pressed key is RELEASED
                    if cpu.waiting_for_key and cpu.released_key_wait == key:
                        cpu.v[cpu.key_target_register] = key
                        cpu.waiting_for_key = False
                        cpu.released_key_wait = None

        # Execute configured cycles per frame
        for _ in range(cycles_per_frame):
            cpu.cycle()

        cpu.update_timers()

        if cpu.sound_timer > 0:
            beep.play(-1)
        else:
            beep.stop()

        # Render Display Frame
        screen.fill(bgColor)
        for y in range(32):
            for x in range(64):
                if cpu.display[x + (y * 64)] == 1:
                    pygame.draw.rect(screen, fgColor, (x * scale, y * scale, scale, scale))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()        