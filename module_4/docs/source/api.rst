API Reference
=============

load_data
---------

.. automodule:: load_data
   :members:
   :undoc-members:
   :show-inheritance:

query_data
----------

.. automodule:: query_data
   :members:
   :undoc-members:
   :show-inheritance:


Additional ETL Components
-------------------------

The ETL pipeline also includes:

* scraper.py
* run_scrape_and_standardize.py
* llm_hosting/app.py

These components are invoked by query_data.py during the Pull Data workflow and are responsible for scraping, standardizing, and loading applicant records.