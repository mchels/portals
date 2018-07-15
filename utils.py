from pathlib import Path


def get_proper_path(parser, path):
    path = Path(path)
    if not path.exists():
        raise parser.error(f'Could not find path {path}.')
    return path

def parse_method_and_args(obj, dic):
    """
    Gets the specified method given an object and a dictionary specifying the
    method. `dic` should have the form
    {'some_key': {'other_key': [arg1, arg2, arg3]}}
    In this case we return obj.some_key.other_key, [arg1, arg2, arg3].
    Assumption: dic has exactly one key.

    Be careful when executing the return values. If you pass, e.g., `sys` as
    `obj` you can end up with dangerous method-args combination.
    """
    while isinstance(dic, dict):
        key, dic = list(dic.items())[0]
        obj = getattr(obj, key)
    args = dic
    return obj, args


if __name__ == '__main__':
    TEST_DICT = {
        'parent': {
            'parent': {
                'resolve': [],
            }
        }
    }
    OBJ = Path.home()
    METHOD, ARGS = parse_method_and_args(OBJ, TEST_DICT)
    # Should be (on Windows)
    # <bound method Path.resolve of WindowsPath('C:/')> []
    print(METHOD, ARGS)
    result = METHOD(*ARGS)
    print(result)
