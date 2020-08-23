from django.db.models.signals import post_save
from django.dispatch import receiver
from openwisp_notifications.signals import notify
from swapper import load_model

from openwisp_controller.config.signals import config_status_changed

Config = load_model('config', 'Config')
Device = load_model('config', 'Device')


@receiver(
    config_status_changed, sender=Config, dispatch_uid='config_change_notification'
)
def config_change_notification(sender, instance, **kwargs):
    if instance.status == 'error':
        notification_type = 'config_problem'
    elif instance.status == 'applied':
        notification_type = 'config_recovery'
    else:
        return
    notify.send(sender=instance, type=notification_type, target=instance.device)


@receiver(post_save, sender=Device, dispatch_uid='device_registered_notification')
def device_registered_notification(sender, instance, created, **kwargs):
    if created:
        notify.send(sender=instance, type='device_registered', target=instance)
