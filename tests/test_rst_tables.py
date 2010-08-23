# Mock out the vim library
import sys
sys.path = ['tests/mocks'] + sys.path
import vim
import mock

vimvar = {}


def fake_eval(x):
    global vimvar
    return vimvar[x]

vim.eval = fake_eval
vim.current = mock.Mock()
vimvar['foo'] = 'bar'

# Begin normal module loading
import os
import unittest

# Load test subjects
from rst_tables import get_table_bounds, reformat_table, parse_table, \
             reflow_table, draw_table, table_line, get_column_widths, \
             get_column_widths_from_border_spec, pad_fields, unify_table, \
             join_rows, partition_raw_lines, split_row_into_lines, \
             reflow_row_contents

class TestRSTTableFormatter(unittest.TestCase):

    def setUp(self):
        # Default vim cursor for all tests is at line 4
        vim.current = mock.Mock()
        self.set_vim_cursor(4, 0)

    def tearDown(self):
        del vim.current

    def set_vim_cursor(self, row, col):
        vim.current.window.cursor = (row, col)

    def read_fixture(self, name):
        return open(os.path.join('tests/fixtures/', name + '.txt'),
                    'r').read().split('\n')

    def load_fixture_in_vim(self, name):
        vim.current.buffer = self.read_fixture(name)

    def testGetBounds(self):
        self.load_fixture_in_vim('default')
        self.assertEquals((3, 6), get_table_bounds())

    def testGetBoundsOnBeginOfFile(self):
        self.load_fixture_in_vim('default')
        vim.current.window.cursor = (1, 0)
        self.assertEquals((1, 1), get_table_bounds())

    def testGetBoundsOnEndOfFile(self):
        self.load_fixture_in_vim('default')
        vim.current.window.cursor = (8, 0)
        self.assertEquals((8, 9), get_table_bounds())

    def testJoinSimpleRows(self):
        input_rows = [['x', 'y', 'z'], ['foo', 'bar']]
        expected = ['x\nfoo', 'y\nbar', 'z']
        self.assertEquals(expected, join_rows(input_rows))

        input_rows.append(['apple', '', 'pear'])
        expected = ['x foo apple', 'y bar', 'z pear']
        self.assertEquals(expected, join_rows(input_rows, sep=' '))

    def testPartitionRawLines(self):
        self.assertEquals([], partition_raw_lines([]))
        self.assertEquals([['']], partition_raw_lines(['']))
        self.assertEquals(
                [['foo'], ['bar']],
                partition_raw_lines(['foo', 'bar']))
        self.assertEquals(
                [['foo'], ['bar']],
                partition_raw_lines(['foo', '+----+', 'bar']))
        self.assertEquals(
                [['foo', 'bar'], ['baz']],
                partition_raw_lines(['+-----+', 'foo', 'bar', '----', 'baz']))

    def testParseSimpleTable(self):
        self.assertEquals([['x y z']], parse_table(['x y z']))
        self.assertEquals([['x', 'y z']], parse_table(['x  y z']))
        self.assertEquals([['x', 'y', 'z']], parse_table(['x  y          z']))

    def testParseTable(self):
        self.load_fixture_in_vim('default')
        expected = [
                ['Column 1', 'Column 2'],
                ['Foo', 'Put two (or more) spaces as a field separator.'],
                ['Bar', 'Even very very long lines like these are fine, as long as you do not put in line endings here.'],
                ['Qux', 'This is the last line.'],
                ]
        self.assertEquals(expected, parse_table(vim.current.buffer[2:6]))

    def testParseTableUnifiesColumns(self):
        input = ['x  y', 'a  b    c', 'only one']
        expected = [['x', 'y', ''], ['a', 'b', 'c'], ['only one', '', '']]
        self.assertEquals(expected, parse_table(input))

    def testUnifyTables(self):
        input = [[' x ', '  y'], ['xxx', ' yyyy ', 'zz']]
        expected = [[' x ', '  y', ''], ['xxx', ' yyyy ', 'zz']]
        self.assertEquals(expected, unify_table(input))

    def testUnifyTablesRemovesEmptyColumns(self):
        input = [['x', '', 'y'], ['xxx', '', 'yyyy', 'zz', '         ']]
        expected = [['x', 'y', ''], ['xxx', 'yyyy', 'zz']]
        self.assertEquals(expected, unify_table(input))

    def testParseDealsWithSpacesAtLineEnd(self):
        input = ['x  y     ', 'a  b ', 'only one']
        expected = [['x', 'y'], ['a', 'b'], ['only one', '']]
        self.assertEquals(expected, parse_table(input))

    def testParseValidTable(self):
        input = ['+-----+----+',
                 '| Foo | Mu |',
                 '+=====+====+',
                 '| x   | y  |',
                 '+-----+----+']
        expect = [['Foo', 'Mu'], ['x', 'y']]
        self.assertEquals(expect, parse_table(input))

    def testParseCorruptedTable(self):
        input = ['+---+---------+',
                 '| Foo | Mu                   |',
                 '+=====+====+',
                 '| x   | This became somewhat larger  |',
                 'blah   | A new line| ',
                 '+-----+----+']
        expect = [['Foo', 'Mu'],
                  ['x\nblah', 'This became somewhat larger\nA new line']]
        self.assertEquals(expect, parse_table(input))

        input = ['+---+---------+',
                 '| Foo | Mu                   |',
                 '+=====+====+',
                 '| x   | This became somewhat larger  |',
                 'blah   | A new line|| ',
                 '+-----+----+']
        expect = [['Foo', 'Mu'],
                  ['x\nblah', 'This became somewhat larger\nA new line']]
        self.assertEquals(expect, parse_table(input))

    def testParseMultiLineFields(self):
        input = """\
+-----+---------------------+
| Foo | Bar                 |
+=====+=====================+
| x   | This is a long line |
|     | that is spread out  |
|     | over multiple lines |
+-----+---------------------+""".split('\n')
        expect = [['Foo', 'Bar'],
                  ['x', 'This is a long line\nthat is spread out\nover multiple lines']]
        self.assertEquals(expect, parse_table(input))

    def testSplitRowIntoLines(self):
        input = ['Foo', 'Bar']
        expect = [['Foo', 'Bar']]
        self.assertEquals(expect, split_row_into_lines(input))
        input = ['One\nTwo\nThree', 'Only one']
        expect = [['One', 'Only one'], ['Two', ''], ['Three', '']]
        self.assertEquals(expect, split_row_into_lines(input))
        input = ['One\n\n\nThree', 'Foo\nBar']
        expect = [['One', 'Foo'], ['', 'Bar'], ['', ''], ['Three', '']]
        self.assertEquals(expect, split_row_into_lines(input))

    def testDrawMultiLineFields(self):
        input = [['Foo', 'Bar'],
                  ['x', 'This is a long line\nthat is spread out\nover multiple lines']]
        expect = """\
+-----+---------------------+
| Foo | Bar                 |
+=====+=====================+
| x   | This is a long line |
|     | that is spread out  |
|     | over multiple lines |
+-----+---------------------+""".split('\n')
        self.assertEquals(expect, draw_table(input))

    def testTableLine(self):
        self.assertEquals('', table_line([], True))
        self.assertEquals('++', table_line([0], True))
        self.assertEquals('+++', table_line([0,0], True))
        self.assertEquals('++-+', table_line([0,1]))
        self.assertEquals('+===+', table_line([3], True))
        self.assertEquals('+===+====+', table_line([3,4], True))
        self.assertEquals('+------------------+---+--------------------+',
                table_line([18,3,20]))

    def testGetColumnWidths(self):
        self.assertEquals([], get_column_widths([[]]))
        self.assertEquals([0], get_column_widths([['']]))
        self.assertEquals([1,2,3], get_column_widths([['x','yy','zzz']]))
        self.assertEquals([3,3,3],
                get_column_widths(
                    [
                        ['x','y','zzz'],
                        ['xxx','yy','z'],
                        ['xx','yyy','zz'],
                    ]))

    def testGetColumnWidthsForMultiLineFields(self):
        self.assertEquals([3,6],
                get_column_widths([['Foo\nBar\nQux',
                                    'This\nis\nreally\nneat!']]))

    def testGetColumnWidthsFromBorderSpec(self):
        input = ['+----+-----+--+-------+',
                 '| xx | xxx |  | xxxxx |',
                 '+====+=====+==+=======+']
        self.assertEquals([2, 3, 0, 5],
            get_column_widths_from_border_spec(input))

    def testPadFields(self):
        table = [['Name', 'Type', 'Description'],
                 ['Lollypop', 'Candy', 'Yummy'],
                 ['Crisps', 'Snacks', 'Even more yummy, I tell you!']]
        expected_padding = [
                 [' Name     ', ' Type   ', ' Description                  '],
                 [' Lollypop ', ' Candy  ', ' Yummy                        '],
                 [' Crisps   ', ' Snacks ', ' Even more yummy, I tell you! ']]
        widths = get_column_widths(table)
        for input, expect in zip(table, expected_padding):
            self.assertEquals(expect, pad_fields(input, widths))

    def testReflowRowContentsWithEnoughWidth(self):
        input = ['Foo\nbar', 'This line\nis spread\nout over\nfour lines.']
        expect = ['Foo bar', 'This line is spread out over four lines.']
        self.assertEquals(expect, reflow_row_contents(input, [99,99]))

    def testReflowRowContentsWithWrapping(self):
        input = ['Foo\nbar', 'This line\nis spread\nout over\nfour lines.']
        expect = ['Foo bar', 'This line is spread\nout over four lines.']
        self.assertEquals(expect, reflow_row_contents(input, [10,20]))

        input = ['Foo\nbar', 'This line\nis spread\nout over\nfour lines.']
        expect = ['Foo bar', 'This\nline\nis\nspread\nout\nover\nfour\nlines.']
        self.assertEquals(expect, reflow_row_contents(input, [10,6]))

    def testReflowRowContentsWithoutRoom(self):
        #self.assertEquals(expect, reflow_row_contents(input))
        pass

    def testDrawTable(self):
        self.assertEquals([], draw_table([]))
        self.assertEquals(['+--+', '|  |', '+==+'], draw_table([['']]))
        self.assertEquals(['+-----+', '| Foo |', '+=====+'],
                draw_table([['Foo']]))
        self.assertEquals(
                ['+-----+----+',
                 '| Foo | Mu |',
                 '+=====+====+',
                 '| x   | y  |',
                 '+-----+----+'],
                draw_table([['Foo', 'Mu'], ['x', 'y']]))


    def testCreateTable(self):
        self.load_fixture_in_vim('default')
        expect = """\
This is paragraph text *before* the table.

+----------+------------------------------------------------------------------------------------------------+
| Column 1 | Column 2                                                                                       |
+==========+================================================================================================+
| Foo      | Put two (or more) spaces as a field separator.                                                 |
+----------+------------------------------------------------------------------------------------------------+
| Bar      | Even very very long lines like these are fine, as long as you do not put in line endings here. |
+----------+------------------------------------------------------------------------------------------------+
| Qux      | This is the last line.                                                                         |
+----------+------------------------------------------------------------------------------------------------+

This is paragraph text *after* the table, with
a line ending.
""".split('\n')
        reformat_table()
        self.assertEquals(expect, vim.current.buffer)

    def testCreateComplexTable(self):
        raw_lines = self.read_fixture('multiline-cells')
        # strip off the last (empty) line from raw_lines (since that line does
        # not belong to the table
        del raw_lines[-1]
        expect = """\
+----------------+---------------------------------------------------------------+
| Feature        | Description                                                   |
+================+===============================================================+
| Ease of use    | Drop dead simple!                                             |
+----------------+---------------------------------------------------------------+
| Foo            | Bar, qux, mux                                                 |
+----------------+---------------------------------------------------------------+
| Predictability | Lorem ipsum dolor sit amet, consectetur adipiscing elit.      |
+----------------+---------------------------------------------------------------+
|                | Nullam congue dapibus aliquet. Integer ut rhoncus leo. In hac |
+----------------+---------------------------------------------------------------+
|                | habitasse platea dictumst. Phasellus pretium iaculis.         |
+----------------+---------------------------------------------------------------+
""".rstrip().split('\n')
        self.assertEquals(expect, draw_table(parse_table(raw_lines)))

    def testReflowTable(self):
        self.load_fixture_in_vim('reflow')
        expect = """\
This is paragraph text *before* the table.

+----------+--------------------------+
| Column 1 | Column 2                 |
+==========+==========================+
| Foo      | Put two (or more) spaces |
|          | as a field separator.    |
+----------+--------------------------+
| Bar      | Even very very long      |
|          | lines like these are     |
|          | fine, as long as you do  |
|          | not put in line endings  |
|          | here.                    |
+----------+--------------------------+
| Qux      | This is the last line.   |
+----------+--------------------------+

This is paragraph text *after* the table, with
a line ending.
""".split('\n')
        reflow_table()
        self.assertEquals(expect, vim.current.buffer)

