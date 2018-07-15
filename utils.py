from pathlib import Path


def get_proper_path(parser, path):
    path = Path(path)
    if not path.exists():
        raise parser.error(f'Could not find path {path}.')
    return path
