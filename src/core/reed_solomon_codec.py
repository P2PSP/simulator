import unireedsolomon as rs
import traceback

coder = rs.RSCoder(n=255, k=225)


def encode(packet):
    # if packet.decode().replace('\x00', ''):
    #     return packet.decode()
    # traceback.print_stack()
    # print('packet: ', packet)
    # packet = '\x01\x01' + packet.decode()
    # print('packet: ', packet)
    # print('encoded packet: ', coder.encode(packet))
    # print("packet: ", packet.encode())
    # print('encoded packet: ', coder.encode(packet).encode())
    # return coder.encode(packet)
    # if type(packet) == bytes:
    #     packet = packet.decode()
    return packet


def decode(received_message):
    # traceback.print_stack()
    # print('received_message: ', received_message)
    # if received_message.decode() == '\x00\x00':
    #     return '\x00\x00'
    # if received_message.decode() == '\x00':
    # return '\x00'
    # if received_message.decode().replace('\x00', '') == '':# and received_message.decode().count('\x00') <= 8:
    #     print('inside if: ', received_message)
    #     return received_message.decode()
    # print('received_message: ', received_message)
    # print('coder.decode(received_message): ', coder.decode(received_message))
    # print("decoded message: ", coder.decode(received_message))
    # return coder.decode(received_message)[0]
    return received_message


if __name__ == '__main__':
    packet = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the 
    industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled."""
    a = encode(packet.encode())
    print(a)
    print(decode(a))
