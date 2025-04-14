from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import PedidoForm, DetallePedidoForm,SeleccionMesaForm,MesaForm
from products.forms import CategoriaForm,ProductoForm
from orders.models import Pedido,Mesa,DetallePedido,Pago
from products.models import Producto,Categoria,AreaPreparacion
from users.models import Usuario,Rol
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from datetime import datetime
from django.db.models import Q
import json



#trabajo con las mesas
@login_required
def lista_mesas(request):
    """Vista para mostrar la lista de todas las mesas"""
    mesas = Mesa.objects.all().order_by('numero')
    
    # Contadores para el resumen
    disponibles = mesas.filter(estado='disponible').count()
    ocupadas = mesas.filter(estado='ocupada').count()
    reservadas = mesas.filter(estado='reservada').count()
    
    context = {
        'mesas': mesas,
        'disponibles': disponibles,
        'ocupadas': ocupadas,
        'reservadas': reservadas,
        'total': mesas.count()
    }
    return render(request, 'orders/mesas/lista_mesas.html', context)

@login_required
def detalle_mesa(request, mesa_id):
    """Vista para mostrar los detalles de una mesa específica"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    return render(request, 'orders/mesas/detalle_mesa.html', {'mesa': mesa})

@login_required
def crear_mesa(request):
    """Vista para crear una nueva mesa"""
    if request.method == 'POST':
        form = MesaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mesa creada correctamente')
            return redirect('orders:lista_mesas')
    else:
        form = MesaForm()
    
    return render(request, 'orders/mesas/form_mesa.html', {'form': form, 'accion': 'Crear'})

@login_required
def editar_mesa(request, mesa_id):
    """Vista para editar una mesa existente"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Mesa {mesa.numero} actualizada correctamente')
            return redirect('orders:lista_mesas')
    else:
        form = MesaForm(instance=mesa)
    
    return render(request, 'orders/mesas/form_mesa.html', {'form': form, 'mesa': mesa, 'accion': 'Editar'})

