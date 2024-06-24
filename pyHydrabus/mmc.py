# Copyright 2020 Nicolas OBERLI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from .protocol import Protocol
from .common import split


class MMC(Protocol):
    """
    MMC protocol handler

    :example:

    >>> import pyHydrabus
    >>> m=pyHydrabus.MMC('/dev/hydrabus')
    >>> # Get CID
    >>> m.cid
    >>> # Get CSD
    >>> m.csd
    >>> # Read block 0
    >>> m.read(0)

    """

    __MMC_DEFAULT_CONFIG = 0b0

    def __init__(self, port=""):
        self._rf = 0
        self._mode = 0
        self._config = self.__MMC_DEFAULT_CONFIG
        super().__init__(name=b"MMC1", fname="eMMC", mode_byte=b"\x0d", port=port)

    def _configure_port(self):
        CMD = 0b10000000
        CMD = CMD | self._config

        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        if self._hydrabus.read(1) == b"\x01":
            return True
        else:
            self._logger.error("Error setting config.")
            return False

    @property
    def cid(self):
        CMD = 0b00000010
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return self._hydrabus.read(16)

    @property
    def csd(self):
        CMD = 0b00000011
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return self._hydrabus.read(16)

    @property
    def ext_csd(self):
        CMD = 0b00000110
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return self._hydrabus.read(512)

    @property
    def bus_width(self):
        """
        Data bus width (1 or 4)
        """
        if self._config & 0b1:
            return 4
        else:
            return 1

    @bus_width.setter
    def bus_width(self, value):
        if value == 1:
            self._config = self._config & ~(1)
        elif value == 4:
            self._config = self._config | (1)
        else:
            print("Invalid value (1 or 4)")
        self._configure_port()


    def write(self, data=b"", block_num=0):
        """
        Write MMC block

        :param data: Data to be written (512 bytes)
        :type data: bytes
        :param block_num: Block number
        :type block_num: int

        :param data: Data to be written
        :type data: bytes
        """
        CMD = 0b00000101

        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._hydrabus.write(block_num.to_bytes(4, byteorder="big"))
        self._hydrabus.write(data)


        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")

        return status == 1

    def read(self, block_num=0):
        """
        Read MMC block

        :param block_num: Block number
        :type block_num: int

        :return: Bytes read
        :rtype: bytes
        """
        CMD = 0b00000100
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._hydrabus.write(block_num.to_bytes(4, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        if status == 1:
            return self._hydrabus.read(512)
        else:
            return b''

    @property
    def lock(self):
        """
        Lock the eMMC with defaukt password
        """
        CMD = 0b00000111
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return status

    @property
    def unlock(self):
        """
        Unlock the eMMC with default password
        """
        CMD = 0b00001000
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return status

    @property
    def set_password(self):
        """
        Set eMMC with a default password
        """
        CMD = 0b00001001
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return status

    @property
    def clear_password(self):
        """
        Clear the eMMC password
        """
        CMD = 0b00001010
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return status

    @property
    def fail_to_lock(self):
        """
        Volontarily send a wrong password while locking the eMMC
        """
        CMD = 0b00001011
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return status

    @property
    def is_lock(self):
        """
        Volontarily send a wrong password while locking the eMMC
        """
        MMC_IS_LOCK = 0xF0
        MMC_LOCKE_ERROR = 0x0F
        CMD = 0b00001100
        return_value = False
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        if status & MMC_LOCKE_ERROR:
            print("CMD42 Error flag ON")
        if status & MMC_IS_LOCK:
            return_value = True
        return return_value

