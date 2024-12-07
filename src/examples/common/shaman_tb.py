'''
Created on Oct 28, 2023

Adapted from https://github.com/psychogenic/tt05-shaman/blob/main/src/test.py
@author: Pat Deegan
@copyright: Copyright (C) 2023 Pat Deegan, https://psychogenic.com
'''

from microcotb.utils import get_sim_time
import microcotb as cocotb
from microcotb.clock import Clock
from microcotb.triggers import ClockCycles # RisingEdge, FallingEdge, Timer, 
import hashlib
import random 

cocotb.set_runner_scope(__name__)

GateLevelTest = False
DoLongLongTest = False
DoEverySizeBlockTest = False


TestMessage = b'if I was a cat, I might be fat but--unlike a cat--I wear a hat, and am in the end not (so) fat... however ' * 3
TestMessageIndy = b'There was a young man of Killarney Who was chock full of what is called blarney'
TestMessageAllSizesTemplate = b'Awake. Shake dreams from your hair, my pretty child, my sweet one. ' \
                      b'Choose the day and choose the sign of your day. The day\'s divinity. First thing you see.'

LongLongMessage = b'1234567890'*30


def hexdigest(m):
    return ''.join(map(lambda i:f'{int(i):02x}', m.digest()))


def padMessage(origmsg: bytearray) -> bytearray:
    '''
        This shows how a message is padded with the
        special 0x80 lastbyte, zeros as required, 
        and a file 8 bytes with the original message
        length.
        The zeros are used to ensure there are a 
        multiple of 64 bytes sent over in the end.
    '''
    if isinstance(origmsg, str):
        message = bytearray(origmsg, 'ascii')
    elif isinstance(origmsg, bytes):
        message = bytearray(origmsg)
    elif not isinstance(origmsg, bytearray):
        raise TypeError
    else:
        message = bytearray(origmsg) # deep copy

    length = len(message) * 8 # orig length, need it below
    message.append(0x80) 
    while (len(message) * 8 + 64) % 512 != 0:
        message.append(0)
    
    message += length.to_bytes(8, 'big')
    
    assert (len(message) * 8) % 512 == 0, "Padding did not complete properly!"
    return message



@cocotb.test()
async def test_sacraficiallamb(dut):
    '''
        This is just a quick & dirty way to ensure
        gate level tests pass.  Need better
        poweronreset state management, ugh.
    
    '''
    
    dut._log.info("start sacrificial lamb--reset all state")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    dut.parallelLoading.value = 0
    dut.resultNext.value = 0
    dut.clockinData.value = 0
    await ClockCycles(dut.clk, 500)

        
    
@cocotb.test()
async def test_unblocked(dut):
    '''
        This is how you'd normally use the system
         * pad the data 
         * start a new digest
         * clock in all the (padded) input
         * wait until outputReady
         * extract the result
    '''
    letters = 'abcdefghijklmnopqrstuvwxyz'
    result_str = ''.join(random.choice(letters) for _i in range(42))

    origMessage =  TestMessageAllSizesTemplate + b' Also: randomsuffix-' + bytearray(result_str, 'ascii')
    
    
    # pad me, amadeus
    paddedMsg = padMessage(origMessage)
    dut._log.info(f'Process msg: {origMessage}')
    dut._log.debug("start")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    # reset everything
    await reset(dut)
    
    # start a new digest
    await startNewDigest(dut)
    
    dut._log.info('Set up for parallel loads')
    dut.parallelLoading.value = 1
    
    # for every byte in the padded message
    # put byte on datain
    # check that busy is LOW, wait if required
    # clock clockinData, so it get added to the stack
    
    numTotalTicks = 0
    for byteVal in paddedMsg:
        
        dut._log.debug('Setting data byte and clockin')
        # set the data input
        dut.databyteIn.value = byteVal 
        
        numBusyTicks = await waitNotBusy(dut)
        
        
        # clock that data in
        dut.clockinData.value = 1
        await ClockCycles(dut.clk, 2) # in parallel mode, this needs to be 2, 1 ok in sync
        dut._log.debug('Setting clockin LOW')
        dut.clockinData.value = 0
        await ClockCycles(dut.clk, 1)
        
        numTotalTicks += (numBusyTicks + 3)
        
        
    # then, wait until ~busy and outputReady
    numTotalTicks += await waitNotBusy(dut)
    numTotalTicks += await waitOutputReady(dut)
        
    
    await ClockCycles(dut.clk, 2)  # changing this to 1 causes skips/fails
    
    # read in the result
    calculated = await readinResult(dut)
    
    m = hashlib.sha256()
    m.update(origMessage)
    hashval = hexdigest(m)
    dut._log.info('SHA256 RESULT:')
    dut._log.info(f'received:    {calculated}')
    dut._log.info(f'hashlib/ext: {hashval}')
    
    assert hashval == calculated, f"For message: '{origMessage}'\ncalculated {calculated} should == {hashval}"
    
    
    
