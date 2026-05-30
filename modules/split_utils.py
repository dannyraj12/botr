import os
import logging

log = logging.getLogger(__name__)


def split_file(path, split_size):
    size = os.path.getsize(path)

    if size <= split_size:
        return [path]

    parts = []
    part_num = 1

    with open(path, "rb") as f:
        while True:
            chunk = f.read(split_size)
            if not chunk:
                break

            part_name = "{}.part{}".format(path, str(part_num).zfill(2))

            with open(part_name, "wb") as pf:
                pf.write(chunk)

            parts.append(part_name)
            log.info("Split part %d -> %s (%d bytes)", part_num, part_name, len(chunk))
            part_num += 1

    return parts
