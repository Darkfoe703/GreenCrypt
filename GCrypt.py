import os
import sys
import time
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2

def full_path(element):
    fullpath = (os.path.abspath(element))
    print(fullpath)
    return(fullpath)

def dir_or_file(element):
    aux = os.path.isfile(element)

    if aux == True:
        print ("Is a file")
        return "file"
    else:
        print ("Is a folder")
        #return (os.path.abspath(element))
        return("folder")

def scan_dir(directory):
    list_files = []
    for dirpath, dirs, files in os.walk(directory):
            for filename in files:
                        list_files.append(os.path.join(dirpath,filename))
                        #print(list_files)
    return(list_files)

def one_by_one(list):
    for x in range(len(list)):
        print(list[x])

def read_file(file):
    try:
        file_in = open(file,"rb")
        content = file_in.read()
        file_in.close()
        print(content)
        return(content)
    except OSError as err:
        print("OS error: {0}".format(err))
        return("")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return("")

def keygen():
    # Salt you generated
    salt = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9'
    # Password provided by the user, can use input() to get this
    password = input()
    # Your key that you can encrypt with
    key = PBKDF2(password, salt, dkLen=32)
    print(key)
    return(key)

def encrypt(secret, key):
    # dato a encriptar
    data0 = secret
    # clave, en este caso de 32bytes para AES256
        # key = clave
    # encabezado del archivo encriptado (completado con cosas randoms para que llegue a 16)
    # es como una firma de integridad manual
    header = b"GreenCrypt\xa8\xb7:\xf5\x83\xd7"
    # construcción del cifrador AES, con el modo EAX
    cipher = AES.new(key, AES.MODE_EAX)
    # Encriptación usando el cifrador, y generación del tag que verificará
    # la integridad el archivo cifrado
    dataX, tag = cipher.encrypt_and_digest(data0)
    # Generación del numero de un uso, que junto con la key
    # nos desencriptaran el archivo
    nonce = cipher.nonce
    final = {'header' : header, 'nonce' : nonce, 'tag' : tag, 'dato' : dataX}
    print(final)
    return(final)

def write_file(parts, name):
    file_out = open(name + ".aes", "wb")
    #Construcción del archivo encriptado:
    #encabezado, número de un uso, tag de verificación, dato cifrado
    [ file_out.write(x) for x in (parts.values()) ]
    file_out.close()

def del_orginal():
    pass

def main():
    path = full_path(input())
    type = dir_or_file(path)
     # ==== If is file, encrypt
        # if not, scan files in folder and subfolders
    if type == "folder":
        files = scan_dir(path)

        x = one_by_one(files)
        #print(x)
    else:
        content = read_file(path)
        key = keygen()
        xxdataxx = encrypt(content, key)
        write_file(xxdataxx, path)
        pass

    #print(files)
    pass

if __name__ == '__main__':
    main()
