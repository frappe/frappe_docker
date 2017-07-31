lxml is a Pythonic, mature binding for the libxml2 and libxslt libraries.  It
provides safe and convenient access to these libraries using the ElementTree
API.

It extends the ElementTree API significantly to offer support for XPath,
RelaxNG, XML Schema, XSLT, C14N and much more.

To contact the project, go to the `project home page
<http://lxml.de/>`_ or see our bug tracker at
https://launchpad.net/lxml

In case you want to use the current in-development version of lxml,
you can get it from the github repository at
https://github.com/lxml/lxml .  Note that this requires Cython to
build the sources, see the build instructions on the project home
page.  To the same end, running ``easy_install lxml==dev`` will
install lxml from
https://github.com/lxml/lxml/tarball/master#egg=lxml-dev if you have
an appropriate version of Cython installed.


After an official release of a new stable series, bug fixes may become
available at
https://github.com/lxml/lxml/tree/lxml-3.8 .
Running ``easy_install lxml==3.8bugfix`` will install
the unreleased branch state from
https://github.com/lxml/lxml/tarball/lxml-3.8#egg=lxml-3.8bugfix
as soon as a maintenance branch has been established.  Note that this
requires Cython to be installed at an appropriate version for the build.

3.8.0 (2017-06-03)
==================

Features added
--------------

* ``ElementTree.write()`` has a new option ``doctype`` that writes out a
  doctype string before the serialisation, in the same way as ``tostring()``.

* GH#220: ``xmlfile`` allows switching output methods at an element level.
  Patch by Burak Arslan.

* LP#1595781, GH#240: added a PyCapsule Python API and C-level API for
  passing externally generated libxml2 documents into lxml.

* GH#244: error log entries have a new property ``path`` with an XPath
  expression (if known, None otherwise) that points to the tree element
  responsible for the error. Patch by Bob Kline.

* The namespace prefix mapping that can be used in ElementPath now injects
  a default namespace when passing a None prefix.

Bugs fixed
----------

* GH#238: Character escapes were not hex-encoded in the ``xmlfile`` serialiser.
  Patch by matejcik.

* GH#229: fix for externally created XML documents.  Patch by Theodore Dubois.

* LP#1665241, GH#228: Form data handling in lxml.html no longer strips the
  option values specified in form attributes but only the text values.
  Patch by Ashish Kulkarni.

* LP#1551797: revert previous fix for XSLT error logging as it breaks
  multi-threaded XSLT processing.

* LP#1673355, GH#233: ``fromstring()`` html5parser failed to parse byte strings.

Other changes
-------------

* The previously undocumented ``docstring`` option in ``ElementTree.write()``
  produces a deprecation warning and will eventually be removed.




