# -*- coding: utf-8 -*-

"""
Custom Django test runner that runs the tests using the
XMLTestRunner class.

This script shows how to use the XMLTestRunner in a Django project. To learn
how to configure a custom TestRunner in a Django project, please read the
Django docs website.
"""

import xmlrunner
import os.path
from django.conf import settings
from django.test.runner import DiscoverRunner


class XMLTestRunner(DiscoverRunner):

    def run_suite(self, suite, **kwargs):
        dummy = kwargs  # unused
        verbosity = getattr(settings, 'TEST_OUTPUT_VERBOSE', 1)
        # XXX: verbosity = self.verbosity
        if isinstance(verbosity, bool):
            verbosity = (1, 2)[verbosity]
        descriptions = getattr(settings, 'TEST_OUTPUT_DESCRIPTIONS', False)
        output_dir = getattr(settings, 'TEST_OUTPUT_DIR', '.')
        single_file = getattr(settings, 'TEST_OUTPUT_FILE_NAME', None)

        kwargs = dict(
            verbosity=verbosity, descriptions=descriptions,
            failfast=self.failfast)
        if single_file is not None:
            file_path = os.path.join(output_dir, single_file)
            with open(file_path, 'wb') as xml:
                return xmlrunner.XMLTestRunner(
                    output=xml, **kwargs).run(suite)
        else:
            return xmlrunner.XMLTestRunner(
                output=output_dir, **kwargs).run(suite)
