import os, sys, time
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2

def ruta(item):
    full_ruta = (os.path.abspath(item))
    print(full_ruta)
    return(full_ruta)
    #pass


def abrir(file):
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
    #pass


def keygen():
    salt = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9' # Salt you generated
    #password = 'marco2' # Password provided by the user, can use input() to get this
    password = input()
    key = PBKDF2(password, salt, dkLen=32) # Your key that you can encrypt with
    #key1 = key[:32]
    #key2 = key[32:]

    print(key)
    return(key)
    #pass


def enc(secreto, clave):
    #dato a encriptar
    #data = b"MarcoRomero"
    data0 = secreto
    #clave, en este caso fija. de 32bytes para AES256
    #key = b'\xc5\x16\xf9}\x9f\x02\x12\xa5@=`.\x9f\x1bN\x87\x8av\x07\xe5\xac\xe2N\xd0\x85\xb1-\x85\x81+\t\xc9'
    key = clave
    #encabezado del archivo encriptado (completado con cosas randoms para que llegue a 16)
    #es como una firma de integridad manual
    header = b"BlackCrypt\xa8\xb7:\xf5\x83\xd7"
    #construcción del cifrador AES, con el modo EAX
    cifrador = AES.new(key, AES.MODE_EAX)
    #Encriptación usando el cifrador, y generación del tag que verificará
    #la integridad el archivo cifrado
    dataX, tag = cifrador.encrypt_and_digest(data0)
    #Generación del numero de un uso, que junto con la key1
    #nos desencriptaran el archivo
    nonce = cifrador.nonce

    final = {'header' : header, 'nonce' : nonce, 'tag' : tag, 'dato' : dataX}
    print(final)
    return(final)

    #print ("Dato: ", data0)
    #print ("Clave: ", key)
    #print ("Header: ", header)
    #print ("Resultado: ",txtcifrado)
    #print ("NONCE: ", nonce)
    #pass


def esc(elementos):
    file_out = open("encrypted.bin", "wb")
    #Construcción del archivo encriptado:
    #encabezado, número de un uso, tag de verificación, dato cifrado
    #[ file_out.write(x) for x in (header, nonce, tag, txtcifrado) ]
    [ file_out.write(x) for x in (elementos.values()) ]
    file_out.close()
    #pass



def main():
    archivo = ruta(input())
    contenido = abrir(archivo)
    clave = keygen()
    secreto = enc(contenido, clave)
    esc(secreto)

    pass




if __name__ == '__main__':
    main()
