from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .autosave import run_autosave


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        run_autosave,
        "interval",
        minutes=1,   # Change to hours=24 in production
        id="autosave_job",
        replace_existing=True,
    )

    scheduler.start()

    print("FASTpay AutoSave Scheduler Started...")