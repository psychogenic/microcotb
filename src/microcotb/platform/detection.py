'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

IsRP2040 = False 
try:
    import machine 
    import rp2
    IsRP2040 = True 
except:
    pass