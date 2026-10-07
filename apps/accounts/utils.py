from pywebpush import webpush, WebPushException
import json
from django.conf import settings
from .models import PushSubscription

def send_web_push(title, body, url):
    """
    Sends a web push notification to all subscribed admin users.
    """
    if not hasattr(settings, 'VAPID_PRIVATE_KEY') or not hasattr(settings, 'VAPID_ADMIN_EMAIL'):
        print("VAPID settings missing")
        return

    payload = json.dumps({
        'title': title,
        'body': body,
        'url': url
    })

    # Query all admin subscriptions
    subscriptions = PushSubscription.objects.filter(user__is_staff=True)

    for sub in subscriptions:
        sub_info = {
            'endpoint': sub.endpoint,
            'keys': {
                'p256dh': sub.p256dh,
                'auth': sub.auth
            }
        }
        try:
            webpush(
                subscription_info=sub_info,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    'sub': settings.VAPID_ADMIN_EMAIL
                }
            )
        except WebPushException as ex:
            # Handle expired/invalid subscriptions (404 Not Found, 410 Gone)
            if ex.response and ex.response.status_code in [404, 410]:
                sub.delete()
        except Exception as e:
            print(f"Web push error: {e}")
