import base64

class Base64(object):
    ALPHABET = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd',
    'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
    'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
    'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7',
    '8', '9', '+', '/']
    padding = '='

    @staticmethod
    def encode(plaintext:bytes):
        bytes_hex = plaintext.hex()
        ret = []
        n, m = len(bytes_hex) // 6, len(bytes_hex) % 6
        i = 0
        while(i < n):
            tmp = bytes_hex[i * 6:(i + 1) *6]
            ret.append(Base64.ALPHABET[(int(tmp[0], 16) << 2) + (int(tmp[1], 16) >> 2)])
            ret.append(Base64.ALPHABET[((int(tmp[1], 16) & int('11', 2)) << 4) + int(tmp[2], 16)])
            ret.append(Base64.ALPHABET[(int(tmp[3], 16) << 2) + (int(tmp[4], 16) >> 2)])
            ret.append(Base64.ALPHABET[((int(tmp[4], 16) & int('11', 2)) << 4) + int(tmp[5], 16)])
            i += 1
        i = i * 6
        if m == 2:
            ret.append(Base64.ALPHABET[(int(bytes_hex[i], 16) << 2) + (int(bytes_hex[i + 1], 16) >> 2)])
            ret.append(Base64.ALPHABET[(int(bytes_hex[i + 1], 16) & int('11', 2)) << 4])
            ret.append(Base64.padding)
            ret.append(Base64.padding)
        elif m ==4:
            ret.append(Base64.ALPHABET[(int(bytes_hex[i], 16) << 2) + (int(bytes_hex[i + 1], 16) >> 2)])
            ret.append(Base64.ALPHABET[((int(bytes_hex[i + 1], 16) & int('11', 2)) << 4) + int(bytes_hex[i + 2], 16)])
            ret.append(Base64.ALPHABET[int(bytes_hex[i + 3], 16) << 2])
            ret.append(Base64.padding)
        return bytes(''.join(ret), 'utf-8')

    @staticmethod
    def decode(input:bytes):
        new_alphabet = list(map(ord, Base64.ALPHABET))
        ret = []
        n = len(input) // 4
        i = 0
        while(i < n - 1):
            tmp = input[i * 4:(i + 1) *4]
            a, b, c, d = new_alphabet.index(tmp[0]), new_alphabet.index(tmp[1]), new_alphabet.index(tmp[2]), new_alphabet.index(tmp[3])
            ret.append(hex(int(bin(a)[2:].zfill(6) + bin(b)[2:].zfill(6) + bin(c)[2:].zfill(6) + bin(d)[2:].zfill(6), 2))[2:].zfill(6))
            i += 1
        end = input[i * 4:]
        s = ''
        for tmp in end:
            if tmp != ord(Base64.padding):
                s = s + bin(new_alphabet.index(tmp))[2:].zfill(6)
        end = hex(int(s[:(len(s) // 8) * 8], 2))[2:]
        if len(end) < 2:
            end = end.zfill(2)
        elif len(end) < 4:
            end = end.zfill(4)
        else:
            end = end.zfill(6)
        ret.append(end)
        return bytes.fromhex(''.join(ret))

def test():
    x = '我是用来测试的字符串：p点\nhello'
    a = base64.b64encode(bytes(x, 'utf-8')).decode()
    print(a)
    b = Base64.encode(bytes(x, 'utf-8')).decode()
    print(b)
    c = base64.b64decode(bytes(a, 'utf-8')).decode()
    print(c)
    d = Base64.decode(bytes(a, 'utf-8')).decode()
    print(d)

if __name__ == '__main__':
    # test()
    with open('data/V2RayN_1662541585.txt', 'rb') as f:
        data = f.read()
        out1 = base64.b64decode(data).decode()
        out2 = Base64.decode(data).decode()
        print(F"out1:{out1}")
        print(F"out2:{out2}")