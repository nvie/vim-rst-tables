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

import unittest
from rst_tables import get_table_bounds, create_table, parse_table, \
                          draw_table, table_line, get_column_widths, \
                          pad_fields

class TestRSTTableFormatter(unittest.TestCase):

    def setUp(self):
        self.plain = """\
This is paragraph text *before* the table.

Column 1  Column 2
Foo  Put two (or more) spaces as a field separator.
Bar  Even very very long lines like these are fine, as long as you do not put in line endings here.
Qux  This is the last line.

This is paragraph text *after* the table, with
a line ending.
"""

    def tearDown(self):
        pass

    def testGetBounds(self):
        input = self.plain
        vim.current.buffer = input.split('\n')
        vim.current.window.cursor = (4, 0)
        self.assertEquals((3, 6), get_table_bounds())

    def testGetBoundsOnBeginOfFile(self):
        input = self.plain
        vim.current.buffer = input.split('\n')
        vim.current.window.cursor = (1, 0)
        self.assertEquals((1, 1), get_table_bounds())

    def testGetBoundsOnEndOfFile(self):
        input = self.plain
        vim.current.buffer = input.split('\n')
        vim.current.window.cursor = (8, 0)
        self.assertEquals((8, 9), get_table_bounds())

    def testParseSimpleTable(self):
        self.assertEquals([['x y z']], parse_table(['x y z']))
        self.assertEquals([['x', 'y z']], parse_table(['x  y z']))
        self.assertEquals([['x', 'y', 'z']], parse_table(['x  y          z']))

    def testParseTable(self):
        input = self.plain
        vim.current.buffer = input.split('\n')
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

    def testParseDealsWithSpacesAtLineEnd(self):
        input = ['x  y     ', 'a  b ', 'only one']
        expected = [['x', 'y'], ['a', 'b'], ['only one', '']]
        self.assertEquals(expected, parse_table(input))

    def testParseValidTable(self):
        input = ['+=====+====+',
                 '| Foo | Mu |',
                 '+=====+====+',
                 '| x   | y  |',
                 '+-----+----+']
        expect = [['Foo', 'Mu'], ['x', 'y']]
        self.assertEquals(expect, parse_table(input))

    def testParseCorruptedTable(self):
        input = ['+===+-----====+',
                 '| Foo | Mu                   |',
                 '+=====+====+',
                 '| x   | This became somewhat larger  |',
                 'blah   | A new line| ',
                 '+-----+----+']
        expect = [['Foo', 'Mu'],
                  ['x', 'This became somewhat larger'],
                  ['blah', 'A new line']]
        self.assertEquals(expect, parse_table(input))

        input = ['+===+-----====+',
                 '| Foo | Mu                   |',
                 '+=====+====+',
                 '| x   | This became somewhat larger  |',
                 'blah   | A new line|| ',
                 '+-----+----+']
        expect = [['Foo', 'Mu', ''],
                  ['x', 'This became somewhat larger', ''],
                  ['blah', 'A new line', '']]
        self.assertEquals(expect, parse_table(input))

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

    def testPadFields(self):
        table = [['Name', 'Type', 'Description'],
                 ['Lollypop', 'Candy', 'Yummy'],
                 ['Crisps', 'Snacks', 'Even more yummy, I tell you!']]
        expected_padding = [
                 [' Name     ', ' Type   ', ' Description                  '],
                 [' Lollypop ', ' Candy  ', ' Yummy                        '],
                 [' Crisps   ', ' Snacks ', ' Even more yummy, I tell you! ']]
        self.assertEquals(expected_padding, pad_fields(table))


    def testDrawTable(self):
        self.assertEquals([], draw_table([]))
        self.assertEquals(['+==+', '|  |', '+==+'], draw_table([['']]))
        self.assertEquals(['+=====+', '| Foo |', '+=====+'],
                draw_table([['Foo']]))
        self.assertEquals(
                ['+=====+====+',
                 '| Foo | Mu |',
                 '+=====+====+',
                 '| x   | y  |',
                 '+-----+----+'],
                draw_table([['Foo', 'Mu'], ['x', 'y']]))

    def testCreateTable(self):
        input = self.plain
        expect = """\
This is paragraph text *before* the table.

+==========+================================================================================================+
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
        vim.current.buffer = input.split('\n')
        vim.current.window.cursor = (4, 10)
        create_table()
        self.assertEquals(expect, vim.current.buffer)
