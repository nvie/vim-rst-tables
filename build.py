#!/usr/bin/env python
import os

source_dir = 'src'
output_dir = 'ftplugin'


def build():
    py_src = file(os.path.join(source_dir, 'rst_tables.py')).read()
    vim_src = file(os.path.join(source_dir, 'base.vim')).read()
    combined_src = vim_src.replace('__PYTHON_SOURCE__', py_src)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    output_path = os.path.join(output_dir, 'rst_tables.vim')
    file(output_path, 'w').write(combined_src)

if __name__ == '__main__':
    build()
