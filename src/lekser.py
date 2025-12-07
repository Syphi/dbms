from pathlib import Path


def read_from_file(path_to_file: Path) -> str:
    if not path_to_file.exists():
        raise Exception("No such file")

    return path_to_file.read_text()


def read_string(command: str) -> list:
    output_stream = []

    for line in command.splitlines():
        for _token in line.split():
            output_stream.append(_token)

    return output_stream

