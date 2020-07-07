import os, sys, time
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes


def main():
    #dato a encriptar
    data = b"MarcoRomero"
    #clave, en este caso fija. de 32bytes para AES256
    key = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9'
    #encabezado del archivo encriptado (completado con cosas randoms para que llegue a 16)
    #es como una firma de integridad manual
    header = b"BlackCrypt\xa8\xb7:\xf5\x83\xd7"
    #construcción del cifrador AES, con el modo EAX
    cifrador = AES.new(key, AES.MODE_EAX)
    #Encriptación usando el cifrador, y generación del tag que verificará
    #la integridad el archivo cifrado
    txtcifrado, tag = cifrador.encrypt_and_digest(data)
    #Generación del numero de un uso, que junto con la key1
    #nos desencriptaran el archivo
    nonce = cifrador.nonce

    print ("Dato: ", data)
    print ("Clave: ", key)
    print ("Header: ", header)
    print ("Resultado: ",txtcifrado)
    print ("NONCE: ", nonce)

    file_out = open("encrypted.bin", "wb")
    #Construcción del archivo encriptado:
    #encabezado, número de un uso, tag de verificación, dato cifrado
    [ file_out.write(x) for x in (header, nonce, tag, txtcifrado) ]
    file_out.close()


if __name__ == '__main__':
    main()
