import zipfile
import tarfile
import os
import shutil
import logging

log = logging.getLogger(__name__)

EXTRACTABLE = {
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz"
}


def zip_file(path: str) -> str:
    """Zip a file or directory. Returns path to the created .zip."""
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

    log.info("Zipped → %s", zip_name)
    return zip_name


def extract_file(path: str, dest_dir: str) -> str:
    """
    Extract an archive into dest_dir.
    Returns path to the extracted content (file or folder).
    """
    name, _ = os.path.splitext(os.path.basename(path))
    out_dir = os.path.join(dest_dir, name)
    os.makedirs(out_dir, exist_ok=True)

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(out_dir)

    elif tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as tf:
            tf.extractall(out_dir)

    else:
        raise ValueError(f"Unsupported archive format: {path}")

    log.info("Extracted %s → %s", path, out_dir)

    # If the archive contained exactly one item, return that item directly
    items = os.listdir(out_dir)
    if len(items) == 1:
        return os.path.join(out_dir, items[0])
    return out_dir
