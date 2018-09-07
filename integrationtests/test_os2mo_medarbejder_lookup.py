#
# Copyright (c) 2017-2018, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""
Integrationtests for the os2mo/os2datascanner integration
see description in the os2mo_medarbejder_lookup module.

You need to have a running default-install with the supplied
example-data (Fedtmule and Anders And) in order for these tests to succeed
correct the OS2MO setting below to point to that

"""

import unittest

from os2mo_medarbejder_lookup import (
    Os2moMedarbejderLookup
)

OS2MO = "os2mo"

goofy = {
    'E-mail': 'goofy@example.com',
    'cpr_no': '1205320000',
    'name': 'Fedtmule',
    'org': {'name': 'Aarhus ' 'Universitet', 'user_key': 'AU',
            'uuid': '456362c4-0ee4-4e5e-a72c-751239745e62'},
    'user_key': 'fedtmule',
    'uuid': '6ee24785-ee9a-4502-81c2-7697009c9053'
}

andersand = {
    'E-mail': 'bruger@example.com',
    'cpr_no': '0906340000',
    'name': 'Anders And',
    'org': {'name': 'Aarhus ' 'Universitet', 'user_key': 'AU',
            'uuid': '456362c4-0ee4-4e5e-a72c-751239745e62'},
    'user_key': 'andersand',
    'uuid': '53181ed2-f1de-4c4a-a8fd-ab358c2c454a',
    'manager_uuid': '53181ed2-f1de-4c4a-a8fd-ab358c2c454a',
    'ou_uuid': '9d07123e-47ac-4a9a-88c8-da82e3a4bc9e'
}


class TestMedarbejderLookupHttp(unittest.TestCase):

    def setUp(self):
        self.os2mo_medarbejder = Os2moMedarbejderLookup(OS2MO)
        self.os2mo_medarbejder.re_cache_all()
        self.maxDiff = None

    def test_recache_all(self):
        self.assertEqual(self.os2mo_medarbejder.employees_by_email, {
            'bruger@example.com': [andersand],
            'goofy@example.com': [goofy],
        })
        self.assertEqual(self.os2mo_medarbejder.employees_by_firstlast, {
            'Anders And': [andersand],
            'Fedtmule': [goofy],
        })
        self.assertEqual(self.os2mo_medarbejder.employees_by_initials, {
            'AA': [andersand],
            'F': [goofy],
        })
        self.assertEqual(self.os2mo_medarbejder.employees_by_lastfirst, {
            'And, Anders': [andersand],
            'Fedtmule': [goofy],
        })
        self.assertEqual(self.os2mo_medarbejder.employees_by_phone, {
            None: [andersand, goofy]
        })
        self.assertEqual(self.os2mo_medarbejder.employees_by_username, {
            'andersand': [andersand],
            'fedtmule':  [goofy],
        })

    def test_get_methods(self):
        self.assertEqual(
            self.os2mo_medarbejder.by_email('bruger@example.com'),
            [andersand]
        )
        self.assertEqual(
            self.os2mo_medarbejder.by_firstlast('Anders And'),
            [andersand]
        )
        self.assertEqual(
            self.os2mo_medarbejder.by_initials('AA'),
            [andersand]
        )
        self.assertEqual(
            self.os2mo_medarbejder.by_lastfirst('And, Anders'),
            [andersand]
        )
        self.assertEqual(
            self.os2mo_medarbejder.by_phone(None),
            [andersand, goofy]
        )
        self.assertEqual(
            self.os2mo_medarbejder.by_username('andersand'),
            [andersand]
        )
        self.assertEqual(
            self.os2mo_medarbejder.by_username('andersine'),
            []
        )
