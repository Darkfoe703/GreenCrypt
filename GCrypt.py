#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time, pathlib
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2


def banner_ascii():
    color_green = "\033[1;32m"  # Bright Green Text
    end_color = "\033[m"
    print(
        color_green
        + """
   ____                      ____                  _
  / ___|_ __ ___  ___ _ __  / ___|_ __ _   _ _ __ | |_
 | |  _| '__/ _ \/ _ | '_ \| |   | '__| | | | '_ \| __|
 | |_| | | |  __|  __| | | | |___| |  | |_| | |_) | |_
  \____|_|  \___|\___|_| |_|\____|_|   \__, | .__/ \__|
                                       |___/|_|
"""
        + end_color
    )


def select_action():
    print("1) Encrypt\n" + "2) Decrypt\n")
    choice = input("Select: ")
    if choice == '1':
        # Encriptar
        return choice
    elif choice == '2':
        # Desencriptar
        return choice
    else:
        print("Invalid choice")
        sys.exit(1)


def full_path():
    element = input("Select a file or folder: ")
    fullpath = os.path.abspath(element)
    if os.path.exists(element) == True:
        return(fullpath)
    else:
        print("The file or folder does not exist")
        sys.exit(1)


def dir_or_file(element):
    aux = os.path.isfile(element)

    if aux == True:
        print("Is a file")
        return "file"
    else:
        print("Is a folder")
        # return (os.path.abspath(element))
        return "folder"


def scan_dir(directory):
    list_files = []
    for dirpath, dirs, files in os.walk(directory):
        for filename in files:
            list_files.append(os.path.join(dirpath, filename))
            # print(list_files)
    return list_files


def one_by_one(key, list):
    for file in range(len(list)):
        print(list[file])
        content = read_file(list[file])
        xxdataxx = encrypt(key, content)
        write_file_X(xxdataxx, list[file])


def read_file(file):
    try:
        file_in = open(file, "rb")
        content = file_in.read()
        file_in.close()
        print(content)
        return content
    except OSError as err:
        print("OS error: {0}".format(err))
        return ""
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return ""


def keygen():
    # Password provided by the user, can use input() to get this
    password = input("Password: ")
    # Salt you generated
    salt = b"\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9"
    # Your key that you can encrypt with
    key = PBKDF2(password, salt, dkLen=32)
    #print(key)
    return key


def encrypt(key, secret):
    # dato a encriptar
    data0 = secret
    # clave, en este caso de 32bytes para AES256
    # key = clave
    # encabezado del archivo encriptado
    # (completado con cosas randoms para que llegue a 16)
    # es como una firma de integridad manual
    header = b"GreenCrypt\xa8\xb7:\xf5\x83\xd7"
    # construcción del cifrador AES, con el modo EAX
    cipher = AES.new(key, AES.MODE_EAX)
    # Encriptación usando el cifrador,
    # y generación del tag que verificará
    # la integridad el archivo cifrado
    dataX, tag = cipher.encrypt_and_digest(data0)
    # Generación del numero de un uso, que junto con la key
    # nos desencriptaran el archivo
    nonce = cipher.nonce
    final ={
            "header": header,
            "nonce": nonce,
            "tag": tag,
            "dato": dataX
            }
    print(final)
    return final


def write_file_X(parts, name):
    file_out = open(name + ".aes", "wb")
    # Construcción del archivo encriptado:
    # encabezado, número de un uso, tag de verificación, dato cifrado
    [file_out.write(x) for x in (parts.values())]
    file_out.close()


def del_orginal(file):
    os.remove(file)


def decrypt(key, file):
    file_in = open(file, "rb")

    header = file_in.read(16)
    nonce = file_in.read(16)
    tag = file_in.read(16)
    dataX = file_in.read()

    file_in.close()

    cipher = AES.new(key, AES.MODE_EAX, nonce)
    data0 = cipher.decrypt_and_verify(dataX, tag)

    # print("Header: ", header)
    # print("NONCE: ", nonce)
    # print("TAG: ", tag)
    # print("BRUTO: ", dataX)
    # print("Dato: ", data0)
    return data0

def write_file_0(content, name):
    file, ext = os.path.splitext(name)
    data0 = content.decode("utf-8")
    try:
        with open(file, "w+") as x:
        x.write(data0)
    except Exception as e:
        print(f"Error al escribir el archivo: {e}")
    


def main():
    #banner_ascii()
    action = select_action()
    path = full_path()
    type_object = dir_or_file(path)
    #print(path) 

    if action == '1':
    # Encriptar
    # ==== If is file, encrypt
    # if not, scan files in folder and subfolders
        match type_object:
            case "folder":
                print("Enc Carpetita")
                # key = keygen()
                # files = scan_dir(path)
                # x = one_by_one(key, files)
                # # print(x)
            case "file":
                print("Enc archivito")
                key = keygen()
                content = read_file(path)
                xxdataxx = encrypt(key, content)
                write_file_X(xxdataxx, path)
                # del_orginal(path)

    elif action == '2':
        # Desencriptar
        match type_object:
            case "folder":
                print("Dec Carpetita")
            # key = keygen()
            # files = scan_dir(path)
            # x = one_by_one(key, files)
            # # print(x)
            case "file":
                print("Dec archivito")
                key = keygen()
                content = read_file(path)
                xxdataxx = decrypt(key, path)
                write_file_0(xxdataxx, path)
                #del_orginal(path)
                #pass
    else:
        print("Invalid choice")
        # print(files)
    #     pass


if __name__ == "__main__":
    main()
