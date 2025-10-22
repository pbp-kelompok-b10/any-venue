from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from .models import Booking
from venue.models import Venue
import json
from datetime import datetime
from django.core.serializers import serialize

# Create your views here.

@login_required
def booking_list(request):
    """Menampilkan daftar booking user"""
    bookings = Booking.objects.filter(user=request.user)
    context = {
        'bookings': bookings,
    }
    return render(request, 'booking/booking_list.html', context)

@login_required
def create_booking(request, venue_id):
    """Create booking untuk venue tertentu (Support AJAX & Regular Form)"""
    venue = get_object_or_404(Venue, id=venue_id)
    
    if request.method == 'POST':
        try:
            booking_date = request.POST.get('booking_date')
            date_type = request.POST.get('date_type', 'outdoor')
            quantity = int(request.POST.get('quantity', 1))
            price = float(request.POST.get('price', venue.price))
            
            # Validasi quantity
            if quantity < 1:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Quantity minimal 1'}, status=400)
                messages.error(request, 'Quantity minimal 1')
                return redirect('venue:detail', venue_id=venue_id)
            
            # Buat booking
            booking = Booking(
                user=request.user,
                venue=venue,
                booking_date=datetime.strptime(booking_date, '%Y-%m-%d').date(),
                date_type=date_type,
                price=price,
                quantity=quantity
            )
            
            booking.save()
            
            # Response untuk AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': 'Booking berhasil dibuat! Menunggu konfirmasi dari owner.',
                    'booking_id': booking.id,
                    'redirect_url': f'/booking/{booking.id}/'
                })
            
            # Response untuk regular form
            messages.success(request, 'Booking berhasil dibuat! Menunggu konfirmasi dari owner.')
            return redirect('booking:detail', booking_id=booking.id)
            
        except ValidationError as e:
            error_msg = str(e)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect('venue:detail', venue_id=venue_id)
        except Exception as e:
            error_msg = f'Terjadi kesalahan: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect('venue:detail', venue_id=venue_id)
    
    # GET request - render halaman detail venue dengan modal
    context = {
        'venue': venue,
    }
    return render(request, 'booking/create_booking.html', context)

@login_required
def booking_detail(request, booking_id):
    """Menampilkan detail booking"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Cek apakah user adalah pemilik booking atau owner venue
    if booking.user != request.user and booking.venue.owner != request.user:
        return HttpResponseForbidden("Anda tidak memiliki akses ke booking ini.")
    
    context = {
        'booking': booking,
    }
    return render(request, 'booking/booking_detail.html', context)

@login_required
@require_POST
def cancel_booking(request, booking_id):
    """Cancel booking"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Cek apakah user adalah pemilik booking
    if booking.user != request.user:
        return JsonResponse({'success': False, 'message': 'Anda tidak memiliki akses.'}, status=403)
    
    if booking.cancel():
        messages.success(request, 'Booking berhasil dibatalkan.')
        return JsonResponse({'success': True, 'message': 'Booking berhasil dibatalkan.'})
    else:
        return JsonResponse({'success': False, 'message': 'Booking tidak dapat dibatalkan.'}, status=400)

@login_required
@require_POST
def confirm_booking(request, booking_id):
    """Confirm booking (hanya untuk owner venue)"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Cek apakah user adalah owner venue
    if booking.venue.owner != request.user:
        return JsonResponse({'success': False, 'message': 'Anda tidak memiliki akses.'}, status=403)
    
    if booking.confirm():
        messages.success(request, 'Booking berhasil dikonfirmasi.')
        return JsonResponse({'success': True, 'message': 'Booking berhasil dikonfirmasi.'})
    else:
        return JsonResponse({'success': False, 'message': 'Booking tidak dapat dikonfirmasi.'}, status=400)

@login_required
@require_POST
def complete_booking(request, booking_id):
    """Complete booking (hanya untuk owner venue)"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Cek apakah user adalah owner venue
    if booking.venue.owner != request.user:
        return JsonResponse({'success': False, 'message': 'Anda tidak memiliki akses.'}, status=403)
    
    if booking.complete():
        messages.success(request, 'Booking berhasil diselesaikan.')
        return JsonResponse({'success': True, 'message': 'Booking berhasil diselesaikan.'})
    else:
        return JsonResponse({'success': False, 'message': 'Booking tidak dapat diselesaikan.'}, status=400)

