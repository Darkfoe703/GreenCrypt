import os, sys, time
from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import PBKDF2


def main():
    file_in = open("encrypted.bin", "rb")

    header = file_in.read(16)
    nonce = file_in.read(16)
    tag = file_in.read(16)
    txtcifrado = file_in.read()

    file_in.close()


    #key = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9'
    salt = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9' # Salt you generated
    #password = 'marco2' # Password provided by the user, can use input() to get this
    password = input()
    key = PBKDF2(password, salt, dkLen=32) # Your key that you can encrypt with
    #key1 = key[:32]
    #key2 = key[32:]

    print(key)
    #return(key)
    #pass

    cifrador = AES.new(key, AES.MODE_EAX, nonce)
    data = cifrador.decrypt_and_verify(txtcifrado, tag)

    print ("Header: ", header)
    print ("NONCE: ", nonce)
    print ("TAG: ", tag)
    print ("BRUTO: ",txtcifrado)

    print ("Dato: ", data)

if __name__ == '__main__':
    main()
