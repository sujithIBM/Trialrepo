import os.path
path1 = "C:/Users/IBM_ADMIN/Desktop/py"
name = 'logwarn.py'

def isReadableFile(file_path, file_name):
    full_path = file_path + "/" + file_name
    try:
        if not os.path.exists(file_path):
            print("File path is invalid.")
        elif not os.path.isfile(full_path):
            print("File does not exist.")
        elif not os.access(full_path, os.R_OK):
            print("File cannot be read.")
        else:
            print("File can be existing.")
    except IOError as ex:
        print("I/O error({0}): {1}".format(ex.errno, ex.strerror))
    except Error as ex:
        print("Error({0}): {1}".format(ex.errno, ex.strerror))

isReadableFile(path1,name)
