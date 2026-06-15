Testing Guide
=============

Overview
--------

The project uses pytest for automated testing.

Run all tests:

::

    pytest

Run tests with coverage:

::

    pytest --cov=src

Test Categories
---------------

The following markers are used:

``web``
    Flask route and page tests.

``buttons``
    Pull Data and Update Analysis behavior.

``analysis``
    Analysis formatting and statistics rendering.

``db``
    Database insertion and schema tests.

``integration``
    End-to-end workflow tests.

``helpers``
    Helper function unit tests.

Example
-------

Run only integration tests:

::

    pytest -m integration

Run only database tests:

::

    pytest -m db

Fixtures
--------

Common fixtures include:

``client``
    Flask test client.

``db_conn``
    PostgreSQL test database connection.

``fake_rows``
    Sample applicant data used during integration testing.

Test Doubles
------------

The test suite uses:

* Mock scraper responses
* Mock database interactions
* Patched Flask routes
* Fake applicant records

Coverage
--------

The project currently maintains:

::

    100% statement coverage

Coverage is verified automatically through pytest-cov.