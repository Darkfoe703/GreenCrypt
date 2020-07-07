import os


def scan(ruta):
    direccion = ruta
    for dirpath, dirs, files in os.walk(direccion):
            for filename in files:
                        fname = os.path.join(dirpath,filename)
                        print(fname)

def path(aux):
    item = aux
    aux1 = (os.path.abspath(item))
    print(aux1)
    return(aux1)


def select_files():
    # https://github.com/Darkfoe703/Cypher/blob/master/cyphermain.py

    ext = [".marco", ".jazmin", ".padre"]
    files_to_enc = []

    direccion = input()
    for dirpath, dirs, files in os.walk(direccion):
        for filename in files:
            if filename.endswith(tuple(ext)):
                files_to_enc.append(os.path.join(dirpath, filename))
    print(files_to_enc)


def main():
    #aux = path(input())
    #camino = scan(aux)
    select_files()


if __name__ == '__main__':
    main()
