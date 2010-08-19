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
    select_data_lines = lambda line: not re.match('^[\t +=-]+$', line)
    lines = filter(select_data_lines, raw_lines)
    lines = map(split_table_row, lines)
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
