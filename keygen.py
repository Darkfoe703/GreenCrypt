import os, sys, time
from Cryptodome.Protocol.KDF import PBKDF2

def main():
    
    salt = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9' # Salt you generated
    password = 'marco2' # Password provided by the user, can use input() to get this
    key = PBKDF2(password, salt, dkLen=32) # Your key that you can encrypt with
    key1 = key[:32]
    key2 = key[32:]

    print (key)
    print (key1)
    print (key2)

if __name__ == '__main__':
    main()
