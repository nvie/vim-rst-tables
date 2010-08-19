Simple example
==============
Set your cursor inside the following paragraph and type ",,c":

Feature  Description
Easy  It's soo easy, man.
Predictable        Amount of spaces doesn't matter.
Repeatable  It can be repeated.
Flexible  Even spaces at the end of a line are fine.                 

Then, the paragraph should turn into:

+=============+============================================+
| Feature     | Description                                |
+=============+============================================+
| Easy        | It's soo easy, man.                        |
+-------------+--------------------------------------------+
| Predictable | Amount of spaces doesn't matter.           |
+-------------+--------------------------------------------+
| Repeatable  | It can be repeated.                        |
+-------------+--------------------------------------------+
| Flexible    | Even spaces at the end of a line are fine. |
+-------------+--------------------------------------------+

Then, fix the "soo" to become "so" and insert the word "really" between
"doesn't" and "matter".  Finally, rename "Easy" to "Super easy", so it looks
like this:

+=============+==================================+
| Feature     | Description                      |
+=============+==================================+
| Super easy        | It's so easy, man.              |
+-------------+----------------------------------+
| Predictable | Amount of spaces doesn't really matter. |
+-------------+----------------------------------+
| Repeatable  | It can be repeated.              |
+-------------+----------------------------------+

Then, set your cursor inside the table again, and type ,,f to reformat the
table.


A more complex example
======================

Feature| Description                                 |
Ease of use | Drop dead simple!
Foo | Bar, qux, mux
Predictability | Deploykdj sfkljsdjf ljdflsk jsdflkj dsflkj sdlkj dfslkj
| | dfslkjds flkdjsfl sdfjlk jdfslk djsfl dfjslk jsdflk jfdslk jdfslkds fjlkds
| | jldkfj ldfsjlsd jldsf jlkjds flds fjlk jdflk jdsflj dslfjs dlfj sdflkj sdlfj
| |dfslkjds flkdjsfl sdfjlk jdfslk djsfl dfjslk jsdflk jfdslk jdfslkds fjlkds
| |jldkfj ldfsjlsd jldsf jlkjds flds fjlk jdflk jdsflj dslfjs dlfj sdflkj sdlfj
| |dfslkjds flkdjsfl sdfjlk jdfslk djsfl dfjslk jsdflk jfdslk jdfslkds fjlkds
| |jldkfj ldfsjlsd jldsf jlkjds flds fjlk jdflk jdsflj dslfjs dlfj sdflkj sdlfj | 
| |ldfsj dlfsj dfskjdfs ldsfj 

And some para-text below it.