@cocotb.test()
async def test_synchronous(dut):
    
    msg = TestMessageIndy
    
    if GateLevelTest:
        if len(msg) > 64+5:
            dut._log.info('Truncating message for gatelevel test')
            msg = msg[:64+5]
            
    dut._log.info("start")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    message_blocks = message_to_blocks(msg)
    dut._log.info(f'Encoding "{msg}" using spinlock')
    dut.parallelLoading.value = 0
    await ClockCycles(dut.clk, 2)
    await processMessageBlocks(dut, msg, message_blocks, mode_parallel=False)
    

@cocotb.test()
async def testBothSHA(dut):
    
    if GateLevelTest:
        dut._log.info('Too heavy for gate level test, skip.')
        return
        
    dut._log.info("start")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    message_blocks = message_to_blocks(TestMessage)
    dut._log.info(f'Encoding {TestMessage} using SPINLOCK')
    dut.parallelLoading.value = 0
    start_time = get_sim_time('us')
    await processMessageBlocks(dut, TestMessage, message_blocks, mode_parallel=False)
    dut._log.info(f'Took {get_sim_time("us") - start_time}us to do')
    
    await ClockCycles(dut.clk, 20)
    dut.parallelLoading.value = 1
    await ClockCycles(dut.clk, 20)
    dut._log.info(f'Encoding {TestMessage} using PARALLEL loads')
    start_time = get_sim_time('us')
    await processMessageBlocks(dut, TestMessage, message_blocks, mode_parallel=True)
    dut._log.info(f'Took {get_sim_time("us") - start_time}us to do')
        

@cocotb.test()
async def test_parallel(dut):
    
    if GateLevelTest:
        dut._log.info('Too heavy for gate level test, skip.')
        return
        
    dut._log.info("start")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    msg = TestMessageIndy
    
    
        
    
    message_blocks = message_to_blocks(msg)
    dut._log.info(f'Encoding "{msg}" using parallel')
    dut.parallelLoading.value = 1
    await ClockCycles(dut.clk, 2)
    
    await processMessageBlocks(dut, msg, message_blocks, mode_parallel=True)


@cocotb.test(skip=not DoLongLongTest)
async def test_bigtext(dut):
    
    if GateLevelTest:
        dut._log.info('Too heavy for gate level test, skip.')
        return
        
    dut._log.info(f"starting test 10MHz clock ({len(LongLongMessage)} bytes)")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    
    if not DoLongLongTest:
        dut._log.info('Skipping longlong test')
        return 
    
    msg = LongLongMessage
    message_blocks = message_to_blocks(msg)
    dut._log.info(f'Encoding Lotsabytes using parallel')
    dut.parallelLoading.value = 1
    await ClockCycles(dut.clk, 2)
    
    await processMessageBlocks(dut, msg, message_blocks, mode_parallel=True)


@cocotb.test(skip=not DoEverySizeBlockTest)
async def test_everysizeblock(dut):
    
    dut._log.info("start")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    if not DoEverySizeBlockTest:
        dut._log.info("Skipping 'everysize' test")
        return 
        
    dut.parallelLoading.value = 1
    await ClockCycles(dut.clk, 2)
    
    msgTemplate = TestMessageAllSizesTemplate * 10
    
    for i in range(1, 64*3):
        msg = msgTemplate[0:i]
        message_blocks = message_to_blocks(msg)
        
        dut._log.info(f'Test {i+1}: {msg}')
        numTicks = await processMessageBlocks(dut, msg, message_blocks, quietLogging=True, mode_parallel=True)
        dut._log.info(f'OK (in {numTicks} ticks)')


