from __future__ import absolute_import
# copyright openpyxl 2010-2015


def namespaced(obj, tagname, namespace=None):
    """
    Utility to create a namespaced tag for an object
    """

    namespace = getattr(obj, "namespace", namespace)
    if namespace is not None:
        tagname = "{%s}%s" % (namespace, tagname)
    return tagname
