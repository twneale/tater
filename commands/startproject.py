import sys
import shutil
import contextlib
from os.path import join, abspath, dirname

import tater


@contextlib.contextmanager
def cd(path):
    '''Creates the path if it doesn't exist'''
    old_dir = os.getcwd()
    try:
        os.makedirs(path)
    except OSError:
        pass
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


def main():
    projname = sys.argv[1]
    try:
        target = sys.argv[2]
    except IndexError:
        target = '.'
    tater_dir = dirname(abspath(tater.__file__))
    exampleapp_dir = join(tater_dir, '..', 'examples', 'exampleapp')
    project_dir = join(target, projname)
    ignore = shutil.ignore_patterns('*.pyc', '__pycache__')
    try:
        shutil.copytree(exampleapp_dir, project_dir, ignore=ignore)
    except OSError as exc:
        if exc.errno:
            print('Error: the folder %r already exists.' % args.module)





if __name__ == '__main__':
    main()