@login_required
def eliminar_mesa(request, mesa_id):
    """Vista para eliminar una mesa"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        mesa_num = mesa.numero
        mesa.delete()
        messages.success(request, f'Mesa {mesa_num} eliminada correctamente')
        return redirect('orders:lista_mesas')
    
    return render(request, 'orders/mesas/confirmar_eliminar_mesa.html', {'mesa': mesa})

@login_required
def cambiar_estado_mesa(request, mesa_id):
    """Vista para cambiar rápidamente el estado de una mesa"""
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in [choice[0] for choice in Mesa.ESTADO_CHOICES]:
            mesa.estado = nuevo_estado
            mesa.save()
            messages.success(request, f'Estado de la mesa {mesa.numero} actualizado a {dict(Mesa.ESTADO_CHOICES)[nuevo_estado]}')
        else:
            messages.error(request, 'Estado no válido')
        
        return redirect('orders:lista_mesas')
    
    return render(request, 'orders/mesas/cambiar_estado_mesa.html', {'mesa': mesa})

#pedidos
@login_required
def tomar_pedido(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
   
    # Permitir acceso si la mesa está disponible O si ya tiene un pedido pendiente/en preparación
    pedido_existente = Pedido.objects.filter(
        mesa=mesa,
        estado__in=['pendiente', 'en_preparacion']
    ).first()
    
    # Solo verificar disponibilidad si no hay un pedido en curso
    if not pedido_existente and not mesa.esta_disponible and mesa.estado != 'reservada':
        messages.error(request, f"La Mesa {mesa.numero} no está disponible actualmente")
        return redirect('orders:seleccionar_mesa')
    
    try:
        mesero = Usuario.objects.get(username=request.user.username)
    except Usuario.DoesNotExist:
        messages.error(request, "No tienes permisos para tomar pedidos.")
        return redirect('home')

    # Obtener pedido existente o crear uno nuevo
    pedido_existente = Pedido.objects.filter(
        mesa=mesa,
        estado__in=['pendiente', 'en_preparacion']
    ).first()

    if request.method == 'POST':
        with transaction.atomic():
            # Si no hay pedido existente, crear uno nuevo
            if not pedido_existente:
                # Cambiar estado de la mesa a OCUPADA
                mesa.estado = 'ocupada'
                mesa.save()
                
                pedido = Pedido.objects.create(
                    mesa=mesa,
                    mesero=mesero,
                    estado='pendiente',
                    monto_total=0,
                    estado_pago='pendiente',
                    numero_comensales=request.POST.get('numero_comensales', 1)
                )
                pedido_existente = pedido  # Actualizar referencia

            action = request.POST.get('action')
            
            if action == 'add_producto':
                # Procesar detalle del pedido
                producto_id = request.POST.get('producto_id')
                cantidad = int(request.POST.get('cantidad', 1))
                producto = get_object_or_404(Producto, id=producto_id)

                DetallePedido.objects.create(
                    pedido=pedido_existente,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    estado='pendiente'
                )

                pedido_existente.calcular_total()
                messages.success(request, f'Producto {producto.nombre} agregado al pedido.')
                return redirect('orders:tomar_pedido', mesa_id=mesa.id)
                
            elif action == 'remove_producto':
                detalle_id = request.POST.get('detalle_id')
                try:
                    detalle = DetallePedido.objects.get(
                        id=detalle_id,
                        pedido=pedido_existente
                    )
                    producto_nombre = detalle.producto.nombre
                    detalle.delete()
                    pedido_existente.calcular_total()
                    messages.success(request, f'Producto {producto_nombre} eliminado del pedido.')
                except DetallePedido.DoesNotExist:
                    messages.error(request, 'No se encontró el detalle del pedido')
                return redirect('orders:tomar_pedido', mesa_id=mesa.id)

    # Obtener categorías y productos
    categorias = Categoria.objects.all()
    
    # Recalcular total por si hubo cambios
    if pedido_existente:
        pedido_existente.calcular_total()
        total_pedido = pedido_existente.monto_total
    else:
        total_pedido = 0

    context = {
        'mesa': mesa,
        'pedido_existente': pedido_existente,
        'categorias': categorias,
        'productos_por_categoria': {
            categoria: Producto.objects.filter(categoria=categoria)
            for categoria in categorias
        },
        'total_pedido': total_pedido
    }
    return render(request, 'orders/pedidos/tomar_pedido.html', context)
@login_required
def detalle_pedido(request, pedido_id):
    """
    View to show and modify order details
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        # Handle actions like removing items or changing quantities
        action = request.POST.get('action')
        if action == 'eliminar_item':
            detalle_id = request.POST.get('detalle_id')
            detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
            detalle.delete()

            # Recalculate total
            pedido.monto_total = sum(
                detalle.cantidad * detalle.precio_unitario 
                for detalle in pedido.detalles.all()
            )
            pedido.save()

    return render(request, 'orders/detalle_pedido.html', {'pedido': pedido})
@login_required
def finalizar_pedido(request, pedido_id):
    """
    Cierra el pedido y redirecciona al pago
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
   
    if request.method == 'POST':
        # Cambiamos el estado a 'completado' en lugar de 'en_preparacion'
        # ya que los productos ya fueron entregados
        pedido.estado = 'completado'
        pedido.save()
        
        messages.success(request, f'El pedido #{pedido.id} ha sido completado. Proceda al pago.')
        # Redireccionamos directamente a la página de pago
        return redirect('orders:procesar_pago', pedido_id=pedido.id)
    
    # Ahora utilizamos una plantilla diferente que refleje que estamos cerrando el pedido
    return render(request, 'orders/pedidos/confirmar_cierre_pedido.html', {'pedido': pedido})

# orders/views.py (continuation)
@login_required
def seleccionar_mesa(request):
    mesas = Mesa.objects.all().order_by('numero')
    
    # Configuración automática de posiciones basada en una cuadrícula
    mesas_por_fila = 5  # Número de mesas por fila
    espaciado_x = 15    # Espacio horizontal entre mesas (%)
    espaciado_y = 15    # Espacio vertical entre mesas (%)
    inicio_x = 10       # Margen izquierdo inicial (%)
    inicio_y = 20       # Margen superior inicial (%)
    
    mesa_positions = {}
    for i, mesa in enumerate(mesas):
        fila = i // mesas_por_fila
        columna = i % mesas_por_fila
        mesa_positions[mesa.numero] = {
            'x': inicio_x + columna * espaciado_x,
            'y': inicio_y + fila * espaciado_y
        }
    
    context = {
        'mesas': mesas,
        'mesa_positions': mesa_positions
    }
    
    return render(request, 'orders/pedidos/seleccionar_mesa.html', context)

@login_required
def cambiar_estado_pedido(request, pedido_id):
    """
    View to change order or order detail status
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        detalle_id = request.POST.get('detalle_id')
        
        if detalle_id:
            # Change status of a specific order detail
            detalle = get_object_or_404(DetallePedido, id=detalle_id, pedido=pedido)
            detalle.estado = nuevo_estado
            detalle.save()
        else:
            # Change status of entire order
            pedido.estado = nuevo_estado
            pedido.save()
            
            # Optionally update all order details
            if nuevo_estado:
                pedido.detalles.update(estado=nuevo_estado)
        
        return redirect('lista_pedidos')
    
    return render(request, 'orders/cambiar_estado_pedido.html', {'pedido': pedido})

