import sys
from django.apps import AppConfig


class CurrencyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'currency'

    def ready(self):
        # Don't start the scheduler during migrate/makemigrations/etc —
        # only when the actual server process is running. Otherwise it
        # tries to write to tables that don't exist yet.
        skip_commands = {'migrate', 'makemigrations', 'collectstatic', 'shell', 'test'}
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        from . import scheduler
        scheduler.start()