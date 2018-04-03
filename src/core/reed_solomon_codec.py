import unireedsolomon as rs

coder = rs.RSCoder(n=255, k=128)


def encode(packet):
    """
    Returns the encoded message. Breaks a message in the max chunks size of 100 bytes for encoding
    :param packet: the chunk to be sent to the peers
    :return: A list having the encoded messages.
    """
    transmittable_message = []
    y = 0
    while y < len(packet):
        if len(packet) - y > 100:
            encoded_message = coder.encode(packet[y:y + 100])
        else:
            encoded_message = coder.encode(packet[y:])
        y += 100
        transmittable_message.append(encoded_message)
    return transmittable_message


def decode(received_message):
    return coder.decode(received_message)


if __name__ == '__main__':
    packet = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it 
    to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, 
    remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem 
    Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem 
    Ipsum. """
    a = encode(packet)
    print(a)
    print(decode(a))
