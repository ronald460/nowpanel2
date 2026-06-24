from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
import pytz

# Create your views here.


def transaction(request):

    context  = {
        'is_admin': request.user.is_superuser,
    }

    return render(request, 'transaction/transaction.html', context)

@csrf_exempt 
def list_transaction(request):
    
    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                public_id,
                id,
                amount_bs,
                origin_bank_reference,
                origin_bank_code,
                client_phone,
                status,
                type,
                created_at
            FROM transactions
        """)
        transact = cursor.fetchall()
    
    # Zona horaria de Venezuela
    venezuela_tz = pytz.timezone('America/Caracas')
    
    
    data = []
    
    for transc in transact:

        created_at = transc[8]
        if created_at:
            # Si es naive (sin zona horaria), asumir UTC
            if created_at.tzinfo is None:
                created_at = pytz.UTC.localize(created_at)
            # Convertir a zona horaria de Venezuela
            created_at_venezuela = created_at.astimezone(venezuela_tz)
            created_at_str = created_at_venezuela.strftime('%d/%m/%Y-%I:%M %p')
        else:
            created_at_str = ''

        data.append({
            'public_id': transc[0],  
            'id': transc[1] or '',  
            'amount_bs': transc[2] or '',  
            'origin_bank_reference': transc[3] or '',  
            'origin_bank_code': transc[4] or '',  
            'client_phone': transc[5] or '',
            'status': transc[6], 
            'type': transc[7],
            'created_at': created_at_str,
             
        })
    
    return JsonResponse({'data': data}, safe=False)