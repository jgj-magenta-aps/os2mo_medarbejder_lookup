#
# Copyright (c) 2017-2018, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""
Helper class to make a number of pre-defined queries into MO
"""

import requests
from anytree import Node


class MoraHelper(object):
    def __init__(self, hostname='localhost'):
        self.host = 'http://' + hostname + '/service/'
        self.cache = {}

    def _split_name(self, name):
        """ Split a name into first and last name.
        Currently just splits at last space, but this might turn out to
        be a too simple rule.
        :param name: The name to split.
        :return: Dict with first and last name separated.
        """
        splitted_name = {'Fornavn': name[:name.rfind(' ')],
                         'Efternavn': name[name.rfind(' '):]}
        return splitted_name

    def _read_node_path(self, node):
        """ Find the full path for a given node
        :param node: The node to find the path for
        :return: List with full path for the node
        """
        path = []
        for sub_node in node.path:
            ou = self.read_organisationsenhed(sub_node.name)
            path += [ou['name']]
        return path

    def _create_fieldnames(self, nodes):
        """ Create a list of fieldnames that has a suitable length
        to accomodate the full tree debth. First names are hard-coded
        the rest are auto-generated
        :param nodes: List of all nodes in tree
        :return: A list of fieldnames
        """
        fieldnames = ['root', 'org', 'sub org']
        for i in range(2, nodes['root'].height):
            fieldnames += [str(i) + 'xsub org']
        return fieldnames

    def _create_path_dict(self, fieldnames, node):
        """ Create a dict with a MO-path to a given node.
        :param fieldnames: The headline for each level of the path.
        :node: The node to find the path for.
        :return: A dict with headlines as keys and nodes as values.
        """
        path = self._read_node_path(node)
        path_dict = {}
        i = 0
        for element in path:
            path_dict[fieldnames[i]] = element
            i += 1
        return path_dict

    def _mo_lookup(self, uuid, url):
        full_url = self.host + url.format(uuid)
        if full_url in self.cache:
            return_dict = self.cache[full_url]
        else:
            return_dict = requests.get(full_url).json()
            self.cache[full_url] = return_dict
        return return_dict

    def read_organisation(self):
        """ Read the main Organisation, all OU's will have this as root.
        Currently reads only one, theroretically more than root org can exist.
        :return: UUID of root organisation
        """
        org_id = self._mo_lookup(uuid=None, url='o')
        return org_id[0]['uuid']

    def read_organisationsenhed(self, uuid):
        """ Return a dict with the data available about an OU
        :param uuid: The UUID of the OU
        :return: Dict with the information about the OU
        """
        org_enhed = self._mo_lookup(uuid, 'ou/{}')
        return org_enhed

    def read_ou_address(self, uuid):
        """ Return a dict with the data available about an OU
        :param uuid: The UUID of the OU
        :return: Dict with the information about the OU
        """
        return_address = {}
        addresses = self._mo_lookup(uuid, 'ou/{}/details/address')
        for address in addresses:
            if address['address_type']['scope'] == 'DAR':
                return_address['Adresse'] = address['name']
        return return_address

    def read_user_address(self, user, username=False, cpr=False):
        """ Read phone number and email from user
        :param user: UUID of the wanted user
        :return: Dict witn phone number and email (if the exists in MO
        """
        addresses = self._mo_lookup(user, 'e/{}/details/address')
        return_address = {}
        for address in addresses:
            if address['address_type']['scope'] == 'PHONE':
                return_address['Telefon'] = address['name']
            if address['address_type']['scope'] == 'EMAIL':
                return_address['E-mail'] = address['name']
        if username or cpr:
            personal_info = self._mo_lookup(user, 'e/{}')
            if username:
                return_address['Brugernavn'] = personal_info['user_key']
            if cpr:
                return_address['CPR-Nummer'] = personal_info['cpr_no']
        return return_address

    def read_organisation_managers(self, org_uuid):
        """ Read the manager of an organisation.
        Currently an exception will be raised if an ou has more than
        one manager.
        :param org_uuid: UUID of the OU to find the manager of
        :return: Returns 0 or 1 manager of the OU.
        """
        manager_list = {}
        managers = self._mo_lookup(org_uuid, 'ou/{}/details/manager')
        # Iterate over all managers, use uuid as key, if more than one
        # distinct uuid shows up in list, rasie an error
        for manager in managers:
            uuid = manager['person']['uuid']
            # Note: We pick the first responsibility, no room for more in list
            # TODO: This is not good enough, we need correct responsibility
            data = {'Navn': manager['person']['name'],
                    'Ansvar': manager['responsibility'][0]['name'],
                    'uuid': uuid
                    }
            manager_list[uuid] = data
        if len(manager_list) == 0:
            manager = {}
        elif len(manager_list) == 1:
            manager = manager_list[uuid]
        elif len(manager_list) > 1:
            # Currently we do not support multiple managers
            print(org_uuid)
            manager = manager_list[uuid]
            # TODO: Fix this...
            # raise Exception('Too many managers')
        return manager

    def read_organisation_people(self, org_uuid, person_type='engagement',
                                 split_name=True):
        """ Read all employees in an ou. If the same employee is listed
        more than once, only the latest listing will be included.
        :param org_uuid: UUID of the OU to find emplyees in.
        :return: The list of emplyoees
        """
        person_list = {}
        persons = self._mo_lookup(org_uuid, 'ou/{}/details/' + person_type)
        for person in persons:
            uuid = person['person']['uuid']
            data = {'Ansættelse gyldig fra': person['validity']['from'],
                    'Ansættelse gyldig til': person['validity']['to'],
                    'Person UUID': uuid,
                    'Org-enhed': person['org_unit']['name'],
                    'Org-enhed UUID': person['org_unit']['uuid'],
                    'Stillingsbetegnelse': person['job_function']['name'],
                    'Engagement UUID': person['uuid']
                    }
            # Finally, add name
            if split_name:
                data.update(self._split_name(person['person']['name']))
            else:
                data['Navn'] = person['person']['name']
            person_list[uuid] = data
        return person_list

    def read_top_units(self, organisation):
        """ Read the ous tha refers directoly to the organisation
        :param organisation: UUID of the organisation
        :return: List of UUIDs of the root OUs in the organisation
        """
        url = self.host + 'o/' + organisation + '/children'
        response = requests.get(url)
        units = response.json()
        return units

    def read_ou_tree(self, org, nodes={}, parent=None):
        """ Recursively find all sub-ou's beneath current node
        :param org: The organisation to start the tree from
        :param nodes: Dict with all modes in the tree
        :param parent: The parent of the current node, None if this is root
        :return: A dict with all nodes in tree, top node is named 'root'
        """
        url = self.host + 'ou/' + org + '/children'
        units = requests.get(url).json()
        if parent is None:
            nodes['root'] = Node(org)
            parent = nodes['root']
        for unit in units:
            uuid = unit['uuid']
            nodes[uuid] = Node(uuid, parent=parent)
            if unit['child_count'] > 0:
                nodes = self.read_ou_tree(uuid, nodes, nodes[uuid])
        return nodes
