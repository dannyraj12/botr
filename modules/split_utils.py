import os


def split_file(path, split_size):
    parts = []

    size = os.path.getsize(path)

    if size <= split_size:
        return [path]

    with open(path, 'rb') as f:
        i = 1

        while True:
            chunk = f.read(split_size)

            if not chunk:
                break

            part_name = f"{path}.part{str(i).zfill(2)}"

            with open(part_name, 'wb') as p:
                p.write(chunk)

            parts.append(part_name)
            i += 1

    return parts
