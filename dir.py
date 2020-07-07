import os, sys, logging, time


def queEs():
    entrada = input()
    aux = os.path.isfile(entrada)

    if aux == True:
        print ("Es un archivo")
        return "archivo"
    else:
        print ("Es una carpeta")
        return (os.path.abspath(entrada))

def abCarpeta(route):
    basepath = route
    with os.scandir(basepath) as entries:
        for entry in entries:
            #if entry.is_file():
                print(entry.path)

def main():
    es = queEs()
    if es == "archivo":
        print ("Se abre el archivo")
    else:
        pass
        abCarpeta(es)


if __name__ == '__main__':
    main()
