
import random
from font import FONTSET

class Chip8:
    def __init__(self):
        # RAM will be stored in this. the chip8 has a grand total of 4096 bytes of ram(RAM! GET HIMM)
        self.memory = bytearray(4096)

        # The Chip8 has 16 registers
        self.v = bytearray(16)

        # this is a register used to hold memory location
        self.i = 0

        # this is the program counter, which points to the current memory instruction
        # chip8 programs should load into ram at 0x200(512 in decimal form), the beginning 
        # ram area is used to contain chip8 interpreter.
        self.pc = 0x200

        # store return addresses when entering functions
        self.stack = []

        # timers all derement at 60hz, which is equivalent to 60 times per second
        self.delay_timer = 0  # used for chip8 delays
        self.sound_timer = 0  # will play a fixed tone when greater than 0

        # this is the display buffer, the chip 8 has a 64 x 32 pixel screen.
        # monochrome display, so 1 = on 0 = off
        self.display = [0] * (64 * 32)

        # this is the container for the keypad. true = key pressed. Planning to use a 4 x 4 chunk of keyboard for this
        self.keypad = [False] * 16

        # key wait state, this is used in instruction FX0A, which pauses the cpu until something is pressed
        self.waiting_for_key = False
        self.key_target_register = 0

        # Load font sprites into memory reserve area starting at address 0x050.
        # load font sprites into the memory, starting at the address of 0x050 
        for idx, byte in enumerate(FONTSET):
            self.memory[0x050 + idx] = byte

    def load_rom(self, filepath: str):
        # simple function to load a .chip8(rom) file
        with open(filepath, "rb") as f:
            rom_data = f.read()
            for idx, byte in enumerate(rom_data):
                self.memory[0x200 + idx] = byte

    def cycle(self):
        # this function executes a singular cpu cycle
        # fetch code -> decode(FTC reference and figure out what to do) -> execute
        # check if waiting for a keystroke. else keep on going lil cpu!
        if self.waiting_for_key:
            return

        #this is the first step in a cpu instruction: fetch the instruction (woah)
        # they are 2 bytes long, so we combine them after shifting 8 by 8 bits.
        # this is to prevent 0x12 + 0x34 from being 0x46, we want 0x1234
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]

        # Advance Program Counter by 2 bytes to point to the next instruction.
        self.pc += 2

        # extract variables commonly used across opcodes:
        x   = (opcode & 0x0F00) >> 8  # 2nd digit: index of register Vx
        y   = (opcode & 0x00F0) >> 4  # 3rd digit: index of register Vy
        n   =  opcode & 0x000F        # 4th digit: 4-bit constant (nibble)
        nn  =  opcode & 0x00FF        # Last 2 digits: 8-bit constant (byte)
        nnn =  opcode & 0x0FFF        # Last 3 digits: 12-bit memory address

        # get the highest hexadecimal digit, so we know what instruction it is
        op_category = opcode & 0xF000

        # execution part(hella elif statements =0)

        if op_category == 0x0000:
            if opcode == 0x00E0:
                # 00E0: clear the display screen
                self.display = [0] * (64 * 32)
            elif opcode == 0x00EE:
                # 00EE: return from a subroutine (pop return address off stack)
                self.pc = self.stack.pop()

        elif op_category == 0x1000:
            # 1NNN: jump to address NNN
            self.pc = nnn

        elif op_category == 0x2000:
            # 2NNN: call subroutine at NNN
            self.stack.append(self.pc)  # Remember return address
            self.pc = nnn               # Jump to subroutine

        elif op_category == 0x3000:
            # 3XNN: skip next instruction if register Vx == NN
            if self.v[x] == nn:
                self.pc += 2

        elif op_category == 0x4000:
            # 4XNN: skip next instruction if register Vx != NN
            if self.v[x] != nn:
                self.pc += 2

        elif op_category == 0x5000:
            # 5XY0: skip next instruction if register Vx == register Vy
            if self.v[x] == self.v[y]:
                self.pc += 2

        elif op_category == 0x6000:
            # 6XNN: set register Vx to byte NN
            self.v[x] = nn

        elif op_category == 0x7000:
            # 7XNN: add byte NN to register Vx (ignores overflow)
            self.v[x] = (self.v[x] + nn) & 0xFF

        elif op_category == 0x8000:
            # arithmatic and bitwise logical operations
            sub_op = opcode & 0x000F

            if sub_op == 0x0:
                # 8XY0: set Vx = Vy
                self.v[x] = self.v[y]
            elif sub_op == 0x1:
                # 8XY1: set Vx = Vx OR Vy
                self.v[x] |= self.v[y]
            elif sub_op == 0x2:
                # 8XY2: set Vx = Vx AND Vy
                self.v[x] &= self.v[y]
            elif sub_op == 0x3:
                # 8XY3: set Vx = Vx XOR Vy
                self.v[x] ^= self.v[y]
            elif sub_op == 0x4:
                # 8XY4: set Vx = Vx + Vy, set VF = 1 if overflow occurred
                total = self.v[x] + self.v[y]
                self.v[x] = total & 0xFF
                self.v[0xF] = 1 if total > 255 else 0
            elif sub_op == 0x5:
                # 8XY5: set Vx = Vx - Vy, set VF = 1 if NO borrow occurred
                flag = 1 if self.v[x] >= self.v[y] else 0
                self.v[x] = (self.v[x] - self.v[y]) & 0xFF
                self.v[0xF] = flag
            elif sub_op == 0x6:
                # 8XY6: shift Vx right by 1. Store dropped bit in VF
                flag = self.v[x] & 0x1
                self.v[x] >>= 1
                self.v[0xF] = flag
            elif sub_op == 0x7:
                # 8XY7: sey Vx = Vy - Vx, set VF = 1 if NO borrow occurred
                flag = 1 if self.v[y] >= self.v[x] else 0
                self.v[x] = (self.v[y] - self.v[x]) & 0xFF
                self.v[0xF] = flag
            elif sub_op == 0xE:
                # 8XYE: shift Vx left by 1. Store dropped bit in VF
                flag = (self.v[x] & 0x80) >> 7
                self.v[x] = (self.v[x] << 1) & 0xFF
                self.v[0xF] = flag

        elif op_category == 0x9000:
            # 9XY0: skip next instruction if register Vx != Vy
            if self.v[x] != self.v[y]:
                self.pc += 2

        elif op_category == 0xA000:
            # ANNN: set Index Register I to address NNN
            self.i = nnn

        elif op_category == 0xB000:
            # BNNN: jump to address NNN + register V0
            self.pc = nnn + self.v[0]

        elif op_category == 0xC000:
            # CXNN: set Vx = (Random Byte) AND NN
            self.v[x] = random.randint(0, 255) & nn

        elif op_category == 0xD000:
            # DXYN: draw sprite at coordinate (Vx, Vy) with width 8 pixels and height N pixels.
            vx = self.v[x] % 64
            vy = self.v[y] % 32
            self.v[0xF] = 0  # reset collision flag

            for row in range(n):
                sprite_byte = self.memory[self.i + row]
                pixel_y = vy + row
                if pixel_y >= 32:
                    break  # stop drawing if sprite runs off screen bottom

                for col in range(8):
                    pixel_x = vx + col
                    if pixel_x >= 64:
                        break  # stop row drawing if sprite runs off screen right

                    # check if bit 'col' inside the sprite byte is set to 1
                    if (sprite_byte & (0x80 >> col)) != 0:
                        idx = pixel_x + (pixel_y * 64)
                        # if pixel is already set, turn it off (XOR logic gate type shii) and mark collision flag
                        if self.display[idx] == 1:
                            self.v[0xF] = 1
                        self.display[idx] ^= 1

        elif op_category == 0xE000:
            if nn == 0x9E:
                # EX9E: skip next instruction if key stored in Vx is PRESSED
                if self.keypad[self.v[x]]:
                    self.pc += 2
            elif nn == 0xA1:
                # EXA1: skip next instruction if key stored in Vx is NOT PRESSED
                if not self.keypad[self.v[x]]:
                    self.pc += 2

        elif op_category == 0xF000:
            if nn == 0x07:
                # FX07: set Vx = value of Delay Timer
                self.v[x] = self.delay_timer
            elif nn == 0x15:
                # FX15: set Delay Timer = value of Vx
                self.delay_timer = self.v[x]
            elif nn == 0x18:
                # FX18: set Sound Timer = value of Vx
                self.sound_timer = self.v[x]
            elif nn == 0x1E:
                # FX1E: add Vx to Index Register I
                self.i = (self.i + self.v[x]) & 0xFFFF
            elif nn == 0x29:
                # FX29: set I = address of font character sprite corresponding to value in Vx
                self.i = 0x050 + (self.v[x] * 5)
            elif nn == 0x0A:
                # FX0A: pause CPU execution until a key is pressed; store key index in Vx
                self.waiting_for_key = True
                self.key_target_register = x
            elif nn == 0x33:
                # FX33: store binary-coded decimal (BCD) value of Vx into memory locations I, I+1, I+2
                self.memory[self.i]     = self.v[x] // 100        # Hundreds digit
                self.memory[self.i + 1] = (self.v[x] // 10) % 10  # Tens digit
                self.memory[self.i + 2] = self.v[x] % 10          # Ones digit
            elif nn == 0x55:
                # FX55: store registers V0 through Vx in memory starting at index address I
                for idx in range(x + 1):
                    self.memory[self.i + idx] = self.v[idx]
            elif nn == 0x65:
                # FX65: read registers V0 through Vx from memory starting at index address I
                for idx in range(x + 1):
                    self.v[idx] = self.memory[self.i + idx]

    def update_timers(self):
        # update timers. this script doesnt do this though the gui app will.... eventually... when i remember to make it... if i remmeber to make it...
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1