from celery import shared_task


@shared_task
def send_activation_email(user_id: int) -> None:
    pass
