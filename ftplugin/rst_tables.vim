"
" reStructuredText tables plugin
" Language:     Python (ft=python)
" Maintainer:   Vincent Driessen <vincent@datafox.nl>
" Version:      Vim 7 (may work with lower Vim versions, but not tested)
" URL:          http://github.com/nvie/vim-rst-tables
"

" Only do this when not done yet for this buffer
if exists("g:loaded_rst_tables_ftplugin")
    finish
endif
let loaded_rst_tables_ftplugin = 1

python << endpython
import vim
import re
from vim_bridge import bridged


def get_table_bounds():
    row, col = vim.current.window.cursor
    upper = lower = row
    try:
        while vim.current.buffer[upper - 1].strip():
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

    return (upper, lower)


def unify_table(table):
    max_fields = max(map(lambda row: len(row), table))
    output = []
    for row in table:
        curr_len = len(row)
        if curr_len < max_fields:
            row += [''] * (max_fields - curr_len)
        output.append(row)
    return output


def parse_table(raw_lines):
    mkfields = lambda line: re.split('\s\s+', line.rstrip())
    output = map(mkfields, raw_lines)
    output = unify_table(output)
    return output


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


def get_column_widths(table):
    widths = []
    for row in table:
        num_fields = len(row)
        # dynamically grow
        if num_fields >= len(widths):
            widths.extend([0] * (num_fields - len(widths)))
        for i in range(num_fields):
            field_text = row[i]
            field_width = len(field_text)
            widths[i] = max(widths[i], field_width)
    return widths


def pad_fields(table, widths=None):
    """Pads fields of the table, so each row lines up nicely with the others.
    If the widths param is None, the widths are calculated automatically.

    """
    if widths is None:
        widths = get_column_widths(table)
    widths = map(lambda w: ' %-' + str(w) + 's ', widths)

    # Pad all fields using the calculated widths
    output = []
    for row in table:
        new_row = []
        for i in range(len(row)):
            col = row[i]
            col = widths[i] % col.strip()
            new_row.append(col)
        output.append(new_row)
    return output


def draw_table(table):
    if table == []:
        return []

    col_widths = get_column_widths(table)
    table = pad_fields(table, col_widths)

    # Reserve room for the spaces
    col_widths = map(lambda x: x + 2, col_widths)
    header_line = table_line(col_widths, header=True)
    normal_line = table_line(col_widths, header=False)

    output = [header_line]
    first = True
    for row in table:
        output.append("|".join([''] + row + ['']))
        if first:
            output.append(header_line)
            first = False
        else:
            output.append(normal_line)

    return output


@bridged
def create_table():
    upper, lower = get_table_bounds()
    slice = vim.current.buffer[upper - 1:lower]
    table = parse_table(slice)
    slice = draw_table(table)
    vim.current.buffer[upper - 1:lower] = slice

endpython

" Add mappings, unless the user didn't want this.
" The default mapping is registered, unless the user remapped it already.
if !exists("no_plugin_maps") && !exists("no_rst_table_maps")
    if !hasmapto('CreateTable(')
        noremap <silent> <leader><leader>c :call CreateTable()<CR>
    endif
    if !hasmapto('ReformatTable(')
        noremap <silent> <leader><leader>f :call ReformatTable()<CR>
    endif
endif