@login_required
def lista_pedidos_pendientes(request):
    pedidos = Pedido.objects.filter(estado_pago='pendiente').order_by('fecha_creacion')
    
    # Preparar detalles por área para cada pedido
    for pedido in pedidos:
        pedido.detalles_por_area = {}
        for detalle in pedido.detalles.all():
            area = detalle.area_preparacion
            if area not in pedido.detalles_por_area:
                pedido.detalles_por_area[area] = []
            pedido.detalles_por_area[area].append(detalle)
        
        # Verificar si todos los productos están listos para cerrar el pedido
        pedido.puede_cerrarse = True  # Comenzamos asumiendo que se puede cerrar
        for detalle in pedido.detalles.all():
            # Si hay algún producto pendiente o en preparación, no se puede cerrar
            if detalle.estado in ['pendiente', 'en_preparacion']:
                pedido.puede_cerrarse = False
                break
    
    context = {
        'pedidos': pedidos
    }
    return render(request, 'orders/pedidos/lista_pedidos_pendientes.html', context)



@login_required
def todos_los_pedidos(request):
    # Obtener todos los pedidos, ordenados de más reciente a más antiguo
    pedidos = Pedido.objects.all().order_by('-fecha_creacion')
    
    context = {
        'pedidos': pedidos
    }
    return render(request, 'orders/pedidos/todos_pedidos.html', context)

@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'orders/pedidos/detalle_pedido.html', {'pedido': pedido})


@login_required
def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Si el método es POST, procesar la eliminación
    if request.method == 'POST':
        # Solo permitir eliminar pedidos pendientes o cancelados
        if pedido.estado_pago in ['pendiente', 'cancelado']:
            # Guardar información para el mensaje
            pedido_info = f"Pedido #{pedido.id} de la Mesa {pedido.mesa.numero}"
            
            # Eliminar el pedido
            pedido.delete()
            
            # Liberar la mesa marcándola como disponible
            mesa = pedido.mesa
            mesa.estado = 'disponible'
            mesa.save()
        
            # Añadir mensaje de éxito
            messages.success(request, f"{pedido_info} ha sido eliminado correctamente.")
            return redirect('orders:todos_los_pedidos')
        else:
            # Añadir mensaje de error
            messages.error(request, f"No se puede eliminar el Pedido #{pedido.id} porque su estado de pago es '{pedido.get_estado_pago_display()}'.")
            return render(request, 'orders/pedidos/error_eliminar_pedido.html', {'pedido': pedido})
    
    # Si el método es GET, mostrar página de confirmación
    return render(request, 'orders/pedidos/confirmar_eliminar_pedido.html', {'pedido': pedido})

