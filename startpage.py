import os
import types
import winreg
from argparse import Namespace
from time import sleep

d = {'uefi': 1, 'ram': 34359738368, 'space': 133264248832, 'resizable': 432008358400, 'arch': 'amd64'}


class Data:
    uefi = 1
    ram = 34359738368
    space = 133264248832
    resizable = 432008358400
    arch = 'amd64'


print(Data.uefi)
