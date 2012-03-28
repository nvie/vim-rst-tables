vim-rst-tables
==============

.. image:: http://stillmaintained.com/nvie/vim-rst-tables.png

Installation
------------
1. Install the following packages from PyPI:

   - vim_bridge_:  This is required for the vim plugin scripts, to call
     directly into Python functions.

2. Clone the git repository::

       git clone git://github.com/nvie/vim-rst-tables.git
       cd vim-rst-tables

3. Copy the file ``ftplugin/rst_tables.vim`` to your ``~/.vim/ftplugin``
   directory

.. _vim_bridge: http://pypi.python.org/pypi/vim_bridge


Usage
-----
1. Open a reStructuredText file
2. Create some kind of table outline::

      This is paragraph text *before* the table.

      Column 1  Column 2
      Foo  Put two (or more) spaces as a field separator.
      Bar  Even very very long lines like these are fine, as long as you do not put in line endings here.
      Qux  This is the last line.

      This is paragraph text *after* the table.

2. Put your cursor somewhere in the table.
3. Press ``,,f`` (to create the table).  The output will look something like
   this::

      This is paragraph text *before* the table.

      +==========+=========================================================+
      | Column 1 | Column 2                                                |
      +==========+=========================================================+
      | Foo      | Put two (or more) spaces as a field separator.          |
      +----------+---------------------------------------------------------+
      | Bar      | Even very very long lines like these are fine, as long  |
      |          | as you do not put in line endings here.                 |
      +----------+---------------------------------------------------------+
      | Qux      | This is the last line.                                  |
      +----------+---------------------------------------------------------+

      This is paragraph text *after* the table.