@login_required
def procesar_pago(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Usar solo los productos activos
    items_activos = pedido.items_activos
    total_activo = pedido.calcular_total_sin_guardar()
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        imprimir_recibo = request.POST.get('imprimir_recibo') == 'on'
        
        # Actualizar el total del pedido antes de crear el pago
        pedido.calcular_total()  # Esto actualizará monto_total con solo los items activos
        
        pago = Pago(
            pedido=pedido,
            monto=pedido.monto_total,
            metodo=metodo_pago
        )        
        
        if metodo_pago == 'efectivo':
            monto_recibido = float(request.POST.get('monto_recibido') or 0)
            pago.notas = f"Monto recibido: ${monto_recibido}, Cambio: ${monto_recibido - pedido.total}"
        elif metodo_pago == 'tarjeta':
            # En un entorno real, aquí iría la integración con un procesador de pagos
            # Solo almacenamos los últimos 4 dígitos por seguridad
            numero_tarjeta = request.POST.get('numero_tarjeta', '')
            if numero_tarjeta:
                ultimos_digitos = numero_tarjeta.replace(' ', '')[-4:]
                pago.notas = f"Pago con tarjeta terminada en {ultimos_digitos}"
        
        pago.save()
        
        # Actualizar estado del pedido
        pedido.estado = 'pagado'
        pedido.save()
        
       
        
        
        # Liberar la mesa marcándola como disponible
        mesa = pedido.mesa
        mesa.estado = 'disponible'
        mesa.save()
        
        messages.success(request, f'El pago del pedido #{pedido.id} ha sido procesado exitosamente.')
        
        # Si se debe imprimir el recibo, redirigir a la página de impresión
        if imprimir_recibo:
            return redirect('orders:imprimir_recibo', pago_id=pago.id)
        
        return redirect('orders:lista_pedidos')   

    return render(request, 'orders/pedidos/procesar_pago.html', {
        'pedido': pedido,
        'items_activos': items_activos,
        'total_activo': total_activo
    })

# Añade estas vistas a tu archivo views.py
@login_required
def completar_pago(request, pedido_id):
    """
    Procesa el pago y actualiza el estado del pedido
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        imprimir_recibo = request.POST.get('imprimir_recibo') == 'on'
        
        # Usar monto_total en lugar de total
        pago = Pago(
            pedido=pedido,
            monto=pedido.monto_total,  # Este es el nombre correcto según tu modelo
            metodo=metodo_pago
        )
        
        if metodo_pago == 'efectivo':
            monto_recibido = float(request.POST.get('monto_recibido', 0))
            cambio = monto_recibido - float(pedido.monto_total)  # Usar monto_total aquí también
            
            pago.monto_recibido = monto_recibido
            pago.cambio = cambio
            pago.notas = f"Pago en efectivo. Monto recibido: ${monto_recibido}, Cambio: ${cambio}"
        elif metodo_pago == 'tarjeta':
            # Simplemente registrar que se pagó con tarjeta usando POS externo
            pago.notas = "Pago con tarjeta usando terminal POS externa"
        
        pago.save()
        
        # Actualizar estado del pedido
        pedido.estado_pago = 'pagado'  # Usar estado_pago en lugar de estado
        pedido.save()
        
        # Liberar la mesa marcándola como disponible
        mesa = pedido.mesa
        mesa.estado = 'disponible'
        mesa.save()
        
        messages.success(request, f'El pago del pedido #{pedido.id} ha sido procesado exitosamente. La mesa {mesa.numero} está disponible.')
        
        # Siempre imprimir recibo si está marcado
        if imprimir_recibo:
            return redirect('orders:imprimir_recibo', pago_id=pago.id)
        
        return redirect('orders:todos_los_pedidos')
    
    # Si no es POST, redirigir a la página de procesar pago
    return redirect('orders:procesar_pago', pedido_id=pedido.id)
@login_required
def imprimir_recibo(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
   
    # Filtrar solo los detalles activos
    detalles_activos = pago.pedido.detalles.exclude(estado='cancelado')
    
    # Calcular el total correcto basado solo en detalles activos
    total_correcto = sum(detalle.subtotal for detalle in detalles_activos)
    cambio_correcto = pago.monto_recibido - total_correcto if pago.monto_recibido else 0
   
    return render(request, 'orders/pedidos/imprimir_recibo.html', {
        'pago': pago,
        'detalles_activos': detalles_activos,
        'total_correcto': total_correcto,
        'cambio_correcto':cambio_correcto
    })
    
# En views.py
@login_required
def imprimir_recibo_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pago = get_object_or_404(Pago, pedido=pedido)  # O pedido.pago_set.first() si hay múltiples pagos
    
    # Resto de tu lógica actual
    detalles_activos = pedido.detalles.exclude(estado='cancelado')
    total_correcto = sum(detalle.subtotal for detalle in detalles_activos)
    cambio_correcto = pago.monto_recibido - total_correcto if pago.monto_recibido else 0
    
    return render(request, 'orders/pedidos/imprimir_recibo.html', {
        'pago': pago,
        'detalles_activos': detalles_activos,
        'total_correcto': total_correcto,
        'cambio_correcto': cambio_correcto
    })    
@login_required
def pedidos_preparacion(request):
    # Determinar el área del usuario actual
    user = request.user
    
    if not hasattr(user, 'rol'):
        messages.error(request, "Tu usuario no tiene un rol asignado.")
        return redirect('dashboard')
    
    try:
        # Permitir acceso a cocina, bar o administrador
        if user.rol.nombre == Rol.COCINA:
            area_nombre = AreaPreparacion.COCINA
            template = 'orders/pedidos/pedidos_cocina.html'
        elif user.rol.nombre == Rol.BAR:
            area_nombre = AreaPreparacion.BAR
            template = 'orders/pedidos/pedidos_bar.html'
        elif user.rol.nombre == Rol.ADMINISTRADOR:
            # Para administrador, podemos mostrar ambas áreas o elegir una por defecto
            area_nombre = request.GET.get('area', AreaPreparacion.COCINA)  # Parámetro opcional para cambiar de área
            
            # Validar que el área solicitada sea válida
            if area_nombre not in [AreaPreparacion.COCINA, AreaPreparacion.BAR]:
                area_nombre = AreaPreparacion.COCINA
            
            # Elegir la plantilla correspondiente
            if area_nombre == AreaPreparacion.COCINA:
                template = 'orders/pedidos/pedidos_cocina.html'
            else:
                template = 'orders/pedidos/pedidos_bar.html'
        else:
            # Cualquier otro rol no tiene permiso
            messages.error(request, "No tienes autorización para acceder a esta sección.")
            return redirect('dashboard')
        
        # Obtener pedidos con items pendientes para esta área
        pedidos = Pedido.objects.filter(
            Q(detalles__producto__categoria__area_preparacion__nombre=area_nombre) &
            Q(detalles__estado__in=['pendiente', 'en_preparacion'])
        ).distinct().order_by('fecha_creacion')
        
        # Organizar los detalles por pedido y área
        pedidos_con_detalles = []
        for pedido in pedidos:
            detalles = pedido.detalles.filter(
                producto__categoria__area_preparacion__nombre=area_nombre,
                estado__in=['pendiente', 'en_preparacion', 'listo']
            ).order_by('estado', 'hora_solicitud')
            
            if detalles.exists():
                pedidos_con_detalles.append({
                    'pedido': pedido,
                    'detalles': detalles
                })
        
        context = {
            'pedidos': pedidos_con_detalles,
            'area': AreaPreparacion.objects.get(nombre=area_nombre)
        }
        
        # Si es administrador, agregar opciones para cambiar de área
        if user.rol.nombre == Rol.ADMINISTRADOR:
            context['es_admin'] = True
            context['area_actual'] = area_nombre
        
        return render(request, template, context)
    
    except AreaPreparacion.DoesNotExist:
        messages.error(request, "El área de preparación no existe.")
        return redirect('dashboard')

@require_POST
@login_required
def actualizar_estado_item(request):
    try:
        # Manejar tanto JSON como form-data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        item_id = data.get('item_id')
        nuevo_estado = data.get('estado')
        
        if not item_id or not nuevo_estado:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        item = DetallePedido.objects.get(pk=item_id)
        
        # Verificar permisos
        user = request.user
        area_item = item.producto.area_preparacion
        
        if (user.rol.nombre == Rol.COCINA and area_item.nombre != AreaPreparacion.COCINA) or \
           (user.rol.nombre == Rol.BAR and area_item.nombre != AreaPreparacion.BAR):
            return JsonResponse({'error': 'No tienes permiso para modificar este ítem'}, status=403)
        
        # Actualizar estado
        item.estado = nuevo_estado
        item.preparado_por = user
        item.save()
        
        return JsonResponse({
            'success': True,
            'nuevo_estado': item.get_estado_display()
        })
        
    except DetallePedido.DoesNotExist:
        return JsonResponse({'error': 'Ítem no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
