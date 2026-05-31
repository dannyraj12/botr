import zipfile
import tarfile
import os
import shutil
import logging

log = logging.getLogger(__name__)


def zip_file(path, dest_dir=None):
    zip_name = path.rstrip("/") + ".zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    full = os.path.join(root, file)
                    arcname = os.path.relpath(full, os.path.dirname(path))
                    zf.write(full, arcname=arcname)
        else:
            zf.write(path, arcname=os.path.basename(path))
    log.info("Zipped -> %s", zip_name)
    return zip_name


def extract_file(path, dest_dir):
    name = os.path.splitext(os.path.basename(path))[0]
    # Strip double extensions like .tar.gz
    if name.endswith(".tar"):
        name = name[:-4]

    out_dir = os.path.join(dest_dir, name)

    # FIX: remove existing dir instead of crashing with Errno 17
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(out_dir)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as tf:
            tf.extractall(out_dir)
    else:
        raise ValueError("Unsupported archive format: {}".format(path))

    log.info("Extracted %s -> %s", path, out_dir)

    items = os.listdir(out_dir)
    if len(items) == 1:
        return os.path.join(out_dir, items[0])
    return out_dir
