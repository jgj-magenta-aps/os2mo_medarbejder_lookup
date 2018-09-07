from setuptools import setup, find_packages
import sys, os

version = '0.0.1'

setup(name='os2mo_medarbejder_lookup',
      version=version,
      description="lookup employees and their managers in os2mo",
      long_description="""\
lookup employees and their managers in os2mo, initially to be used from os2datascanner""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='os2mo os2webscanner',
      author='J\xc3\xb8rgen G\xc3\xa5rdsted J\xc3\xb8rgensen',
      author_email='jgj@magenta-aps.dk',
      url='',
      license='MPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
