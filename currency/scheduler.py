from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.core.management import call_command


def run_update_rates():
    call_command("update_rates")


def run_backup_db():
    call_command("backup_db")


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        run_update_rates,
        "interval",
        hours=24,
        id="update_rates_job",
        replace_existing=True,
    )
    scheduler.add_job(
        run_backup_db,
        "interval",
        hours=24,
        id="backup_db_job",
        replace_existing=True,
    )
    scheduler.start()
    print("FASTpay Currency & Backup Scheduler Started...")