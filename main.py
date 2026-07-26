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

def run_menu(screen, font, cycles_per_frame):
    # le config menu on boot
    examples = get_example_roms()
    selected_idx = 0
    # menu items: list of example ROMs + 1 settinges option
    total_options = len(examples) + 1  

    while True:
        screen.fill((20, 20, 30))
        
        # header
        title = font.render("--- OctoPy MAIN MENU ---", True, (255, 255, 255))
        screen.blit(title, (width // 2 - title.get_width() // 2, 30))

        sub = font.render("UP/DOWN: Navigate | ENTER: Select ROM", True, (180, 180, 180))
        screen.blit(sub, (width // 2 - sub.get_width() // 2, 65))

        # le rom selector
        y = 110
        section_title = font.render("Select ROM:", True, (0, 255, 128))
        screen.blit(section_title, (80, y))
        y += 30

        if not examples:
            no_roms = font.render("No .ch8 files found in 'roms/' folder.", True, (255, 100, 100))
            screen.blit(no_roms, (100, y))
            y += 30

        for idx, rom_path in enumerate(examples):
            color = (255, 200, 0) if idx == selected_idx else (255, 255, 255)
            prefix = "> " if idx == selected_idx else "  "
            text = font.render(f"{prefix}{os.path.basename(rom_path)}", True, color)
            screen.blit(text, (100, y))
            y += 30

        # config
        y += 15
        config_title = font.render("Configuration:", True, (0, 255, 128))
        screen.blit(config_title, (80, y))
        y += 30

        config_idx = len(examples)
        is_config_selected = (selected_idx == config_idx)
        
        color = (255, 200, 0) if is_config_selected else (255, 255, 255)
        prefix = "> " if is_config_selected else "  "
        
        cfg_text = font.render(
            f"{prefix}Instructions / Frame: < {cycles_per_frame} >  (LEFT/RIGHT to adjust)", 
            True, 
            color
        )
        screen.blit(cfg_text, (100, y))

        pygame.display.flip()

        # handle Menu Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_idx = (selected_idx - 1) % total_options
                elif event.key == pygame.K_DOWN:
                    selected_idx = (selected_idx + 1) % total_options
                
                # adjust cycles per frame when config setting is highlighted
                elif is_config_selected:
                    if event.key == pygame.K_LEFT:
                        cycles_per_frame = max(1, cycles_per_frame - 1)
                    elif event.key == pygame.K_RIGHT:
                        cycles_per_frame = min(100, cycles_per_frame + 1)

                # Select ROM
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if selected_idx < len(examples):
                        return examples[selected_idx], cycles_per_frame


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("CHIP-8 Emulator")
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

            elif event.type == pygame.KEYDOWN:
                # Return to menu to swap ROM or change speed
                if event.key in (pygame.K_ESCAPE, pygame.K_F1):
                    rom_path, cycles_per_frame = run_menu(screen, font, cycles_per_frame)
                    cpu = Chip8()
                    cpu.load_rom(rom_path)

                elif event.key in KEY_MAP:
                    key = KEY_MAP[event.key]
                    cpu.keypad[key] = True
                    if cpu.waiting_for_key:
                        cpu.v[cpu.key_target_register] = key
                        cpu.waiting_for_key = False

            elif event.type == pygame.KEYUP:
                if event.key in KEY_MAP:
                    key = KEY_MAP[event.key]
                    cpu.keypad[key] = False

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