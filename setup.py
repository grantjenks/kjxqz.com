from setuptools import Command, setup
from setuptools.command.test import test as TestCommand

import kjxqz


class Deploy(Command):
    description = 'copy website files to host'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        filenames = [
            'www/index.html',
            'www/dawg.js',
            'www/service-worker.js',
            'nginx.conf',
        ]
        remote = 'magnesium:/srv/www/www.kjxqz.com/'
        for filename in filenames:
            self.spawn(['scp', filename, remote + filename])
        self.spawn(['ssh', 'magnesium', 'sudo', 'nginx', '-s', 'reload'])


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        exit(errno)


with open('README.rst') as reader:
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
    cmdclass={'deploy': Deploy, 'test': Tox},
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
)
