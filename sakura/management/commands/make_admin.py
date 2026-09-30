"""Create the admin/admin superuser described by the project owner."""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Create/reset the admin superuser (admin/admin)"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default="admin")
        parser.add_argument("--email", default="admin@sakura.local")
        parser.add_argument("--force-password", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        u = options["username"]
        p = options["password"]
        user, created = User.objects.get_or_create(
            username=u, defaults={"email": options["email"], "is_staff": True, "is_superuser": True}
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.email = options["email"]
        if created or options["force_password"]:
            user.set_password(p)
        user.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"{'created' if created else 'updated'} superuser "
                f"{user.username} / {p if (created or options['force_password']) else '(password kept)'}"
            )
        )
