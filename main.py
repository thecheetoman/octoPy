import sys
import pygame
import numpy as np
from cpu import Chip8

# CONFIGUREATION i dont know how to spell
scale = 15                          # scale pixel size up (64x32 -> 960x480 resolution)
width, height = 64 * scale, 32 * scale
bgColor = (15, 15, 15)            # background color(when pixels are off)
fgColor = (0, 255, 128)           # color when pixel is on
instructionsPerFrame = 1          # cpu instructions per frame. allows to speed up game

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

def main():
    # check if the user provided a rom or stinky =(
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_rom.ch8>")
        sys.exit(1)

    #initialize pygame and mixer
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("OctoPy")
    clock = pygame.time.Clock()

    beep = generateBeep()

    # initialize cpu and load the rom from command line argument
    cpu = Chip8()
    cpu.load_rom(sys.argv[1])

    running = True
    while running:
        # user input handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_MAP:
                    key = KEY_MAP[event.key]
                    cpu.keypad[key] = True

                    # resume CPU if waiting for a key press (Opcode FX0A)
                    if cpu.waiting_for_key:
                        cpu.v[cpu.key_target_register] = key
                        cpu.waiting_for_key = False

            elif event.type == pygame.KEYUP:
                if event.key in KEY_MAP:
                    key = KEY_MAP[event.key]
                    cpu.keypad[key] = False

        # handle cpu cycles
        for _ in range(instructionsPerFrame):
            cpu.cycle()

        # update cpu timers
        cpu.update_timers()
        
        if cpu.sound_timer > 0:
            beep.play(-1)  # loop beep audio if timer is active
        else:
            beep.stop()

        # screen updating logic
        screen.fill(bgColor)
        
        for y in range(32):
            for x in range(64):
                # Check pixel state in flat display array
                if cpu.display[x + (y * 64)] == 1:
                    pygame.draw.rect(
                        screen,
                        fgColor,
                        (x * scale, y * scale, scale, scale)
                    )

        pygame.display.flip()

        # lock emulator frame rate to 60 FPS
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()        