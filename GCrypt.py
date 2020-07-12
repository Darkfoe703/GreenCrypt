import os
import sys
import time
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2

def banner_ascii():
    BGREEN = "\033[1;32m" # Bright Green Text
    ENDColor = "\033[m"
    print(BGREEN + """
   ____                      ____                  _
  / ___|_ __ ___  ___ _ __  / ___|_ __ _   _ _ __ | |_
 | |  _| '__/ _ \/ _ | '_ \| |   | '__| | | | '_ \| __|
 | |_| | | |  __|  __| | | | |___| |  | |_| | |_) | |_
  \____|_|  \___|\___|_| |_|\____|_|   \__, | .__/ \__|
                                       |___/|_|
""" + ENDColor)

def select_action():
    print("1) Encrypt\n" + "2) Decrypt\n")
    input("Select: ")
    pass

def full_path():
    element = input("Select a file or folder: ")
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

def one_by_one(key, list):
    for file in range(len(list)):
        print(list[file])
        content = read_file(list[file])
        xxdataxx = encrypt(key, content)
        write_file(xxdataxx, list[file])

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
    # Password provided by the user, can use input() to get this
    password = input("Password: ")
    # Salt you generated
    salt = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9'
    # Your key that you can encrypt with
    key = PBKDF2(password, salt, dkLen=32)
    print(key)
    return(key)

def encrypt(key, secret):
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

def del_orginal(file):
    os.remove(file)

def decrytp():
    pass



def main():
    banner_ascii()
    select_action()
    path = full_path()
    type = dir_or_file(path)
     # ==== If is file, encrypt
        # if not, scan files in folder and subfolders
    if type == "folder":
        key = keygen()
        files = scan_dir(path)
        x = one_by_one(key, files)
        #print(x)
    else:
        key = keygen()
        content = read_file(path)
        xxdataxx = encrypt(key, content)
        write_file(xxdataxx, path)
        del_orginal(path)
        pass

    #print(files)
    pass

if __name__ == '__main__':
    main()