BoundaryTestString= """Dear Sir stroke Madam, I am writing to inform you of a fire which has broken out on the premises of... no, that's too formal.Dear Sir stroke Madam.Fire... exclamation mark.Fire... exclamation mark. Help me... exclamation mark. 123 Carrendon Road.Looking forward to hearing from you."""

# calculated hashes for substrings, using sha256sum
BoundaryTests = [# "D"
(1,
    '3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43'),
# "De"
(2,
    'e2eca64bd73ce8672efc022c65d7a599f8bbfc1e216a6fe9d08f82e20061d618'),
# "Dea"
(3,
    '063fa0eb89944a26ec1e68b58f0e67cdd254d3cae5aea28daa71bca2c8fa1947'),
# "Dear Sir stroke Madam, I am writing to inform you of a fire wh"
(62,
    '90fc0a268f8b81bc6c317ea4748f0a1692f60d73302c3df8596dd1e71953f402'),
# "Dear Sir stroke Madam, I am writing to inform you of a fire whi"
(63,
    '3ae03b684b8ef073b8cb60e4cf540ed80a7d5e4eb395da1117c7142c2df113f7'),
# "Dear Sir stroke Madam, I am writing to inform you of a fire whic"
(64,
    'b1caae86680b14f40ec3ebee88c961a79d60d4670a52e08f8f14dc1aaf3a028a'),
# "Dear Sir stroke Madam, I am writing to inform you of a fire which"
(65,
    'a82bce2cb69472e018d823b990b93a7e201e3291a45c58d92c24a88b06d96bed'),
# "Dear Sir stroke Madam, I am writing to inform you of a fire which has broken out on the premises of... no, that's too formal.De"
(127,
    'f68340bd496c1f9c082887a3196d38bcae855f1effed51629788b976cff1e4f6'),
# "Dear Sir stroke Madam, I am writing to inform you of a fire which has broken out on the premises of... no, that's too formal.Dea"
(128,
    'baaf138cab10cd71049a70dc377ecead43d26645d885621ac0bffe290f18637e'),
# "Dear Sir stroke Madam, I am writing to inform you of a fire which has broken out on the premises of... no, that's too formal.Dear"
(129,
    '0dd8ceed479109f82ef65c3eb51ca9eedf3d013445c8124ce521638f63f520b6'),
]


@cocotb.test()
async def test_should_fail(dut):
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    assert dut.rst_n.value == 0, f"rst_n ({dut.rst_n.value}) == 0"
        
        

@cocotb.test(skip=DoEverySizeBlockTest)
async def test_boundaryblocksizes(dut):
    dut._log.info("start")
    clock = Clock(dut.clk, 1, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    
    if DoEverySizeBlockTest:
        dut._log.info("Skipping: doing 'everysize' test instead")
        return 
        
    testsToRun = BoundaryTests
    if GateLevelTest:
        dut._log.info('Too heavy for gate level test, shorten.')
        testsToRun = [BoundaryTests[2]]
        return
        
    dut.parallelLoading.value = 1
    await ClockCycles(dut.clk, 2)
    
    
    for tst in testsToRun:
        sz = tst[0]
        msg = BoundaryTestString[0:sz]
        dut._log.info(f"Size {sz}: '{msg}'")
        message_blocks = message_to_blocks(msg)
        await processMessageBlocks(dut, msg, message_blocks, quietLogging=False, hashval=tst[1],  mode_parallel=True)
        
        

# ################ Utilities #################### #
async def reset(dut):
    # reset
    dut._log.debug("rst_n low")
    dut.rst_n.value = 0
    
    dut.databyteIn.value = 0
    dut.parallelLoading.value = 0
    dut.resultNext.value = 0
    dut.start.value = 0
    dut.resultNext.value = 0
    
    await ClockCycles(dut.clk, 2)
    dut._log.debug("rst_n high")
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10) 
    
    
    dut._log.info("reset done")
    
    await startNewDigest(dut)
    
    
    
async def startNewDigest(dut):
    dut._log.debug('New message start')
    dut.start.value = 1
    await ClockCycles(dut.clk, 2)
    dut.start.value = 0
    await ClockCycles(dut.clk, 2)


