KJXQZ
=====

`KJXQZ`_ is an Apache2 licensed collection of `anagram word solver`_ tools.

.. _`KJXQZ`: https://www.kjxqz.com/
.. _`anagram word solver`: https://www.kjxqz.com/

.. image:: https://github.com/grantjenks/kjxqz.com/actions/workflows/integration.yml/badge.svg
   :target: https://github.com/grantjenks/kjxqz.com/actions/workflows/integration.yml

.. image:: https://github.com/grantjenks/kjxqz.com/actions/workflows/release.yml/badge.svg
   :target: https://github.com/grantjenks/kjxqz.com/actions/workflows/release.yml

Quickstart
----------

Installing `KJXQZ`_ is simple with `pip <https://pypi.org/project/pip/>`_::

    $ pip install kjxqz

You can access documentation in the interpreter with Python's built-in `help`
function. The `help` works on modules, classes and methods in `KJXQZ`_.

.. code-block:: python

    >>> import kjxqz
    >>> help(kjxqz)

To build website assets from the packaged word list::

    $ python -m kjxqz

Development
-----------

Install `uv <https://docs.astral.sh/uv/>`_ and sync dev dependencies::

    $ uv sync --extra dev

Run checks and tests::

    $ uv run poe check

Common tasks::

    $ uv run poe fmt
    $ uv run poe test
    $ uv run poe docs
    $ uv run poe build-dist

Publishing
----------

The `release workflow`_ builds distributions and publishes to PyPI using GitHub
Actions Trusted Publishing. Push a tag beginning with ``v`` to trigger release.

.. _`release workflow`: https://github.com/grantjenks/kjxqz.com/actions/workflows/release.yml

References
----------

- `Reference`_

.. _`Reference`: https://www.grantjenks.com/docs/kjxqz/reference.html

Useful Links
------------

- `KJXQZ Documentation`_
- `KJXQZ at PyPI`_
- `KJXQZ at Github`_
- `KJXQZ Issue Tracker`_

.. _`KJXQZ Documentation`: https://www.grantjenks.com/docs/kjxqz/
.. _`KJXQZ at PyPI`: https://pypi.org/project/kjxqz/
.. _`KJXQZ at Github`: https://github.com/grantjenks/kjxqz.com
.. _`KJXQZ Issue Tracker`: https://github.com/grantjenks/kjxqz.com/issues

KJXQZ License
-------------

Copyright 2018-2026 Grant Jenks

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
