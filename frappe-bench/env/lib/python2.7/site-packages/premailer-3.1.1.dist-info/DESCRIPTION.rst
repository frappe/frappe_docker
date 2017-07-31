premailer
=========

|Travis|

|Coverage Status|

Looking for sponsors
--------------------

This project is actively looking for corporate sponsorship. If you want
to help making this an active project consider `pinging
Peter <http://www.peterbe.com/contact>`__ and we can talk about putting
up logos and links to your company.

Python versions
---------------

Our
`tox.ini <https://github.com/peterbe/premailer/blob/master/tox.ini>`__
makes sure premailer works in:

-  Python 2.6
-  Python 2.7
-  Python 3.3
-  Python 3.4
-  Python 3.5
-  PyPy

Turns CSS blocks into style attributes
--------------------------------------

When you send HTML emails you can't use style tags but instead you have
to put inline ``style`` attributes on every element. So from this:

.. code:: html

    <html>
    <style type="text/css">
    h1 { border:1px solid black }
    p { color:red;}
    </style>
    <h1 style="font-weight:bolder">Peter</h1>
    <p>Hej</p>
    </html>

You want this:

.. code:: html

    <html>
    <h1 style="font-weight:bolder; border:1px solid black">Peter</h1>
    <p style="color:red">Hej</p>
    </html>

premailer does this. It parses an HTML page, looks up ``style`` blocks
and parses the CSS. It then uses the ``lxml.html`` parser to modify the
DOM tree of the page accordingly.

Getting started
---------------

If you haven't already done so, install ``premailer`` first:

::

    $ pip install premailer

Next, the most basic use is to use the shortcut function, like this:

::

    >>> from premailer import transform
    >>> print transform("""
    ...         <html>
    ...         <style type="text/css">
    ...         h1 { border:1px solid black }
    ...         p { color:red;}
    ...         p::first-letter { float:left; }
    ...         </style>
    ...         <h1 style="font-weight:bolder">Peter</h1>
    ...         <p>Hej</p>
    ...         </html>
    ... """)
    <html>
    <head></head>
    <body>
        <h1 style="font-weight:bolder; border:1px solid black">Peter</h1>
        <p style="color:red">Hej</p>
    </body>
    </html>

For more advanced options, check out the code of the ``Premailer`` class
and all its options in its constructor.

You can also use premailer from the command line by using his main
module.

::

    $ python -m premailer -h
    usage: python -m premailer [options]

    optional arguments:
    -h, --help            show this help message and exit
    -f [INFILE], --file [INFILE]
                          Specifies the input file. The default is stdin.
    -o [OUTFILE], --output [OUTFILE]
                          Specifies the output file. The default is stdout.
    --base-url BASE_URL
    --remove-internal-links PRESERVE_INTERNAL_LINKS
                          Remove links that start with a '#' like anchors.
    --exclude-pseudoclasses
                          Pseudo classes like p:last-child', p:first-child, etc
    --preserve-style-tags
                          Do not delete <style></style> tags from the html
                          document.
    --remove-star-selectors
                          All wildcard selectors like '* {color: black}' will be
                          removed.
    --remove-classes      Remove all class attributes from all elements
    --strip-important     Remove '!important' for all css declarations.
    --method METHOD       The type of html to output. 'html' for HTML, 'xml' for
                          XHTML.
    --base-path BASE_PATH
                          The base path for all external stylsheets.
    --external-style EXTERNAL_STYLES
                          The path to an external stylesheet to be loaded.
    --disable-basic-attributes DISABLE_BASIC_ATTRIBUTES
                          Disable provided basic attributes (comma separated)
    --disable-validation  Disable CSSParser validation of attributes and values
    --pretty              Pretty-print the outputted HTML.

A basic example:

::

    $ python -m premailer --base-url=http://google.com/ -f newsletter.html
    <html>
    <head><style>.heading { color:red; }</style></head>
    <body><h1 class="heading" style="color:red"><a href="http://google.com/">Title</a></h1></body>
    </html>

The command line interface supports standard input.

