# jhu_software_concepts
Modern Software Concepts in Python
Module 1: Personal Website
Created by Raul Perez

--------------------------
PROJECT DESCRIPTION
--------------------------

This is a personal website that utilizes Flask web framework in Python, blueprints, and cascading style sheets (CSS) for development.
The site is static and includes:
- Multiple pages
    - Home Page
    - Projects and Publications Page
    - My Contact Information Page
- Navigation bar 
- Relative images on each Page and texts
- Custom CSS file that organizes and displays the content for each page.
- Links to external websites

------------------------- 
PROJECT REQUIREMENTS
-------------------------
SHALL use Flask as your web framework
SHALL have the following web pages:
    Your homepage
        Include your name
        Include your position
        Provide a bio
        Include a picture
        Bio text on the left, image on the right
    Contact info
        Include your email address
        Include your LinkedIn information
    Projects (or publications)
        Include your Module 1 project title
        Include details about your Module 1 Project
        Include a link to your Module 1 Project GitHub
SHALL have a navigation bar
SHALL be able to access each of your pages from other pages within the navigation bar
SHALL be located on the top right corner of each web screen
SHALL show the current tab as a highlighted tab
SHALL be colorized (with a different color from the rest of the page)
SHALL be able to start your web application using the command $python run.py
SHALL be available on GitHub within a private repository called jhu_software_concepts within a folder named module_1.
SHALL run at port 8080 and localhost or 0.0.0.0
SHALL include a requirements.txt file that allows complete reconstruction of your environment.
SHALL use Python 3.10+
SHALL include a README.txt within your solution folder that includes instructions covering how to run your site.
SHALL include screenshots of your running site saved as a PDF within your module_1 folder.
SHOULD use blueprints to control pages
Requires sub-pages module
SHOULD use CSS to manipulate format/color/spacing of objects
SHOULD use HTML templates for each webpage
SHOULD include static and templates folders
SHOULD be well commented, clear, with appropriately named variables.

-------------------------
HOW TO RUN THE WEBSITE  
-------------------------
1. Open terminal in the jhu_software_concepts/module_1/ folder
2. Activate the virtual enviornment for your platform like so:
    $ python -m venv venv
    $ source venv/bin/Activate
3. Ensure Flask is installed, if not please input the follow:
    (venv) $ python -m pip install Flask
