DigitalOcean article: https://www.digitalocean.com/community/tutorials/build-a-to-do-application-using-django-and-react#step-1-setting-up-the-backend

# Django-React integration

Of course! Let's proceed to Section 14: Caching for Improved Performance.

14.1 Implementing Caching:
In this section, we will explore how to implement caching in our API to improve performance by reducing the response time for frequently accessed data.

Step 1: Install Required Packages:
   - In your Django project directory, open your terminal or command prompt.
   - Run the following command to install the required package:

     ```
     pip install django-cacheops
     ```

   - This package provides caching support for Django.

Step 2: Configure Caching:
   - In your Django project's settings (`api/settings.py`), add the following lines at the end of the file:

     ```python
     CACHEOPS_REDIS = {
         'host': 'localhost',
         'port': 6379,
         'db': 1,
     }

     CACHEOPS = {
         'api.*': {'ops': 'all'},
     }
     ```

   - These settings configure the Redis cache backend and define which models should be cached.

Step 3: Apply Caching to Models:
   - In your Django models (`api/models.py`), import the cacheops decorator at the top of the file:

--------------

[Bootstrap5 Examples](https://getbootstrap.com/docs/5.0/examples/)

----------

Order of OpenAI playground calls:

- create thread (POST/v1/threads)
- add message (POST/v1/threads/thread_qsgFWRdCoedCFXxbhlH0vZUt/messages)
- run thread (POST/v1/threads/thread_qsgFWRdCoedCFXxbhlH0vZUt/runs)
- get run's steps (GET/v1/threads/thread_qsgFWRdCoedCFXxbhlH0vZUt/runs/run_DA1LV55b2Yf6rjeJoSoZTblW/steps) (not sure why)
- get run's status (GET/v1/threads/thread_qsgFWRdCoedCFXxbhlH0vZUt/runs/run_DA1LV55b2Yf6rjeJoSoZTblW)
- get runs (GET/v1/threads/thread_qsgFWRdCoedCFXxbhlH0vZUt/runs)
- get messages (GET/v1/threads/thread_qsgFWRdCoedCFXxbhlH0vZUt/messages)
