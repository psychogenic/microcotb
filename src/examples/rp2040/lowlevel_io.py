'''
Created on Dec 13, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import machine

@micropython.native
def write_ui_in_byte(val):
    # dump_portset('ui_in', val)
    # low level machine stuff
    # move the value bits to GPIO spots
    # low nibble starts at 9 | high nibble at 17 (-4 'cause high nibble)
    val = ((val & 0xF) << 9) | ((val & 0xF0) << 17-4)
    # xor with current GPIO values, and mask to keep only input bits
    # 0x1E1E00 == 0b111100001111000000000 so GPIO 9-12 and 17-20
    val = (machine.mem32[0xd0000010] ^ val) & 0x1E1E00
    # val is now be all the input bits that have CHANGED:
    # writing to 0xd000001c will flip any GPIO where a 1 is found
    machine.mem32[0xd000001c] = val
    
@micropython.native
def read_ui_in_byte():
    # just read the high and low nibbles from GPIO and combine into a byte
    return ( (machine.mem32[0xd0000004] & (0xf << 17)) >> (17-4)) | ((machine.mem32[0xd0000004] & (0xf << 9)) >> 9)

@micropython.native
def write_uio_byte(val):
    # dump_portset('uio', val)
    # low level machine stuff
    # move the value bits to GPIO spots
    # for bidir, all uio bits are in a line starting 
    # at GPIO 21
    val = (val << 21)
    val = (machine.mem32[0xd0000010] ^ val) & 0x1FE00000
    # val is now be all the bits that have CHANGED:
    # writing to 0xd000001c will flip any GPIO where a 1 is found,
    # only applies immediately to pins set as output 
    machine.mem32[0xd000001c] = val
    
    
@micropython.native
def read_uio_byte():
    return (machine.mem32[0xd0000004] & (0xff << 21)) >> 21

@micropython.native
def read_uio_outputenable():
    # GPIO_OE register, masked for our bidir pins
    return (machine.mem32[0xd0000020] & 0x1FE00000) >> 21
    
    
@micropython.native
def write_uio_outputenable(val):
    # GPIO_OE register, clearing bidir pins and setting any enabled
    val = (val << 21)
    machine.mem32[0xd0000020] = (machine.mem32[0xd0000020] & ((1 << 21) - 1)) | val
    
@micropython.native
def write_uo_out_byte(val):
    # low level machine stuff
    # move the value bits to GPIO spots
    
    val = ((val & 0xF) << 5) | ((val & 0xF0) << 13-4)
    val = (machine.mem32[0xd0000010] ^ val) & 0x1E1E0
    # val is now be all the bits that have CHANGED:
    # writing to 0xd000001c will flip any GPIO where a 1 is found,
    # only applies immediately to pins set as output 
    machine.mem32[0xd000001c] = val

@micropython.native
def read_uo_out_byte():
    # just read the high and low nibbles from GPIO and combine into a byte
    return ( (machine.mem32[0xd0000004] & (0xf << 13)) >> (13-4)) | ((machine.mem32[0xd0000004] & (0xf << 5)) >> 5)

    