"
" reStructuredText tables plugin
" Language:     Python (ft=python)
" Maintainer:   Vincent Driessen <vincent@datafox.nl>
" Version:      Vim 7 (may work with lower Vim versions, but not tested)
" URL:          http://github.com/nvie/vim-rst-tables
"
" This plugin is a more flexible reimplementation of the ideas and the
" existing Vim plugin by Hugo Ruscitti:
"   http://www.vim.org/scripts/script.php?script_id=3041
"

" Only do this when not done yet for this buffer
if exists("g:loaded_rst_tables_ftplugin")
    finish
endif
let loaded_rst_tables_ftplugin = 1

" Default to Python 2
let py_cmd_ver = 'python'
let py_cmd_ver_other = 'python3'
" Allow user to select Python 3
if exists('g:rst_prefer_python_version') &&
            \ g:rst_prefer_python_version == 3
    let py_cmd_ver = 'python3'
    let py_cmd_ver_other = 'python'
endif
if !has(py_cmd_ver)
    let py_cmd_ver = py_cmd_ver_other
    if !has(py_cmd_ver)
        echoerr "Error: Requires Vim compiled with +python or +python3"
        finish
    endif
endif

if py_cmd_ver == 'python'
    command! -nargs=1 Python python <args>
else
    command! -nargs=1 Python python3 <args>
endif

Python << endpython

import vim

import sys
PY2 = sys.version_info[0] < 2

from os.path import dirname, join as pjoin

# get the directory this script is in: the vim_bridge python module should be installed there.
our_pth = dirname(vim.eval('expand("<sfile>")'))
sys.path.insert(0, pjoin(our_pth, 'vim_bridge'))

import re
import textwrap
import unicodedata
import codecs
from vim_bridge import bridged


def get_table_bounds():
    row, col = vim.current.window.cursor
    upper = lower = row
    try:
        while vim.current.buffer[upper - 1].strip() and upper > 0:
            upper -= 1
    except IndexError:
        pass
    else:
        upper += 1

    try:
        while vim.current.buffer[lower - 1].strip():
            lower += 1
    except IndexError:
        pass
    else:
        lower -= 1

    match = re.match(r'^(\s*).*$', vim.current.buffer[upper-1])

    return (upper, lower, match.group(1))

def join_rows(rows, sep='\n'):
    """Given a list of rows (a list of lists) this function returns a
    flattened list where each the individual columns of all rows are joined
    together using the line separator.

    """
    output = []
    for row in rows:
        # grow output array, if necessary
        if len(output) <= len(row):
            for i in range(len(row) - len(output)):
                output.extend([[]])

        for i, field in enumerate(row):
            field_text = field.strip()
            if field_text:
                output[i].append(field_text)
    return [sep.join(lines) for lines in output]


def line_is_separator(line):
    return re.match(r'^[\t +=-]+$', line)


def has_line_seps(raw_lines):
    for line in raw_lines:
        if line_is_separator(line):
            return True
    return False


def partition_raw_lines(raw_lines):
    """Partitions a list of raw input lines so that between each partition, a
    table row separator can be placed.

    """
    if not has_line_seps(raw_lines):
        return [[x] for x in raw_lines]

    curr_part = []
    parts = [curr_part]
    for line in raw_lines:
        if line_is_separator(line):
            curr_part = []
            parts.append(curr_part)
        else:
            curr_part.append(line)

    # remove any empty partitions (typically the first and last ones)
    return [x for x in parts if x!= []]


def unify_table(table):
    """Given a list of rows (i.e. a table), this function returns a new table
    in which all rows have an equal amount of columns.  If all full column is
    empty (i.e. all rows have that field empty), the column is removed.

    """
    max_fields = max([len(row) for row in table])

    empty_cols = [True] * max_fields
    output = []
    for row in table:
        curr_len = len(row)
        if curr_len < max_fields:
            row += [''] * (max_fields - curr_len)
        output.append(row)

        # register empty columns (to be removed at the end)
        for i in range(len(row)):
            if row[i].strip():
                empty_cols[i] = False

    # remove empty columns from all rows
    table = output
    output = []
    for row in table:
        cols = []
        for i in range(len(row)):
            should_remove = empty_cols[i]
            if not should_remove:
                cols.append(row[i])
        output.append(cols)

    return output


def split_table_row(row_string):
    if row_string.find("|") >= 0:
        # first, strip off the outer table drawings
        row_string = re.sub(r'^\s*\||\|\s*$', '', row_string)
        return re.split(r'\s*\|\s*', row_string.strip())
    return re.split(r'\s\s+', row_string.rstrip())