@login_required
def my_bookings(request):
    """Menampilkan semua booking milik user yang sedang login dengan filter lengkap"""
    bookings = Booking.objects.filter(user=request.user)
    
    # Filter berdasarkan status jika ada
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Filter berdasarkan tanggal
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        bookings = bookings.filter(booking_date__gte=date_from)
    if date_to:
        bookings = bookings.filter(booking_date__lte=date_to)
    
    # Filter berdasarkan harga minimum
    min_price = request.GET.get('min_price')
    if min_price:
        bookings = bookings.filter(total_price__gte=min_price)
    
    # Filter berdasarkan harga maksimum
    max_price = request.GET.get('max_price')
    if max_price:
        bookings = bookings.filter(total_price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    if sort_by in ['booking_date', '-booking_date', 'total_price', '-total_price', 'created_at', '-created_at']:
        bookings = bookings.order_by(sort_by)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'booking/my_bookings.html', context)

@login_required
def venue_bookings(request):
    """Menampilkan semua booking untuk venue milik owner (untuk owner)"""
    # Ambil semua venue milik user
    user_venues = Venue.objects.filter(owner=request.user)
    
    # Ambil semua booking dari venue-venue tersebut
    bookings = Booking.objects.filter(venue__in=user_venues)
    
    # Filter berdasarkan status jika ada
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'booking/venue_bookings.html', context)

# API Views untuk AJAX
@login_required
def check_availability(request):
    """Check apakah venue available pada tanggal tertentu (AJAX)"""
    if request.method == 'GET':
        venue_id = request.GET.get('venue_id')
        booking_date = request.GET.get('booking_date')
        
        if not venue_id or not booking_date:
            return JsonResponse({'available': False, 'message': 'Parameter tidak lengkap'})
        
        try:
            venue = Venue.objects.get(id=venue_id)
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            
            # Cek apakah sudah ada booking
            existing = Booking.objects.filter(
                venue=venue,
                booking_date=date_obj,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if existing:
                return JsonResponse({
                    'available': False, 
                    'message': 'Venue sudah dibooking pada tanggal tersebut'
                })
            else:
                return JsonResponse({
                    'available': True, 
                    'message': 'Venue tersedia'
                })
        except Venue.DoesNotExist:
            return JsonResponse({'available': False, 'message': 'Venue tidak ditemukan'})
        except ValueError:
            return JsonResponse({'available': False, 'message': 'Format tanggal salah'})
    
    return JsonResponse({'available': False, 'message': 'Method not allowed'}, status=405)

@login_required
def booking_json(request):
    """API endpoint untuk mendapatkan booking user dalam format JSON (hanya user yang login)"""
    bookings = Booking.objects.filter(user=request.user)
    
    # Filter berdasarkan status jika ada
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Convert to JSON dengan data yang diperlukan
    data = []
    for booking in bookings:
        data.append({
            'id': booking.id,
            'venue_name': booking.venue.name,
            'venue_id': booking.venue.id,
            'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
            'date_type': booking.date_type,
            'quantity': booking.quantity,
            'price': float(booking.price),
            'total_price': float(booking.total_price),
            'status': booking.status,
            'status_display': booking.get_status_display(),
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_cancellable': booking.is_cancellable(),
            'is_reviewable': booking.is_reviewable(),
        })
    
    return JsonResponse({'bookings': data, 'count': len(data)}, safe=False)

@login_required
def venue_bookings_json(request):
    """API endpoint untuk owner mendapatkan booking venue mereka dalam format JSON"""
    # Ambil semua venue milik user (owner)
    user_venues = Venue.objects.filter(owner=request.user)
    
    # Ambil semua booking dari venue-venue tersebut
    bookings = Booking.objects.filter(venue__in=user_venues)
    
    # Filter berdasarkan status jika ada
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Filter berdasarkan venue jika ada
    venue_filter = request.GET.get('venue_id')
    if venue_filter:
        bookings = bookings.filter(venue_id=venue_filter)
    
    # Convert to JSON
    data = []
    for booking in bookings:
        data.append({
            'id': booking.id,
            'user': booking.user.username,
            'user_id': booking.user.id,
            'venue_name': booking.venue.name,
            'venue_id': booking.venue.id,
            'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
            'date_type': booking.date_type,
            'quantity': booking.quantity,
            'price': float(booking.price),
            'total_price': float(booking.total_price),
            'status': booking.status,
            'status_display': booking.get_status_display(),
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    return JsonResponse({'bookings': data, 'count': len(data)}, safe=False)
