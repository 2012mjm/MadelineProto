# -*- coding: utf-8 -*-
# Author: Sammy Pfeiffer
# Author: Anton Grigoryev
# This file implements the AES 256 IGE cipher
# working in Python 2.7 and Python 3.4 (other versions untested)
# as it's needed for the implementation of Telegram API
# It's based on PyCryto

from __future__ import print_function
from Crypto.Util.strxor import strxor
from Crypto.Cipher import AES


class IGE:
    def __init__(self, key, iv):
        if len(key) != 32:
            raise ValueError("key must be 32 bytes long (was " +
                             str(len(key)) + " bytes)")
        if len(iv) != 32:
            raise ValueError("iv must be 32 bytes long (was " +
                             str(len(iv)) + " bytes)")

        self.key = key
        self.iv = iv

        self.cipher = AES.new(key, AES.MODE_ECB, iv)

    def encrypt(self, message):
        return self._ige(message, operation="encrypt")

    def decrypt(self, message):
        return self._ige(message, operation="decrypt")

    def _ige(self, message, operation="decrypt"):
        """Given a key, given an iv, and message
         do whatever operation asked in the operation field.
         Operation will be checked for: "decrypt" and "encrypt" strings.
         Returns the message encrypted/decrypted.
         message must be a multiple by 16 bytes (for division in 16 byte blocks)
         key must be 32 byte
         iv must be 32 byte (it's not internally used in AES 256 ECB, but it's
         needed for IGE)"""

        if len(message) % blocksize != 0:
            raise ValueError("message must be a multiple of 16 bytes (try adding " +
                            str(16 - len(message) % 16) + " bytes of padding)")

        blocksize = self.cipher.block_size
        ivp = self.iv[0:blocksize]
        ivp2 = self.iv[blocksize:]

        ciphered = bytearray()

        for i in range(0, len(message), blocksize):
            indata = message[i:i+blocksize]
            if operation == "decrypt":
                xored = strxor(indata, ivp2)
                decrypt_xored = self.cipher.decrypt(xored)
                outdata = strxor(decrypt_xored, ivp)
                ivp = indata
                ivp2 = outdata
            elif operation == "encrypt":
                xored = strxor(indata, ivp)
                encrypt_xored = self.cipher.encrypt(xored)
                outdata = strxor(encrypt_xored, ivp2)
                ivp = outdata
                ivp2 = indata
            else:
                raise ValueError("operation must be either 'decrypt' or 'encrypt'")
            ciphered.extend(outdata)
        return ciphered