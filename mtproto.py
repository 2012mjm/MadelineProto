# -*- coding: utf-8 -*-
"""
Created on Tue Sep  2 19:26:15 2014

@author: agrigoryev
"""
from binascii import crc32
from datetime import datetime
import io
import json
import socket
import struct


def vis(bs):
    """
    Function to visualize byte streams. Split into bytes, print to console.
    :param bs: BYTE STRING
    """
    symbols_in_one_line = 8
    n = len(bs) // symbols_in_one_line
    for i in range(n):
        print(" ".join(["%02X" % b for b in bs[i*symbols_in_one_line:(i+1)*symbols_in_one_line]])) # for every 8 symbols line
    print(" ".join(["%02X" % b for b in bs[(i+1)*symbols_in_one_line:]])+"\n") # for last line


class TL:
    def __init__(self):
        with open("TL_schema.JSON", 'r') as f:
            TL_dict = json.load(f)

        self.methods = TL_dict['methods']
        self.constructors = TL_dict['constructors']

        self.func_dict_id = {}
        self.func_dict_name = {}
        self.obj_dict_id = {}
        self.obj_dict_name = {}

        # Read constructors

        for elem in self.constructors:
            z = TlElement(elem)
            self.func_dict_id = {}

    def serialize(self, type_, data):
        # 1. Type constructor ID
        # 2. type costructor params

        # Bare types
        if type_ == 'string':
            assert isinstance(data, str)
            struct.pack("<L", len(data))
        if type_ == 'int':
            assert isinstance(data, str)
            struct.pack("<L", len(data))

    def deserialize(self, byte_string, type_=None, subtype=None):

        if isinstance(byte_string, io.BytesIO):
            bytes_io = byte_string
        elif isinstance(byte_string, bytes):
            bytes_io = io.BytesIO(byte_string)
        else:
            raise TypeError("Bad input type, use bytes string or BytesIO object")

        # Built-in bare types

        if type_ == 'int':
            x = struct.unpack('<i', bytes_io.read(4))[0]
        elif type_ == '#':
            x = struct.unpack('<I', bytes_io.read(4))[0]
        elif type_ == 'long':
            x = struct.unpack('<q', bytes_io.read(8))[0]
        elif type_ == 'double':
            x = struct.unpack('<d', bytes_io.read(8))[0]
        elif type_ == 'int128':
            t = struct.unpack('<16s', bytes_io.read(16))[0]
            x = int.from_bytes(t, 'little')
        elif type_ == 'int256':
            t = struct.unpack('<32s', bytes_io.read(32))[0]
            x = int.from_bytes(t, 'little')
        elif type_ == 'bytes':
            l = int.from_bytes(bytes_io.read(1), 'little')
            x = bytes_io.read(l)
            bytes_io.read(-(l+1) % 4)  # skip padding bytes
        elif type_ == 'string':
            l = int.from_bytes(bytes_io.read(1), 'little')
            assert l <=254
            if l == 254:
                # We have a long string
                long_len = int.from_bytes(bytes_io.read(3), 'little')
                x = bytes_io.read(long_len)
                bytes_io.read(-long_len % 4)  # skip padding bytes
            else:
                # We have a short string
                x = bytes_io.read(l)
                bytes_io.read(-(l+1) % 4)  # skip padding bytes
            assert isinstance(x, bytes)
        elif type_ == 'vector':
            assert subtype is not None
            count = int.from_bytes(bytes_io.read(4), 'little')
            x = [self.deserialize(bytes_io, type_=subtype) for i in range(count)]
        else:
            # Boxed types

            i = struct.unpack('<i', bytes_io.read(4))[0]  # read type ID
            try:
                tl_elem = self.obj_dict_id[i]
            except:
                raise Exception("Could not extract type: %s" % type_)
            base_boxed_types = ["Vector", "Int", "Long", "Double", "String", "Int128", "Int256"]
            if tl_elem.result in base_boxed_types:
                x = self.deserialize(bytes_io, type_=tl_elem.name, subtype=subtype)

            else:  # other types
                x = {}
                for arg in tl_elem.args:
                    x[arg['name']] = self.deserialize(bytes_io, type_=arg['type'], subtype=arg['subtype'])
        return x


class Session:
    def __init__(self, ip, port):
        # creating socket
        self.sock = socket.socket()
        self.sock.connect((ip, port))
        self.auth_key_id = None
        self.number = 0

    def __del__(self):
        # closing socket when session object is deleted
        self.sock.close()

    @staticmethod
    def header_unencrypted(message):
        """
        Creating header for the unencrypted message:
        :param message: byte string to send
        """
        # Basic instructions: https://core.telegram.org/mtproto/description#unencrypted-message

        # Message id: https://core.telegram.org/mtproto/description#message-identifier-msg-id
        msg_id = int(datetime.utcnow().timestamp()*2**30)*4

        return (b'\x00\x00\x00\x00\x00\x00\x00\x00' +
                struct.pack('<Q', msg_id) +
                struct.pack('<L', len(message)))

    # TCP Transport

    # Instructions may be found here: https://core.telegram.org/mtproto#tcp-transport
    # If a payload (packet) needs to be transmitted from server to client or from client to server,
    # it is encapsulated as follows: 4 length bytes are added at the front (to include the length,
    # the sequence number, and CRC32; always divisible by 4) and 4 bytes with the packet sequence number
    # within this TCP connection (the first packet sent is numbered 0, the next one 1, etc.),
    # and 4 CRC32 bytes at the end (length, sequence number, and payload together).

    def send_message(self, message):
        """
        Forming the message frame and sending message to server
        :param message: byte string to send
        """

        print('>>')
        vis(message)  # Sending message visualisation to console
        data = self.header_unencrypted(message) + message
        step1 = struct.pack('<LL', len(data)+12, self.number) + data
        step2 = step1 + struct.pack('<L', crc32(step1))
        self.sock.send(step2)
        self.number += 1

    def recv_message(self):
        """
        Reading socket and receiving message from server. Check the CRC32 and
        """
        packet_length_data = self.sock.recv(4) # reads how many bytes to read

        if len(packet_length_data) > 0:  # if we have smth. in the socket
            packet_length = struct.unpack("<L", packet_length_data)[0]
            packet = self.sock.recv(packet_length - 4)  # read the rest of bytes from socket
            (self.number, auth_key_id, message_id, message_length)= struct.unpack("<L8s8sI", packet[0:24])
            data = packet[24:24+message_length]
            crc = packet[-4:]

            # Checking the CRC32 correctness of received data
            if crc32(packet_length_data + packet[0:-4]).to_bytes(4, 'little') == crc:
                print('<<')
                vis(data)  # Received message visualisation to console
                return data
