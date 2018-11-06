# Fathom Training Server

This is a prototype service for maintaining a set of training webpages for Fathom.

## Development Setup

Prerequisites:

- Docker 18.03.0 or higher
- docker-compose 1.21.0 or higher
- Recent node/npm

1. Clone the repository:

   ```sh
   git clone https://github.com/osmose/fathom-training-server.git
   cd fathom-training-server
   ```
2. Build the Docker image:

   ```sh
   docker-compose build
   ```
3. Run migrations:

   ```sh
   docker-compose run webserver pipenv run python manage.py migrate
   ```
4. Create an admin account:

   ```sh
   docker-compose run webserver pipenv run python manage.py createsuperuser
   ```
5. Build frontend files:

   ```sh
   npm install
   npm run build # or `npm run watch`
   ```
6. Start everything:

   ```sh
   docker-compose up
   ```

## What can it do?

- Add webpages in the admin interface (http://localhost:8000/admin/) and then use the "freeze" admin action to freeze and persist their frozen HTML.
  - Once frozen, view the webpage by clicking the "View on Site" button on the webpage's admin page.

## License

Fathom Training Server is licensed under the MPL 2.0. See the `LICENSE` file for details.
