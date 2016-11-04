web: gunicorn Flights140.wsgi
worker: celery worker -A Flights140 -B -n tweetworker
worker: celery worker -A Flights140 -Q alert,email
