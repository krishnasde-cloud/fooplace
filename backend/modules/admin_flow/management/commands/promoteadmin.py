from django.core.management.base import BaseCommand, CommandError

from modules.users.models import User


class Command(BaseCommand):
    help = "Set an existing Fooplace user to type=admin so they can open /admin/."

    def add_arguments(self, parser):
        parser.add_argument(
            "identity",
            help="Email or Clerk user_id of a user who has already signed in once.",
        )

    def handle(self, *args, **options):
        identity = options["identity"]
        user = User.objects.filter(email__iexact=identity).first()
        if user is None:
            user = User.objects.filter(user_id=identity).first()
        if user is None:
            raise CommandError(f"No user found for {identity!r}. Sign in once first.")

        user.user_type = User.UserType.ADMIN
        user.save(update_fields=["user_type"])
        self.stdout.write(
            self.style.SUCCESS(f"Promoted {user.email or user.user_id} to admin.")
        )
