#
# Copyright (c) 2017-2018, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""
Find employees by different keys (phone email etc.)
lookup = Os2moMedarbejderLookup("os2mo")
employee = lookup.by_email('bruger@example.com')
Find employees manager by
manager = lookup.by_uuid(employee["manager_uuid"])

"""

import queue
import threading
from .mora_helpers import MoraHelper
from anytree import PreOrderIter


class Os2moMedarbejderLookup(MoraHelper):
    def __init__(self, hostname):
        super(Os2moMedarbejderLookup, self).__init__(hostname)
        self.employees_by_username = {}
        self.employees_by_firstlast = {}
        self.employees_by_lastfirst = {}
        self.employees_by_initials = {}
        self.employees_by_email = {}
        self.employees_by_phone = {}
        self.employees_by_uuid = {}

    def read_user_address(self, user):
        """ Read phone number and email into user
        :param user: UUID of the wanted user
        :return: Dict with phone number and email (if the exists in MO
        """
        addresses = self._mo_lookup(user, 'e/{}/details/address')
        personal_info = self._mo_lookup(user, 'e/{}')
        for address in addresses:
            if address['address_type']['scope'] == 'PHONE':
                personal_info['Telefon'] = address['name']
            if address['address_type']['scope'] == 'EMAIL':
                personal_info['E-mail'] = address['name']
        return personal_info

    def cache_user(self, user_queue):
        """ User has been cached in _mo_lookup, and this method makes a lot of
        pointers to that cached value making it possible to immediately look up
        emplyoee by different keys
        """
        while not user_queue.empty():
            user = user_queue.get_nowait()
            user = self.read_user_address(user['uuid'])

            # by username / uuid

            self.employees_by_username.setdefault(
                user["user_key"],
                []).append(user)

            self.employees_by_uuid.setdefault(
                user["uuid"],
                []).append(user)

            # initials / name parts

            initials = "".join([x[0] for x in user["name"].split(" ")]).upper()
            split_name = user["name"].rsplit(maxsplit=1)

            self.employees_by_initials.setdefault(
                initials,
                []).append(user)

            self.employees_by_firstlast.setdefault(
                user["name"],
                []).append(user)

            self.employees_by_lastfirst.setdefault(
                ", ".join(reversed(split_name)),
                []).append(user)

            # addresses

            self.employees_by_email.setdefault(
                user.get("E-mail"),
                []).append(user)

            self.employees_by_phone.setdefault(
                user.get("Telefon"),
                []).append(user)

            user_queue.task_done()

    def pre_cache_employee_relations(self):
        """ Create the tree, traverse it, making flat lookup tables
        """
        org = self.read_organisation()
        top_units = self.read_top_units(org)
        self.nodes = self.read_ou_tree(top_units[0]['uuid'])

        # organization unit and manager

        for node in PreOrderIter(self.nodes['root']):
            ou = self.read_organisationsenhed(node.name)
            manager = self.read_organisation_managers(node.name)

            for employee_uuid in self.read_organisation_people(node.name):
                employee = self.employees_by_uuid[employee_uuid][0]
                employee["manager_uuid"] = manager.get("uuid")
                employee["ou_uuid"] = ou.get("uuid")

    def pre_cache_users(self):
        """ Pre-read all users in organisation, can give a significant
        performance enhancement, since this can be multi-threaded. Only
        works for the complete organisation.
        """
        org_id = self.read_organisation()
        user_queue = queue.Queue()
        for user in self._mo_lookup(org_id, 'o/{}/e?limit=99999')['items']:
            user_queue.put(user)
        workers = {}
        for i in range(0, 5):
            workers[i] = threading.Thread(target=self.cache_user,
                                          args=[user_queue])
            workers[i].start()
        user_queue.join()

    def by_username(self, key):
        return self.employees_by_username.get(key, [])

    def by_firstlast(self, key):
        return self.employees_by_firstlast.get(key, [])

    def by_lastfirst(self, key):
        return self.employees_by_lastfirst.get(key, [])

    def by_initials(self, key):
        return self.employees_by_initials.get(key, [])

    def by_email(self, key):
        return self.employees_by_email.get(key, [])

    def by_phone(self, key):
        return self.employees_by_phone.get(key, [])

    def by_uuid(self, key):
        return self.employees_by_uuid.get(key, [])

    def re_cache_all(self):
        self.cache = {}
        self.employees_by_username = {}
        self.employees_by_firstlast = {}
        self.employees_by_lastfirst = {}
        self.employees_by_initials = {}
        self.employees_by_email = {}
        self.employees_by_phone = {}
        self.employees_by_uuid = {}
        self.pre_cache_users()
        self.pre_cache_employee_relations()
