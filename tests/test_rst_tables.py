""" Run tests with

pytest tests
"""

import re

# Mock out the vim library
from os.path import join as pjoin, dirname, abspath
import sys
ROOT = abspath(pjoin(dirname(__file__), '..'))
MOD_NAME = 'rst_tables'
VIM_PATH = pjoin(ROOT, 'ftplugin', MOD_NAME + '.vim')
sys.path.insert(0, pjoin(ROOT, 'tests', 'mocks'))

import vim
import mock


VIMVAR = {'expand("<sfile>")': VIM_PATH,
          '&encoding': 'utf-8'}

def fake_eval(x):
    global VIMVAR
    return VIMVAR[x]

vim.eval = fake_eval
vim.current = mock.Mock()

# Read Python code in rst_tables, make into a module.
# https://stackoverflow.com/questions/5362771/how-to-load-a-module-from-code-in-a-string
from types import ModuleType
with open(VIM_PATH) as fobj:
    content = fobj.read()
python_code = re.search(r'^Python << endpython(.*)^endpython',
                        content, flags=re.M | re.S).groups()[0]
mod = ModuleType(MOD_NAME)
sys.modules[MOD_NAME] = mod
exec(python_code, mod.__dict__)

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
        self.assertEqual((3, 6, ''), get_table_bounds())

    def testGetBoundsOnBeginOfFile(self):
        self.load_fixture_in_vim('default')
        vim.current.window.cursor = (1, 0)
        self.assertEqual((1, 1, ''), get_table_bounds())

    def testGetBoundsOnEndOfFile(self):
        self.load_fixture_in_vim('default')
        vim.current.window.cursor = (8, 0)
        self.assertEqual((8, 9, ''), get_table_bounds())

    def testJoinSimpleRows(self):
        input_rows = [['x', 'y', 'z'], ['foo', 'bar']]
        expected = ['x\nfoo', 'y\nbar', 'z']
        self.assertEqual(expected, join_rows(input_rows))

        input_rows.append(['apple', '', 'pear'])
        expected = ['x foo apple', 'y bar', 'z pear']
        self.assertEqual(expected, join_rows(input_rows, sep=' '))

    def testPartitionRawLines(self):
        self.assertEqual([], partition_raw_lines([]))
        self.assertEqual([['']], partition_raw_lines(['']))
        self.assertEqual(
                [['foo'], ['bar']],
                partition_raw_lines(['foo', 'bar']))
        self.assertEqual(
                [['foo'], ['bar']],
                partition_raw_lines(['foo', '+----+', 'bar']))
        self.assertEqual(
                [['foo', 'bar'], ['baz']],
                partition_raw_lines(['+-----+', 'foo', 'bar', '----', 'baz']))

    def testParseSimpleTable(self):
        self.assertEqual([['x y z']], parse_table(['x y z']))
        self.assertEqual([['x', 'y z']], parse_table(['x  y z']))
        self.assertEqual([['x', 'y', 'z']], parse_table(['x  y          z']))

    def testParseTable(self):
        self.load_fixture_in_vim('default')
        expected = [
                ['Column 1', 'Column 2'],
                ['Foo', 'Put two (or more) spaces as a field separator.'],
                ['Bar', 'Even very very long lines like these are fine, as long as you do not put in line endings here.'],
                ['Qux', 'This is the last line.'],
                ]
        self.assertEqual(expected, parse_table(vim.current.buffer[2:6]))

    def testParseTableUnifiesColumns(self):
        input = ['x  y', 'a  b    c', 'only one']
        expected = [['x', 'y', ''], ['a', 'b', 'c'], ['only one', '', '']]
        self.assertEqual(expected, parse_table(input))

    def testUnifyTables(self):
        input = [[' x ', '  y'], ['xxx', ' yyyy ', 'zz']]
        expected = [[' x ', '  y', ''], ['xxx', ' yyyy ', 'zz']]
        self.assertEqual(expected, unify_table(input))

    def testUnifyTablesRemovesEmptyColumns(self):
        input = [['x', '', 'y'], ['xxx', '', 'yyyy', 'zz', '         ']]
        expected = [['x', 'y', ''], ['xxx', 'yyyy', 'zz']]
        self.assertEqual(expected, unify_table(input))

    def testParseDealsWithSpacesAtLineEnd(self):
        input = ['x  y     ', 'a  b ', 'only one']
        expected = [['x', 'y'], ['a', 'b'], ['only one', '']]
        self.assertEqual(expected, parse_table(input))

    def testParseValidTable(self):
        input = ['+-----+----+',
                 '| Foo | Mu |',
                 '+=====+====+',
                 '| x   | y  |',
                 '+-----+----+']
        expect = [['Foo', 'Mu'], ['x', 'y']]
        self.assertEqual(expect, parse_table(input))

    def testParseCorruptedTable(self):
        input = ['+---+---------+',
                 '| Foo | Mu                   |',
                 '+=====+====+',
                 '| x   | This became somewhat larger  |',
                 'blah   | A new line| ',
                 '+-----+----+']
        expect = [['Foo', 'Mu'],
                  ['x\nblah', 'This became somewhat larger\nA new line']]
        self.assertEqual(expect, parse_table(input))

        input = ['+---+---------+',
                 '| Foo | Mu                   |',
                 '+=====+====+',
                 '| x   | This became somewhat larger  |',
                 'blah   | A new line|| ',
                 '+-----+----+']
        expect = [['Foo', 'Mu'],
                  ['x\nblah', 'This became somewhat larger\nA new line']]
        self.assertEqual(expect, parse_table(input))

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
        self.assertEqual(expect, parse_table(input))

    def testSplitRowIntoLines(self):
        input = ['Foo', 'Bar']
        expect = [['Foo', 'Bar']]
        self.assertEqual(expect, split_row_into_lines(input))
        input = ['One\nTwo\nThree', 'Only one']
        expect = [['One', 'Only one'], ['Two', ''], ['Three', '']]
        self.assertEqual(expect, split_row_into_lines(input))
        input = ['One\n\n\nThree', 'Foo\nBar']
        expect = [['One', 'Foo'], ['', 'Bar'], ['', ''], ['Three', '']]
        self.assertEqual(expect, split_row_into_lines(input))

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
        self.assertEqual(expect, draw_table('', input))

    def testTableLine(self):
        self.assertEqual('', table_line([], True))
        self.assertEqual('++', table_line([0], True))
        self.assertEqual('+++', table_line([0,0], True))
        self.assertEqual('++-+', table_line([0,1]))
        self.assertEqual('+===+', table_line([3], True))
        self.assertEqual('+===+====+', table_line([3,4], True))
        self.assertEqual('+------------------+---+--------------------+',
                table_line([18,3,20]))

    def testGetColumnWidths(self):
        self.assertEqual([], get_column_widths([[]]))
        self.assertEqual([0], get_column_widths([['']]))
        self.assertEqual([1,2,3], get_column_widths([['x','yy','zzz']]))
        self.assertEqual([3,3,3],
                get_column_widths(
                    [
                        ['x','y','zzz'],
                        ['xxx','yy','z'],
                        ['xx','yyy','zz'],
                    ]))

    def testGetColumnWidthsForMultiLineFields(self):
        self.assertEqual([3,6],
                get_column_widths([['Foo\nBar\nQux',
                                    'This\nis\nreally\nneat!']]))

    def testGetColumnWidthsFromBorderSpec(self):
        input = ['+----+-----+--+-------+',
                 '| xx | xxx |  | xxxxx |',
                 '+====+=====+==+=======+']
        self.assertEqual([2, 3, 0, 5],
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
            self.assertEqual(expect, pad_fields(input, widths))

    def testReflowRowContentsWithEnoughWidth(self):
        input = ['Foo\nbar', 'This line\nis spread\nout over\nfour lines.']
        expect = ['Foo bar', 'This line is spread out over four lines.']
        self.assertEqual(expect, reflow_row_contents(input, [99,99]))

    def testReflowRowContentsWithWrapping(self):
        input = ['Foo\nbar', 'This line\nis spread\nout over\nfour lines.']
        expect = ['Foo bar', 'This line is spread\nout over four lines.']
        self.assertEqual(expect, reflow_row_contents(input, [10,20]))

        input = ['Foo\nbar', 'This line\nis spread\nout over\nfour lines.']
        expect = ['Foo bar', 'This\nline\nis\nspread\nout\nover\nfour\nlines.']
        self.assertEqual(expect, reflow_row_contents(input, [10,6]))

    def testReflowRowContentsWithoutRoom(self):
        #self.assertEqual(expect, reflow_row_contents(input))
        pass

    def testDrawTable(self):
        self.assertEqual([], draw_table('', []))
        self.assertEqual(['+--+', '|  |', '+==+'], draw_table('', [['']]))
        self.assertEqual(['+-----+', '| Foo |', '+=====+'],
                draw_table('', [['Foo']]))
        self.assertEqual(
                ['+-----+----+',
                 '| Foo | Mu |',
                 '+=====+====+',
                 '| x   | y  |',
                 '+-----+----+'],
                draw_table('', [['Foo', 'Mu'], ['x', 'y']]))


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
        self.assertEqual(expect, vim.current.buffer)

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
        self.assertEqual(expect, draw_table('', parse_table(raw_lines)))

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
        self.assertEqual(expect, vim.current.buffer)

