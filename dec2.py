import os
import sys
import time
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2

def full_path():
    element = input("Select a file or folder: ")
    fullpath = (os.path.abspath(element))
    print(fullpath)
    return(fullpath)

def keygen():
    # Password provided by the user, can use input() to get this
    password = input("Password: ")
    # Salt you generated
    salt = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9'
    # Your key that you can encrypt with
    key = PBKDF2(password, salt, dkLen=32)
    print(key)
    return(key)

def decrytp(key, file):
    file_in = open(file, "rb")

    header = file_in.read(16)
    nonce = file_in.read(16)
    tag = file_in.read(16)
    dataX = file_in.read()

    file_in.close()

    cipher = AES.new(key, AES.MODE_EAX, nonce)
    data0 = cipher.decrypt_and_verify(dataX, tag)

    print ("Header: ", header)
    print ("NONCE: ", nonce)
    print ("TAG: ", tag)
    print ("BRUTO: ", dataX)
    print ("Dato: ", data0)
    return(data0)

def write_file_X(parts, name):
    file_out = open(name + ".aes", "wb")
    #Construcción del archivo encriptado:
    #encabezado, número de un uso, tag de verificación, dato cifrado
    [ file_out.write(x) for x in (parts.values()) ]
    file_out.close()

def write_file_0(name, content):
    # Guarda la IP en un archivo
    file, ext = os.path.splitext(name)
    data0 = content.decode("unicode")
    #x = open(file, "w+")
    #x.write(data0)
    #x.close()

    with open(file, "w+") as x:
        x.write(data0)

	# Devuelve al programa principal la IP en esa variable
	#return DireccionIP

#>>> import os
#>>> filename, file_extension = os.path.splitext('/path/to/somefile.ext')
#>>> filename
#'/path/to/somefile'
#>>> file_extension
#'.ext'

def main():
    file = full_path()
    key = keygen()
    content = decrytp(key, file)
    write_file_0(file, content)
    pass

if __name__ == '__main__':
    main()
