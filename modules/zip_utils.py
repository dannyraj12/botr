import zipfile
import os


def zip_file(path):
    zip_name = path + ".zip"

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(path, arcname=os.path.basename(path))

    return zip_name
