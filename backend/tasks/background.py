# backend/tasks/background.py
from flask_mail import Message
from backend.extensions import mail, celery
from flask import current_app as app
import smtplib
from backend.app import app, mail   # <-- import your Flask app + Mail


smtplib.SMTP.debuglevel = 1

@celery.task(name='tasks.send_booking_email')
def send_booking_email(to_email, body):
    with app.app_context():
        try:
            msg = Message(
                subject="Booking Confirmed",
                recipients=[to_email],
                body=body
            )
            mail.send(msg)
            print(f"Email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send booking email: {str(e)}")
            raise

@celery.task(name='tasks.send_release_email')
def send_release_email(to_email, body):
    with app.app_context():
        try:
            msg = Message(
                subject="Parking Spot Released",
                recipients=[to_email],
                body=body
            )
            mail.send(msg)
            print(f"Release email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send release email: {str(e)}")
            raise

