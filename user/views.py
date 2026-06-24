from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connections
from django.contrib import messages

# Create your views here.


def usuarios(request):

    context = {
        'is_admin': request.user.is_superuser,
    }


    return render(request, 'user/users.html', context)

def lista_users(request):

    # with connections['legacy'].cursor() as cursor:
    #     cursor.execute("""
    #         SELECT 
    #             u.public_id,
    #             u.name,
    #             u.last_name,
    #             u.document,
    #             u.email,
    #             u.phone,
    #             u.deletion_status,
    #             u.created_at,
    #             u.status,
    #             u.deleted,
    #             w.balance
    #         FROM users u
    #         LEFT JOIN drivers d ON u.id = d.user_id  
    #         WHERE d.user_id IS NULL;
    #     """)
    #     user = cursor.fetchall()

    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.public_id as id,
                u.name,
                u.last_name,
                u.document,
                u.email,
                u.phone,
                u.deletion_status,
                u.created_at,
                u.status,
                u.deleted,
                w.balance
            FROM users u 
            INNER JOIN user_wallets w ON w.user_id = u.id;
        """)
            
        # Obtener como diccionarios
        columns = [desc[0] for desc in cursor.description]
        user = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data = []
        for users in user:
            data.append({
                'id': users['id'],  
                'name': users['name'] or '',  
                'last_name': users['last_name'] or '',  
                'document': users['document'] or '',  
                'email': users['email'] or '',  
                'phone': users['phone'] or '',
                'deletion_status': users['deletion_status'], 
                'created_at': users['created_at'].strftime('%d/%m/%Y'),
                'status': users['status'],  
                'deleted': users['deleted'],  
                'balance': float(users['balance'] or 0), 
            })

        return JsonResponse({'data': data}, safe=False)

def believe_user(request, id):
    if 'legacy' not in connections.databases:
        db_alias = 'default'
        print("Conexión 'legacy' no encontrada, usando 'default'")
    else:
        db_alias = 'legacy'

    if request.method == 'POST':
        believe = request.POST.get('believe')
        description = request.POST.get('description')
        movement = request.POST.get('movement_type')

        print(movement)
        
        if not believe or believe == '':
            messages.error(request, 'No introdujo ningún monto')
            return redirect('believe_user', id=id)

        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        public_id,
                        id,
                        name,
                        last_name,
                        document,
                        email
                    FROM users
                    WHERE public_id = %s 
                """, [id])
                
                user_data = cursor.fetchone()

                if not user_data:
                    return render(request, 'error.html', {'mensaje': 'usuario no encontrado'})
                
                # Corregido: user_data[1] es el id
                user_id = user_data[1]
                
                mont = believe.replace(",", ".")
                print(mont)

                # Consultar wallet
                cursor.execute("""
                    SELECT 
                        public_id,
                        id,
                        balance
                    FROM user_wallets
                    WHERE user_id = %s 
                """, [user_id])
                
                user_wallet = cursor.fetchone()
                
                new_balance = None
                wallet_id = None
                status = None

                if movement == 'DEBIT':
                    transaction_type = 'DEBIT'
                    status = 'COMPLETED'
                    balance_wallet = user_wallet[2]
                    wallet_id = user_wallet[1]
                    new_balance = float(balance_wallet) - float(mont) 

                elif movement == 'CREDIT':
                    transaction_type = 'CREDIT'
                    status = 'COMPLETED'
                    balance_wallet = user_wallet[2]
                    wallet_id = user_wallet[1]
                    new_balance = float(mont) + float(balance_wallet)

                else:
                    messages.error(request, 'Tipo de movimiento no válido')
                    return redirect('believe_user', id=id)

                if new_balance is None:
                    messages.error(request, 'Error al calcular el nuevo balance')
                    return redirect('believe_user', id=id)

                
                # Actualizar balance
                cursor.execute("""
                    UPDATE user_wallets 
                    SET balance = %s 
                    WHERE id = %s
                """, [new_balance, wallet_id])  
                
                # Corregido: INSERT correcto
                cursor.execute("""
                    INSERT INTO user_transactions 
                    (description, amount_usd, type, status, user_wallet_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, [description, mont, transaction_type, status, wallet_id])
                
                # Commit después de todas las operaciones
                connections[db_alias].commit()

                if movement == 'CREDIT':
                
                    print(f"Monto acreditado correctamente: {believe}")
                    messages.success(request, 'Monto acreditado a la billetera correctamente')

                elif movement == 'DEBIT':
                    print(f"Monto acreditado correctamente: {believe}")
                    messages.success(request, 'Monto debitado a la billetera correctamente')

                return redirect('usuarios')  
            
        except Exception as e:
            print(f"Error: {e}")
            connections[db_alias].rollback()  # Rollback general
            messages.error(request, f'Error al acreditar: {str(e)}')
            return redirect('believe_user', id=id)
    
    # GET request
    try:
        with connections[db_alias].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    public_id,
                    name,
                    last_name,
                    document,
                    email
                FROM users
                WHERE public_id = %s 
            """, [id])
            
            user_data = cursor.fetchone()
            
            if not user_data:
                return render(request, 'error.html', {'mensaje': 'Usuario no encontrado'})
            
            usuario_info = {
                'public_id': user_data[0],
                'name': user_data[1],
                'last_name': user_data[2],
                'document': user_data[3],
                'email': user_data[4],
            }
            
            context = {
                'usuario': usuario_info,
                'public_id': id,
            }
            
            return render(request, 'user/believe.html', context)
    
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'error.html', {'mensaje': f'Error: {str(e)}'})


def user_transaction(request, id):


    return render(request, 'user/user_transact.html')


def list_user_trans(request, id):

    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                id
                FROM users WHERE public_id = %s;
        """, [id])
    
    user_data = cursor.fetchall()
    user_id = user_data[0]

    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                id
                FROM users WHERE user_id = %s;
        """, [user_id])
    
    wallet_data = cursor.fetchall()
    wallet_id = wallet_data[0]

    with connections['legacy'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                type,
                status,
                description,
                amount_usd,
                amount_bs,
                created_at
            FROM user_transactions WHERE user_wallet_id = %s
        """,[wallet_id])
            
        # Obtener como diccionarios
        columns = [desc[0] for desc in cursor.description]
        transact = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data = []
        for transac in transact:
            data.append({
                'id': transac['id'],  
                'type': transac['type'] or '',  
                'status': transac['status'] or '',  
                'description': transac['description'] or '',  
                'amount_usd': float(transac['amount_usd'] or 0),  
                'amount_bs': float(transac['amount_bs'] or 0),
                'created_at': transac['created_at'].strftime('%d/%m/%Y'),
                
            })

        return JsonResponse({'data': data}, safe=False)