async def waitNotBusy(dut):
    numBusyTicks = 0
    isBusy = dut.busy.value
    while isBusy and numBusyTicks < 1000:
        dut._log.debug('busy')
        await ClockCycles(dut.clk, 1)
        #dut._log.info('busy2')
        isBusy = dut.busy.value
        numBusyTicks += 1
        assert numBusyTicks < 1000, f"Busy too long: numticks {numBusyTicks}"
    return numBusyTicks

async def waitOutputReady(dut):
    numReadyTicks = 0
    outputReady = dut.resultReady.value
    while not outputReady:
        dut._log.debug('Check resultReady')
        outputReady = dut.resultReady.value
        await ClockCycles(dut.clk, 1)
        numReadyTicks += 1
        assert numReadyTicks < 1000, f"outputrdy too long: numticks {numReadyTicks}"
        
    return numReadyTicks


def message_to_blocks(message: bytearray) -> bytearray:
    """chunk message bytearray into 512 bit block(s) with any required padding"""

    if isinstance(message, str):
        message = bytearray(message, 'ascii')
    elif isinstance(message, bytes):
        message = bytearray(message)
    elif not isinstance(message, bytearray):
        raise TypeError

    # Padding
    length = len(message) * 8 # len(message) is number of BYTES!!!
    message.append(0x80)
    
    while (len(message) * 8 + 64) % 512 != 0:
        message.append(0x00)

    message += length.to_bytes(8, 'big') # pad to 8 bytes or 64 bits

    assert (len(message) * 8) % 512 == 0, "Padding did not complete properly!"

    # Parsing
    blocks = [] # contains 512-bit chunks of message
    for i in range(0, len(message), 64): # 64 bytes is 512 bits
        blocks.append(message[i:i+64])
        
    return blocks
    
    

async def loadMessageBlock(dut, message_block, quietLogging:bool = True, mode_parallel:bool = True):
    # print(f' handle message block (f{message_block}) len {len(message_block)}')
    t = 0
    numSlots = len(message_block)/4
    numBusyTicks = 0
    numTotalTicks = 0
    if not quietLogging:
        dut._log.info('Load msg block')
        dut._log.debug(f'contents: {message_block}')
    while t < numSlots:
        #print(message_block[t])
        dut._log.debug(f'Slot {t}')
        i = int.from_bytes(bytes(message_block[t*4:(t*4)+4]), 'big')
        for btIdx in range(4):
            daShift = ((3-btIdx)*8)
            byteVal = (i & (0xff << daShift)) >> daShift
            
            numBusyTicks = 0
            isBusy = dut.busy.value
            while isBusy and numBusyTicks < 1000:
                dut._log.debug('busy')
                await ClockCycles(dut.clk, 1)
                isBusy = dut.busy.value
                numBusyTicks += 1
                assert numBusyTicks < 1000, f"Busy for {numBusyTicks} ticks"
            
            dut._log.debug('Setting data byte and clockin')
            dut.databyteIn.value = byteVal 
            dut.clockinData.value = 1
            if mode_parallel:
                await ClockCycles(dut.clk, 2) # in parallel mode, this needs to be 2, 1 ok in sync
            else:
                await ClockCycles(dut.clk, 1) # in parallel mode, this needs to be 2, 1 ok in sync
                
            dut._log.debug('Setting clockin LOW')
            dut.clockinData.value = 0
            await ClockCycles(dut.clk, 1)
            
            numTotalTicks += (numBusyTicks + 3)
            
        dut._log.debug('u32 done')
        isBusy = dut.busy.value
        if (t < numSlots - 1 ) and isBusy:
            dut._log.info("hum busy")
        
        t += 1
        
    if not quietLogging:
        dut._log.info(f'loadblock done in {numTotalTicks}')
    return numTotalTicks 
        


async def readinResult(dut) -> str:
    
    results_bytes = []
    for _i in range(32):
        results_bytes.append(dut.resultbyteOut.value)
        dut.resultNext.value = 1
        await ClockCycles(dut.clk, 2)  # changing this to 1 causes skips/fails
        dut.resultNext.value = 0
        await ClockCycles(dut.clk, 1)
        
    
    calculated = ''.join(map(lambda i: f'{int(i):02x}', results_bytes))
    return calculated

