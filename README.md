## SearchSmartly Assessment


### QuickStart
- If you have docker installed, you can get started using these steps:
  - Run the quickstart script `source scripts/docker-quickstart.sh` to start up the application in development mode
  - Run `docker exec -it web python manage.py createsuperuser` in another terminal to create a superuser
  - Access the admin application at [localhost:8000/admin](http://localhost:8000/admin) using your superuser credentials
  - To load the data, run `docker exec web python manage.py loadpoi <path_to_file(s) or directory>`. You can add multiple files or directories


### Production Setup
- The application is also production ready and has been set up to use nginx and gunicorn


### Screenshot
![poi_img](/screenshots/poi_img.png)
