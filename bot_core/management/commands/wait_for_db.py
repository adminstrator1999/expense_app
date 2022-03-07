import time

from psycopg2.errors import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command for checking if database is ready"""
    def handle(self, *args, **options):
        self.stdout.write("Waiting for database ...")
        db_ready = False
        while db_ready is False:
            try:
                self.check(databases=['default'])
                db_ready = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write("Database is unavailable. Waiting for 1 second ...")
                time.sleep(1)
        self.stdout.write("Database is ready!")

