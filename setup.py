import io
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

import kjxqz


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


with io.open('README.rst', encoding='UTF-8') as reader:
    readme = reader.read()


setup(
    name='kjxqz',
    version=kjxqz.__version__,
    description='Word list and solver.',
    long_description=readme,
    author='Grant Jenks',
    author_email='contact@grantjenks.com',
    url='http://www.kjxqz.com/',
    packages=['kjxqz'],
    include_package_data=True,
    tests_require=['tox'],
    cmdclass={'test': Tox},
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
