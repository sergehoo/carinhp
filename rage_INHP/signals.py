from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from rage.models import EmployeeUser, ProtocoleVaccination


@receiver(post_save, sender=EmployeeUser)
def assign_user_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name=instance.role)
        instance.groups.add(group)


# @receiver(post_save, sender=ProtocoleVaccination)
# def creer_rendez_vous_vaccination(sender, instance, created, **kwargs):
#     if created:
#         generer_rendez_vous(instance)
