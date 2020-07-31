import os


def main():
    x = input()
    lista = select_files(x)
    print("FIN DEL print DE LA LISTA")
    uno_por_uno(lista)


def select_files(elemento):
    # https://github.com/Darkfoe703/Cypher/blob/master/cyphermain.py

    ext = [".doc"]
    files_to_enc = []

    direccion = elemento
    for dirpath, dirs, files in os.walk(direccion):
        for filename in files:
            if filename.endswith(tuple(ext)):
                files_to_enc.append(os.path.join(dirpath, filename))
    print(*files_to_enc, sep="\n")
    return files_to_enc


def uno_por_uno(lista):
    for x in range(len(lista)):
        print(lista[x])
        os.remove(lista[x])


if __name__ == "__main__":
    main()