async def processMessageBlocks(dut, encodedMsg, message_blocks, quietLogging=True, hashval:str = None, 
                               mode_parallel:bool=True):
    dut._log.debug('Start message HIGH')
    dut.start.value = 1
    await ClockCycles(dut.clk, 1)
    dut._log.debug('Start message LOW')
    dut.start.value = 0
    await ClockCycles(dut.clk, 1)
    tickWaitCountTotal = 0
    
    loadTicksTotal = 0
    
    for block in message_blocks:
        
        dut._log.debug(f'Process block')
        loadTicksTotal += await loadMessageBlock(dut, block)
        dut._log.debug(f'tot ticks now {loadTicksTotal}')
        
        await ClockCycles(dut.clk, 1)
        
        tickWaitCountTotal += await waitNotBusy(dut)
        if not mode_parallel:
            tickWaitCountTotal += await waitOutputReady(dut)
    
    avgWaitTickCount = int(tickWaitCountTotal/len(message_blocks))
    if not quietLogging:
        dut._log.info(f'Spent avg of {avgWaitTickCount} waiting on processing, per block')
        dut._log.info(f'All blocks input, waiting until done...')
        
    # await ClockCycles(dut.clk, 1)
    dut._log.info('Wait for result')
    
    tickWaitCountTotal += await waitOutputReady(dut)
    if not quietLogging:
        dut._log.info(f'Done after {tickWaitCountTotal}')
        
    await ClockCycles(dut.clk, 2)  # changing this to 1 causes skips/fails
    
    calculated = await readinResult(dut)
    if hashval is None or not len(hashval):
        m = hashlib.sha256()
        
        m.update(encodedMsg)
        hashval = hexdigest(m)
    
    if not quietLogging:
        dut._log.info('SHA256 RESULT:')
    dut._log.info(f'rcvd digest: {calculated}')
    if not quietLogging:
        dut._log.info(f'hashlib/ext: {hashval}')
    
    assert hashval == calculated, f"For message: '{encodedMsg}'\ncalc {calculated} should == {hashval}"
    
    
    return  tickWaitCountTotal
    
       
import examples.fpga_io.tt_dut as tt_dut

class ShamanDUT(tt_dut.TinyTapeoutDUT):
    '''
        Rather than setup neptune-specific signal mappings on the FPGA,
        doing it here allows a single I/O-through SUB FPGA to work with 
        *any* tiny tapeout project.
        
        So the base class DUT will expose ui_in, uo_out etc for all projects,
        and here we create named attributes using bits and slices from those
        standard signals, that are used in the testbench.
    '''
    def __init__(self, serial_port:str):
        super().__init__(serial_port, 'SHAMAN', auto_discover=True)

        self.databyteIn = self.ui_in
        self.resultbyteOut = self.uo_out
        
        self.resultReady = self.new_bit_attribute('resultReady', self.uio_out, 0)
        self.beginProcessingDataBlock = self.new_bit_attribute('beginProcessingDataBlock', self.uio_out, 1)
        
        self.parallelLoading = self.new_bit_attribute('parallelLoading', self.uio_in, 2)
        self.resultNext = self.new_bit_attribute('resultNext', self.uio_in, 3)
        
        self.busy = self.new_bit_attribute('busy', self.uio_out, 4)
        self.processingReceivedDataBlock = self.new_bit_attribute('processingReceivedDataBlock', self.uio_out, 5)
        self.start = self.new_bit_attribute('start', self.uio_in, 6)
        self.clockinData = self.new_bit_attribute('clockinData', self.uio_in, 7)
        
        self.oe_bidir_setting = 0b11001100
        

import logging
def main(ser_port:str='/dev/ttyACM0'):
    from microcotb.time.value import TimeValue
    TimeValue.ReBaseStringUnits = True # want pretty strings

    logging.basicConfig(level=logging.INFO)
    
    dut = ShamanDUT(ser_port)
    dut.is_monitoring = True
    dut.sync_change_dumps =  True
    
    dut.uio_oe.value = dut.oe_bidir_setting
    
    runner = cocotb.get_runner(__name__)
    dut._log.info(f"enabled shaman project. Will test with\n{runner}")
    runner.test(dut)

if __name__ == '__main__':
    main()