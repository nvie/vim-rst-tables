vim-rst-tables
==============

.. image:: http://stillmaintained.com/nvie/vim-rst-tables.png

.. contents:: **Contents**
   :local:


Installation
------------
1. Install the following python package::

      pip install git+https://github.com/rpuntaie/vim_bridge.git

   This is not yet on PyPI.

2. Clone the git repository::

      git clone git://github.com/nvie/vim-rst-tables.git

3. Source the files in ``.vimrc``::

      source "~/.vim/bundle/vim-rst-tables/ftplugin/rst_tables.vim"

Steps 2 and 3 are implicit if you use a plugin manager (``Vundle.vim`` or ``Dein.vim``)

.. _vim_bridge: http://pypi.python.org/pypi/vim_bridge


Usage
-----

Creating a new table
~~~~~~~~~~~~~~~~~~~~

1. Open a reStructuredText file
2. Create some kind of table outline::

      This is paragraph text *before* the table.

      Column 1  Column 2
      Foo  Put two (or more) spaces as a field separator.
      Bar  Even very very long lines like these are fine, as long as you do not put in line endings here.
      Qux  This is the last line.

      This is paragraph text *after* the table.

2. Put your cursor somewhere in the table.
3. To create the table, press :kbd:`,,o` (or :kbd:`\\o` if vim's
   :kbd:`&lt;Leader&gt;` is set to the default value).  The output will look
   something like this::

      This is paragraph text *before* the table.

      +----------+---------------------------------------------------------+
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


Re-flowing an existing table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, you may have a column that contains enough data that your
table is a little hard to work with.  To fix that kind of problem,
you can define the column width you would prefer, and re-flow your table.

1. Change the number of "---" signs in the top row of your table to match
   the column widths you would prefer.
2. Put your cursor somewhere in the table.
3. Press :kbd:`,,l` to re-flow the table (or :kbd:`\\l` if vim's
   :kbd:`&lt;Leader&gt;` is set to the default value; see also the ``:map``
   command).
