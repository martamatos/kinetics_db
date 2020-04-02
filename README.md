Kinetics DB
=================================================

Work in progress on a database to store info about metabolic kinetic models + web interface. 

Uses Flask, SQLAlchemy, and Bootstrap.

It is deployed in Docker containers: one for the app and one for the database.



Table of contents
-----------------

* [Introduction](#introduction)
* [How to deploy it](#how-to-deploy)
* [How to draw the DB diagram](#how-to-draw-db-diagram)
* [Contributing](#contributing)
* [Known issues and limitations](#known-issues-and-limitations)



Introduction
------------

This project started as a tentative of properly storing the kinetic data we use to build kinetic models in our group, especially the enzyme regulation part. Storing omics data is not part of the scope.

First a database structure was designed (see the diagrams in `DB_diagrams` folder), and implemented using SQLAlchemy, so that any RDBMS can be used. At the moment i am using PostgreSQL.

To interact with the database a web interface was set up using flask, jinja templates to render the html, and bootstrap for the CSS style.

This interface allows the user to add models and everything it entails, as well as modify existing data. The user can also inspect those models and all their elements, e.g. reactions or regulations. 
Soon the user will be able to:
 - download complete models in an excel file (same format that GRASP takes as an input).;
 - add models (and respective information) by uploading a GRASP input excel file.

The API documentation can be found here (TODO sphinx link).
 
 

How to deploy
--------------

This app is meant to be deployed using docker-compose with two containers: one for the app and the other for the database.

The necessary configuration files are:
 - `Dockerfile` - with all the configurations to create the container for the app.
 - `docker-compose.yml` - with the configurations to run docker-compose.
 
The above files depend on:
 - `.env` - the file with the variables for the flask app.
 - `.env_postgres` - the file with the variables for the postgres container.
 
Keep in mind that the value of the variable `POSTGRES_URL` in the `.env` file needs to be changed from `localhost` to the Postgres container name when running the whole thing with docker compose. 

At the moment the app is deployed in the QMCM group's server and is accessed by redirecting the server's localhost to the user's localhost while accessing the server through ssh (`ssh -L 5000:localhost:5000 user_name@ip_address`). 

Thus, to deploy all we need to do is to load the app image on the server and then run `docker-compose up`.



How to draw DB diagram
------------------------

If you want to draw the DB diagram in an automatic way as a sanity check, you can use the `eralchemy` package and run:

```python
from eralchemy import render_er

render_er(db.Model, 'erd_from_sqlalchemy.pdf')
```



Contributing
------------

To contribute it is recommended that you create a virtual environment.
If you use conda to create virtual environments you can use the `environment.yml`.
If you use virtualenv or pipenv, you can install the required packages using pip and `requirements.txt`.

The unit tests can be found in `app/tests`.
To run these you need a test database.
Right now a postgres database is configured and this database runs on a docker container.
To set up the database, ensure you have Docker installed as well as docker-compose.
Running `docker-compose up` should get it going.

Alternatively you can configure another database by changing the settings in `config.py` and in the `TestConfig` class of every test file.

To run the app, you need to:
 1. have the necessary packages installed (see first paragraph of this section);
 2. have a working and running RDBMS (see second paragraph of this section);
 3. run the script `load_initial_data.py` under `app/load_data.py` to both create the database tables and insert some data on it;
 4. if the above conditions are met, just run `flask run` in the project main folder, go to `localhost:5000` on your browser and enjoy :)
 


Known issues and limitations
----------------------------

 - Model download is not working properly yet, the downloaded file is not correct.
 - Model upload is not working properly yet, some fields are not added to the database properly.
 - Models are not associated to the user that created them, so they can be modified by any user. This is why at the moment no deletions are allowed. In the future every model should be associated with a user and only that user can modify/delete it.
 - The email server is not really working yet, so if a user forgets their password, they won't be able to retrieve it.