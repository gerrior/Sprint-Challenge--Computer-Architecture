"""CPU functionality."""

import sys

instructions = {
    '???':  0b00000000,
    'HLT':  0b00000001,
    'LDI':  0b00000010,
    'PUSH': 0b00000101,
    'POP':  0b00000110,
    'PRN':  0b00000111,
    'CALL': 0b00010000,
    'RET':  0b00010001,
    'JMP':  0b00010100,
    'JEQ':  0b00010101,
    'JNE':  0b00010110,
    'CMP':  0b00100111,
    'ADD':  0b00100000,
    'MUL':  0b00100010
}


class CPU:
    """Main CPU class."""
    
    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 0xFF  # x is a list of 25 zeroes
        self.registers = [0] * 0x08
        self.pc = 0     # Program Counter, address of the currently executing instruction
        self.ir = 0     # Instruction Register, contains a copy of the currently executing instruction
        self.mar = 0    # Memory Address Register, holds the memory address we're reading or writing
        self.mdr = 0    # Memory Data Register, holds the value to write or the value just read
        self.fl = 0     # Flags, see below

        self.sp = 0xF4

        self.branch_table = {}
        self.branch_table[instructions['HLT' ]] = self.hlt
        self.branch_table[instructions['LDI' ]] = self.ldi
        self.branch_table[instructions['PUSH']] = self.push
        self.branch_table[instructions['POP' ]] = self.pop
        self.branch_table[instructions['PRN' ]] = self.prn
        self.branch_table[instructions['CALL']] = self.call
        self.branch_table[instructions['RET' ]] = self.ret
        self.branch_table[instructions['JMP' ]] = self.jmp
        self.branch_table[instructions['JEQ' ]] = self.jeq
        self.branch_table[instructions['JNE' ]] = self.jne
        self.branch_table[instructions['CMP' ]] = self.cmp
        self.branch_table[instructions['ADD' ]] = self.add
        self.branch_table[instructions['MUL' ]] = self.mul

    # Register getter methods
    @property
    def r0(self):
        return self.registers[0]
    @property
    def r1(self):
        return self.registers[1]
    @property
    def r2(self):
        return self.registers[2]
    @property
    def r3(self):
        return self.registers[3]
    @property
    def r4(self):
        return self.registers[4]
    @property
    def r5(self):
        return self.registers[5]
    @property
    def r6(self):
        return self.registers[6]
    @property
    def sp(self):
        return self.registers[7]

    # Register setter methods
    @r0.setter
    def r0(self, value):
        self.registers[0] = value
    @r1.setter
    def r1(self, value):
        self.registers[1] = value
    @r2.setter
    def r2(self, value):
        self.registers[2] = value
    @r3.setter
    def r3(self, value):
        self.registers[3] = value
    @r4.setter
    def r4(self, value):
        self.registers[4] = value
    @r5.setter
    def r5(self, value):
        self.registers[5] = value
    @r6.setter
    def r6(self, value):
        self.registers[6] = value
    @sp.setter
    def sp(self, value):
        self.registers[7] = value

    def ram_read(self, mar):
        return self.ram[mar]
    
    def ram_write(self, mar, mdr):
        self.ram[mar] = mdr

    def load(self):
        """Load a program into memory."""

        address = 0

        # Load the program from file
        file = None # If open fails, compiler will complain "local variable 'file' referenced before assignment"
        filename = None # And if second argument is missing
        program = []

        try:
            # filename = sys.argv[1] # This will throw if there is no second argument
            # filename = "examples/mult.ls8"
            # filename = "examples/print8.ls8"
            # filename = "examples/stack.ls8"
            # filename = "examples/call.ls8"
            filename = "sctest.ls8"

            file = open(filename, "r")
            for line in file:
                line = line.split("#", 1) # Find comments
                line = line[0].strip() # Take non-comment portion and trim spaces
                if len(line) == 0: # If there is nothing left...
                    continue 

                byte = int(line, 2)
                program.append(byte)

            if len(program) == 0:
                raise EOFError

        except EOFError:
            print(f"{filename} did not contain a program")
            sys.exit()
        except:
            if filename != None and len(filename) == 0:
                print("Second argument must be filename: python3 ls8.py examples/print.ls8")
            else:
                print(f"Unable to open filename {filename}")
            sys.exit()

        finally:
            if file is not None:
                file.close()

        # Load the program into RAM
        for instruction in program:
            self.ram[address] = instruction
            address += 1


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.registers[reg_a] += self.registers[reg_b]
        elif op == "CMP":
            # If they are equal, set the Equal E flag to 1, otherwise set it to 0.
            if self.registers[reg_a] == self.registers[reg_b]:
                self.fl |= 0x01
            else:
                self.fl &= ~0x01

            # If registerA is greater than registerB, set the Greater-than G flag to 1, otherwise set it to 0.
            if self.registers[reg_a] > self.registers[reg_b]:
                self.fl |= 0x02
            else:
                self.fl &= ~0x02

            # If registerA is less than registerB, set the Less-than L flag to 1, otherwise set it to 0.
            if self.registers[reg_a] < self.registers[reg_b]:
                self.fl |= 0x04
            else:
                self.fl &= ~0x04

        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        while True:
            # Read the memory address that's stored in register PC, and store that result in the Instruction Register.
            self.ir = self.ram_read(self.pc) & 0x3F
            self.branch_table[self.ir]()

            # Advance PC by the highest two order bits
            if self.ir != instructions['CALL'] and self.ir != instructions['RET'] and self.ir != instructions['JMP']:
                self.pc = self.pc + (self.ram_read(self.pc) >> 6) + 1

    def hlt(self):
        sys.exit()

    def ldi(self):
        self.registers[self.ram_read(self.pc + 1) & 0x07] = self.ram_read(self.pc + 2)
        return

    def push(self):
        # Decrement stack pointer
        self.sp -= 1

        # Keep R7 in the range 00-FF
        self.sp &= 0xFF

        # get register value
        reg_num = self.ram_read(self.pc + 1)
        value = self.registers[reg_num]

        # Store in memory
        address_to_push_to = self.sp
        self.ram_write(address_to_push_to, value)

    def pop(self):
        # Get value from RAM
        address_to_pop_from = self.sp
        value = self.ram_read(address_to_pop_from)

        # Store in the given register
        reg_num = self.ram_read(self.pc + 1)
        self.registers[reg_num] = value

        # Increment SP
        self.sp += 1

    def prn(self):
        print(self.registers[self.ram_read(self.pc + 1) & 0x07])
        return 
        
    def call(self):
        # Get address of the next instruction
        return_addr = self.pc + 2

        # Push that on the stack
        self.sp -= 1
        address_to_push_to = self.sp
        self.ram_write(address_to_push_to, return_addr)

        # Set the PC to the subroutine address
        reg_num = self.ram_read(self.pc + 1)
        subroutine_addr = self.registers[reg_num]

        self.pc = subroutine_addr

    def ret(self):
        # Get return address from the top of the stack
        address_to_pop_from = self.sp
        return_addr = self.ram_read(address_to_pop_from)
        self.sp += 1

        # Set the PC to the return address
        self.pc = return_addr

    # Jump to the address stored in the given register
    def jmp(self):
        # Set the PC to the address stored in the given register
        reg_num = self.ram_read(self.pc + 1)
        stored_addr = self.registers[reg_num]

        self.pc = stored_addr

    def jeq(self):
        # If equal flag is set (true), jump to the address stored in the given register.
        if self.fl & 0x01 == True:
            # Set the PC to the address stored in the given register
            reg_num = self.ram_read(self.pc + 1)
            stored_addr = self.registers[reg_num]

            self.pc = stored_addr

    def jne(self):
        # If equal flag is set (true), jump to the address stored in the given register.
        if self.fl & 0x01 == False:
            # Set the PC to the address stored in the given register
            reg_num = self.ram_read(self.pc + 1)
            stored_addr = self.registers[reg_num]

            self.pc = stored_addr

    def cmp(self):
        reg_a = self.ram_read(self.pc + 1)
        reg_b = self.ram_read(self.pc + 2)

        self.alu('CMP', reg_a, reg_b)
        return

    def add(self):
        reg_a = self.ram_read(self.pc + 1)
        reg_b = self.ram_read(self.pc + 2)

        self.alu('ADD', reg_a, reg_b)
        return

    def mul(self):
        self.r0 = self.r0 * self.r1
        return

