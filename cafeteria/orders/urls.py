from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Rutas para Pedidos
    path('tomar-pedido/<int:mesa_id>/', views.tomar_pedido, name='tomar_pedido'),
    path('pedidos/', views.lista_pedidos_pendientes, name='lista_pedidos_pendientes'),
    path('detalle-pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('finalizar-pedido/<int:pedido_id>/', views.finalizar_pedido, name='finalizar_pedido'),
    path('finalizar/<int:pedido_id>/', views.finalizar_pedido, name='finalizar_pedido'),   
    path('pedido/<int:pedido_id>/procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('pedido/<int:pedido_id>/completar-pago/', views.completar_pago, name='completar_pago'),
    path('pago/<int:pago_id>/recibo/', views.imprimir_recibo, name='imprimir_recibo'), 
    path('pedido/<int:pedido_id>/recibo/', views.imprimir_recibo_pedido, name='imprimir_recibo_pedido'),
  
  
    
    path('todos-pedidos/', views.todos_los_pedidos, name='todos_los_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedido/<int:pedido_id>/eliminar/', views.eliminar_pedido, name='eliminar_pedido'),
    
    path('seleccionar-mesa/', views.seleccionar_mesa, name='seleccionar_mesa'),
    
    # Rutas para Mesas
    path('mesas/', views.lista_mesas, name='lista_mesas'), 
    path('mesas/<int:mesa_id>/', views.detalle_mesa, name='detalle_mesa'),
    path('mesas/crear/', views.crear_mesa, name='crear_mesa'),  
    path('mesas/editar/<int:mesa_id>/', views.editar_mesa, name='editar_mesa'),
    path('mesas/eliminar/<int:mesa_id>/', views.eliminar_mesa, name='eliminar_mesa'),
    path('mesas/cambiar_estado/<int:mesa_id>/', views.cambiar_estado_mesa, name='cambiar_estado_mesa'),
    
    
    path('preparacion/', views.pedidos_preparacion, name='pedidos_preparacion'),
    path('actualizar-estado/', views.actualizar_estado_item, name='actualizar_estado_item'),
    
    
    #informes
    path('informe-ventas/', views.informe_ventas, name='informe_ventas'),
    
    # Añade estas URLs a tu archivo urls.py
    

]