::

    $ echo '<style>.heading { color:red; }</style><h1 class="heading"><a href="/">Title</a></h1>' | python -m premailer --base-url=http://google.com/
    <html>
    <head><style>.heading { color:red; }</style></head>
    <body><h1 class="heading" style="color:red"><a href="http://google.com/">Title</a></h1></body>
    </html>

Turning relative URLs into absolute URLs
----------------------------------------

Another thing premailer can do for you is to turn relative URLs (e.g.
"/some/page.html" into "http://www.peterbe.com/some/page.html"). It does
this to all ``href`` and ``src`` attributes that don't have a ``://``
part in it. For example, turning this:

.. code:: html

    <html>
    <body>
    <a href="/">Home</a>
    <a href="page.html">Page</a>
    <a href="http://crosstips.org">External</a>
    <img src="/folder/">Folder</a>
    </body>
    </html>

Into this:

.. code:: html

    <html>
    <body>
    <a href="http://www.peterbe.com/">Home</a>
    <a href="http://www.peterbe.com/page.html">Page</a>
    <a href="http://crosstips.org">External</a>
    <img src="http://www.peterbe.com/folder/">Folder</a>
    </body>
    </html>

by using ``transform('...', base_url='http://www.peterbe.com/')``.

Ignore certain ``<style>`` or ``<link>`` tags
---------------------------------------------

Suppose you have a style tag that you don't want to have processed and
transformed you can simply set a data attribute on the tag like:

.. code:: html

    <head>
    <style>/* this gets processed */</style>
    <style data-premailer="ignore">/* this gets ignored */</style>
    </head>

That tag gets completely ignored except when the HTML is processed, the
attribute ``data-premailer`` is removed.

It works equally for a ``<link>`` tag like:

.. code:: html

    <head>
    <link rel="stylesheet" href="foo.css" data-premailer="ignore">
    </head>

HTML attributes created additionally
------------------------------------

Certain HTML attributes are also created on the HTML if the CSS contains
any ones that are easily translated into HTML attributes. For example,
if you have this CSS: ``td { background-color:#eee; }`` then this is
transformed into ``style="background-color:#eee"`` AND as an HTML
attribute ``bgcolor="#eee"``.

Having these extra attributes basically as a "back up" for really shit
email clients that can't even take the style attributes. A lot of
professional HTML newsletters such as Amazon's use this. You can disable
some attributes in ``disable_basic_attributes``.


Capturing logging from ``cssutils``
-----------------------------------

`cssutils <https://pypi.python.org/pypi/cssutils/>`__ is the library that
``premailer`` uses to parse CSS. It will use the python ``logging`` module
to mention all issues it has with parsing your CSS. If you want to capture
this, you have to pass in ``cssutils_logging_handler`` and
``cssutils_logging_level`` (optional). For example like this:

.. code:: python

    >>> import logging
    >>> import premailer
    >>> from io import StringIO
    >>> mylog = StringIO()
    >>> myhandler = logging.StreamHandler(mylog)
    >>> p = premailer.Premailer("""
    ...         <html>
    ...         <style type="text/css">
    ...         @keyframes foo { from { opacity: 0; } to { opacity: 1; } }
    ...         </style>
    ...         <p>Hej</p>
    ...         </html>
    ... """,
    ... cssutils_logging_handler=myhandler,
    ... cssutils_logging_level=logging.INFO)
    >>> result = p.transform()
    >>> mylog.getvalue()
    'CSSStylesheet: Unknown @rule found. [2:1: @keyframes]\n'

Running tests with tox
----------------------

To run ``tox`` you don't need to have all available Python versions
installed because it will only work on those you have. To use ``tox``
first install it:

::

    pip install tox

Then simply start it with:

::

    tox

Donations aka. the tip jar
--------------------------

If you enjoy, benefit and want premailer to continue to be an actively
maintained project please consider supporting me on
`Gratipay <https://gratipay.com/peterbe/>`__.

|Gratipay|

.. |Travis| image:: https://travis-ci.org/peterbe/premailer.png?branch=master
   :target: https://travis-ci.org/peterbe/premailer
.. |Coverage Status| image:: https://coveralls.io/repos/peterbe/premailer/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/peterbe/premailer?branch=master
.. |Gratipay| image:: https://img.shields.io/gratipay/peterbe.svg
   :target: https://gratipay.com/peterbe/