def parse_table(raw_lines):
    row_partition = partition_raw_lines(raw_lines)
    lines = [join_rows([split_table_row(row) for row in row_string])
             for row_string in row_partition]
    return unify_table(lines)


def table_line(widths, header=False):
    if header:
        linechar = '='
    else:
        linechar = '-'
    sep = '+'
    parts = []
    for width in widths:
        parts.append(linechar * width)
    if parts:
        parts = [''] + parts + ['']
    return sep.join(parts)


def get_field_width(field_text):
    return max([len(s) for s in field_text.split('\n')])


def get_string_width(string):
    width = 0
    for char in list(string):
        eaw = unicodedata.east_asian_width(char)
        if eaw == 'Na' or eaw == 'H':
            width += 1
        else:
            width += 2
    return width

def split_row_into_lines(row):
    row = [field.split('\n') for field in row]
    height = max([len(field_lines) for field_lines in row])
    turn_table = []
    for i in range(height):
        fields = []
        for field_lines in row:
            if i < len(field_lines):
                fields.append(field_lines[i])
            else:
                fields.append('')
        turn_table.append(fields)
    return turn_table


def get_column_widths(table):
    widths = []
    for row in table:
        num_fields = len(row)
        # dynamically grow
        if num_fields >= len(widths):
            widths.extend([0] * (num_fields - len(widths)))
        for i in range(num_fields):
            field_text = row[i]
            field_width = get_field_width(field_text)
            widths[i] = max(widths[i], field_width)
    return widths


def get_column_widths_from_border_spec(slice):
    border = None
    for row in slice:
        if line_is_separator(row):
            border = row.strip()
            break

    if border is None:
        raise RuntimeError('Cannot reflow this table. Top table border not found.')

    left = right = None
    if border[0] == '+':
        left = 1
    if border[-1] == '+':
        right = -1
    # This will return one width if there are no + characters
    return [max(0, len(drawing) - 2) for drawing in border[left:right].split('+')]


def pad_fields(row, widths):
    """Pads fields of the given row, so each field lines up nicely with the
    others.

    """
    widths = [' %-' + str(w) + 's ' for w in widths]

    # Pad all fields using the calculated widths
    new_row = []
    for i in range(len(row)):
        col = widths[i] % row[i].strip()
        new_row.append(col)
    return new_row


def reflow_row_contents(row, widths):
    new_row = []
    for i, field in enumerate(row):
        wrapped_lines = textwrap.wrap(field.replace('\n', ' '), widths[i])
        new_row.append("\n".join(wrapped_lines))
    return new_row


def draw_table(indent, table, manual_widths=None):
    if table == []:
        return []

    if manual_widths is None:
        col_widths = get_column_widths(table)
    else:
        col_widths = manual_widths

    # Reserve room for the spaces
    sep_col_widths = [x + 2 for x in col_widths]
    header_line = table_line(sep_col_widths, header=True)
    normal_line = table_line(sep_col_widths, header=False)

    output = [indent+normal_line]
    first = True
    for row in table:

        if manual_widths:
            row = reflow_row_contents(row, manual_widths)

        row_lines = split_row_into_lines(row)

        # draw the lines (num_lines) for this row
        for row_line in row_lines:
            row_line = pad_fields(row_line, col_widths)
            output.append(indent+"|".join([''] + row_line + ['']))

        # then, draw the separator
        if first:
            output.append(indent+header_line)
            first = False
        else:
            output.append(indent+normal_line)

    return output


def proc_table(func):
    upper, lower, indent = get_table_bounds()
    table_txt = vim.current.buffer[upper - 1:lower]
    if PY2:
        encoding = vim.eval("&encoding")
        table_txt = [codecs.decode(x, encoding) for x in table_txt]
    table_txt = func(indent, table_txt)
    if PY2:
        table_txt = [codecs.encode(x, encoding) for x in table_txt]
    vim.current.buffer[upper - 1:lower] = table_txt


def _reformat(indent, table_txt):
    table = parse_table(table_txt)
    return draw_table(indent, table)


@bridged
def reformat_table():
    proc_table(_reformat)


def _reflow(indent, table_txt):
    widths = get_column_widths_from_border_spec(table_txt)
    table = parse_table(table_txt)
    return draw_table(indent, table, widths)


@bridged
def reflow_table():
    proc_table(_reflow)


endpython

" Add mappings, unless the user didn't want this.
" The default mapping is registered, unless the user remapped it already.
if !exists("no_plugin_maps") && !exists("no_rst_table_maps")
    if !hasmapto('ReformatTable(')
        noremap <silent> <leader><leader>c :call ReformatTable()<CR>
    endif
    if !hasmapto('ReflowTable(')
        noremap <silent> <leader><leader>f :call ReflowTable()<CR>
    endif
endif
