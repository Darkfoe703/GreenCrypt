import os, sys, time
from Cryptodome.Random import get_random_bytes

def main():
    aux1 = "marco"
    largo1 = len(aux1)#cuenta los caraacteres de la cadena
    print (aux1)
    print (largo1)

    aux2 = bytes(aux1,"utf-8")#Transforma una caden an bytes codificados en utf-8
    largo2 = len(aux2)#cuenta los bytes
    print (aux2)
    print (largo2)

    aux3 = get_random_bytes(16)#genera 16 bytes aleatorios
    largo3 = len(aux3)
    print (aux3)
    print (largo3)

    aux4 = b'marco'#marco como bytes
    largo4 = len(aux4)
    print (aux4)
    print (largo4)

if __name__ == '__main__':
    main()
