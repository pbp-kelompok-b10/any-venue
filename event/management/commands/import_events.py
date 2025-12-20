import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from account.models import Profile
from venue.models import Venue
from event.models import Event


class Command(BaseCommand):
    help = (
        "Mengimpor data Event dari file events_data.csv. "
        "Owner event akan otomatis mengikuti owner venue (akun yang sama dengan venue)."
    )

    def handle(self, *args, **options):
        file_path = "events_data.csv"

        # Fallback owner: superuser (jika suatu venue tidak punya owner / data bermasalah)
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stdout.write(self.style.ERROR(
                "ERROR: Superuser tidak ditemukan. Buat dulu (python manage.py createsuperuser)."
            ))
            return

        fallback_owner_profile, created = Profile.objects.get_or_create(
            user=superuser,
            defaults={"role": "OWNER"}
        )
        if not created and fallback_owner_profile.role != "OWNER":
            fallback_owner_profile.role = "OWNER"
            fallback_owner_profile.save(update_fields=["role"])

        self.stdout.write(self.style.SUCCESS(f"Memulai impor data dari {file_path}..."))
        self.stdout.write(
            f"Fallback owner: {fallback_owner_profile.user.username} (role={fallback_owner_profile.role})"
        )

        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                required_headers = {"venue_name", "name", "date", "start_time"}
                missing = required_headers - set(reader.fieldnames or [])
                if missing:
                    self.stdout.write(self.style.ERROR(
                        f"ERROR: Header CSV kurang: {', '.join(sorted(missing))}"
                    ))
                    self.stdout.write(self.style.ERROR(
                        "Minimal header: venue_name,name,date,start_time (opsional: description,total_slots,thumbnail,owner_username)"
                    ))
                    return

                created_count = 0
                updated_count = 0
                skipped_count = 0
                mismatch_owner = 0

                for row in reader:
                    venue_name = (row.get("venue_name") or "").strip()
                    if not venue_name:
                        skipped_count += 1
                        continue

                    try:
                        venue = Venue.objects.get(name=venue_name)
                    except Venue.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"SKIP: Venue '{venue_name}' tidak ditemukan."
                        ))
                        skipped_count += 1
                        continue

                    # Owner event = owner venue (sesuai requirement)
                    owner_profile = getattr(venue, "owner", None) or fallback_owner_profile

                    # Pastikan role OWNER
                    if owner_profile.role != "OWNER":
                        owner_profile.role = "OWNER"
                        owner_profile.save(update_fields=["role"])

                    # Kalau CSV menyediakan owner_username, cek apakah sesuai dengan owner venue
                    owner_username_csv = (row.get("owner_username") or "").strip()
                    if owner_username_csv and owner_profile.user.username != owner_username_csv:
                        mismatch_owner += 1
                        self.stdout.write(self.style.WARNING(
                            f"WARNING: owner_username CSV ({owner_username_csv}) != owner venue ({owner_profile.user.username}) "
                            f"untuk venue '{venue_name}'. Owner event tetap mengikuti owner venue."
                        ))

                    # Parse date & time
                    date_str = (row.get("date") or "").strip()
                    time_str = (row.get("start_time") or "").strip()
                    try:
                        date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        self.stdout.write(self.style.WARNING(
                            f"SKIP: Format date salah '{date_str}' (harus YYYY-MM-DD) untuk venue '{venue_name}'."
                        ))
                        skipped_count += 1
                        continue

                    # Terima HH:MM atau HH:MM:SS
                    time_val = None
                    for fmt in ("%H:%M", "%H:%M:%S"):
                        try:
                            time_val = datetime.strptime(time_str, fmt).time()
                            break
                        except ValueError:
                            pass
                    if time_val is None:
                        self.stdout.write(self.style.WARNING(
                            f"SKIP: Format start_time salah '{time_str}' (harus HH:MM atau HH:MM:SS) untuk venue '{venue_name}'."
                        ))
                        skipped_count += 1
                        continue

                    # Optional fields
                    description = (row.get("description") or "").strip()
                    thumbnail = (row.get("thumbnail") or "").strip() or getattr(venue, "image_url", None) or None

                    total_slots_raw = (row.get("total_slots") or "").strip()
                    try:
                        total_slots = int(total_slots_raw) if total_slots_raw else 0
                    except ValueError:
                        total_slots = 0

                    # Update or create
                    _, created_flag = Event.objects.update_or_create(
                        venue=venue,
                        name=(row.get("name") or "").strip(),
                        date=date_val,
                        start_time=time_val,
                        defaults={
                            "owner": owner_profile,
                            "description": description,
                            "total_slots": total_slots,
                            "thumbnail": thumbnail,
                        },
                    )

                    if created_flag:
                        created_count += 1
                    else:
                        updated_count += 1

                self.stdout.write(self.style.SUCCESS("--- Impor Selesai! ---"))
                self.stdout.write(f"{created_count} event baru dibuat.")
                self.stdout.write(f"{updated_count} event di-update.")
                self.stdout.write(f"{skipped_count} baris di-skip.")
                if mismatch_owner:
                    self.stdout.write(self.style.WARNING(
                        f"{mismatch_owner} baris memiliki owner_username yang tidak cocok dengan owner venue (event tetap mengikuti owner venue)."
                    ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File {file_path} tidak ditemukan."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Terjadi error: {e}"))
            import traceback
            traceback.print_exc()
