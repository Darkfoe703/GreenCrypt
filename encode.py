
import chardet


def get_file_encoding(src_file_path):
    """
    Get the encoding type of a file
    :param src_file_path: file path
    :return: str - file encoding type
    """

    with open(src_file_path) as src_file:
        return src_file.encoding
    

def get_file_encoding_chardet(file_path):
    """
    Get the encoding of a file using chardet package
    :param file_path:
    :return:
    """
    with open(file_path, 'rb') as f:

        result = chardet.detect(f.read())
        return result['encoding']


csv_file_path = input('Please enter csv filename: ')
print('Endcoding: ' + str(get_file_encoding(csv_file_path)))
print('Endcoding with chardet: ' + str(get_file_encoding_chardet(csv_file_path)))
