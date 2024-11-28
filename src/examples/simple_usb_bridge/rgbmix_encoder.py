from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles
import random
class Encoder():

    CYCLE = [ 1, 1, 0, 0 ]

    # number of cycles at the edges of transitions vulnerable to bouncing
    # % chance of a bounce within the edges
    def __init__(self, dut, clk, a, b, clocks_per_phase = 20, noise_cycles = 5, noise_chance = 0.5):
        # inputs
        self.dut = dut
        self.clk = clk
        self.a = a
        self.b = b

        self.a.value = 0
        self.b.value = 0

        # internals
        self.cycle = 0
        self.clocks_per_phase = clocks_per_phase
        self.noise_chance = noise_chance
        self.noise_cycles = noise_cycles
        self.a_phase = 3
        self.b_phase = 2
        self.last_a_phase = 3
        self.last_b_phase = 2
        self.a_edge = 0
        self.b_edge = 0

    def set_clocks_per_phase(self, clocks_per_phase):
        self.clocks_per_phase = clocks_per_phase

    async def update(self, incr = 1):
        await ClockCycles(self.clk, 1)
        self.cycle += 1 
        if self.cycle % self.clocks_per_phase == 0:
            # advance a phase
            self.a_phase = (self.a_phase + incr) % len(Encoder.CYCLE)
            self.b_phase = (self.b_phase + incr) % len(Encoder.CYCLE)

            # if a transition just happened, make a note of where we are for triggering noisy edges
            if Encoder.CYCLE[self.a_phase] != Encoder.CYCLE[self.last_a_phase]:
                self.a_edge = self.cycle
            
            if Encoder.CYCLE[self.b_phase] != Encoder.CYCLE[self.last_b_phase]:
                self.b_edge = self.cycle 

            self.last_a_phase = self.a_phase
            self.last_b_phase = self.b_phase

        # set encoder inputs
        self.a.value = Encoder.CYCLE[self.a_phase]
        self.b.value = Encoder.CYCLE[self.b_phase]
        # self.dut.dump_state()

        # randomly generate noise at edges
        if (self.cycle - self.a_edge) < self.noise_cycles and random.random() < self.noise_chance:
            self.a.value = random.randint(0, 1)
        if (self.cycle - self.b_edge) < self.noise_cycles and random.random() < self.noise_chance:
            self.b.value = random.randint(0, 1)

