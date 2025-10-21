import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from venue.models import Venue, City, Category 

class Command(BaseCommand):
    help = 'Mengimpor data venue dari file venues_data.csv'

    def handle(self, *args, **options):
        file_path = 'venues_data.csv'

        # 1. Dapatkan user untuk 'owner'. Kita pakai superuser pertama sebagai default.
        default_owner = User.objects.filter(is_superuser=True).first()
        if not default_owner:
            self.stdout.write(self.style.ERROR(
                'ERROR: Tidak ada superuser ditemukan. Harap buat superuser terlebih dahulu.'
            ))
            self.stdout.write(self.style.ERROR(
                'Jalankan: python manage.py createsuperuser'
            ))
            return  # Hentikan script

        self.stdout.write(self.style.SUCCESS(f'Memulai impor data dari {file_path}...'))
        self.stdout.write(f'Semua venue baru akan dimiliki oleh: {default_owner.username}')

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                venues_created = 0
                venues_updated = 0

                for row in reader:
                    
                    # 2. Handle ForeignKeys (City & Category)
                    # get_or_create: Cari objek, jika tidak ada, buat baru.
                    city_obj, _ = City.objects.get_or_create(name=row['lokasi_kota'])
                    category_obj, _ = Category.objects.get_or_create(name=row['kategori_olahraga'])

                    # 3. Handle harga (yang bisa kosong)
                    harga = row.get('harga_per_jam')
                    if not harga or harga == '':
                        harga_bersih = None  # Akan disimpan sebagai NULL di DB
                    else:
                        harga_bersih = int(float(harga)) # Ubah ke int

                    # 4. Buat atau Update Venue dengan mapping field yang benar
                    venue, created = Venue.objects.update_or_create(
                        name=row['nama'],  # Field unik sebagai pencari
                        defaults={
                            # Mapping nama field model -> nama header CSV
                            'owner': default_owner,
                            'price': harga_bersih,
                            'city': city_obj,
                            'category': category_obj,
                            'type': row['tipe'], 
                            'address': row['alamat'], 
                            'description': row['deskripsi'], 
                            'image_url': row['link_gambar'] 
                        }
                    )

                    if created:
                        venues_created += 1
                    else:
                        venues_updated += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f'Impor selesai! {venues_created} venue baru dibuat, {venues_updated} venue di-update.'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File {file_path} tidak ditemukan.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Terjadi error: {e}'))