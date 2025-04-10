from django.db import models

# orders/models.py
class Mesa(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
        ('mantenimiento', 'Mantenimiento')
    ]
    numero = models.IntegerField(unique=True)
    capacidad = models.IntegerField()
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='disponible'
    )
    area = models.CharField(max_length=50, blank=True, null=True)
    codigo_qr = models.ImageField(upload_to='mesas_qr/', blank=True, null=True)  # Para identificación rápida
    
    @property
    def esta_disponible(self):
        return self.estado == 'disponible'
        
    def __str__(self):
        return f"Mesa {self.numero} - {self.area}" if self.area else f"Mesa {self.numero}"
    
    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ['numero']

class Pedido(models.Model):
    ESTADO_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('en_preparacion', 'En Preparación'),
        ('listo', 'Listo'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado')
    ]
   
    ESTADO_PAGO = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado')
    ]
   
    mesa = models.ForeignKey(Mesa, on_delete=models.PROTECT)
    mesero = models.ForeignKey('users.Usuario', on_delete=models.PROTECT, related_name='pedidos_tomados')
    cajero = models.ForeignKey('users.Usuario', on_delete=models.PROTECT, related_name='pedidos_cobrados', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO, default='pendiente')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO, default='pendiente')
    notas = models.TextField(blank=True, null=True)
    numero_comensales = models.IntegerField(default=1)
   
    def __str__(self):
        return f"Pedido #{self.id} - Mesa {self.mesa.numero}"
   
    def calcular_total(self):
        """Recalcula el total del pedido basado en sus detalles activos (no cancelados)"""
        # Solo suma los detalles que no están cancelados
        total = sum(detalle.subtotal for detalle in self.detalles.all().exclude(estado='cancelado'))
        self.monto_total = total
        self.save()
        return total
    
    def calcular_total_sin_guardar(self):
        """Calcula el total del pedido sin guardar el modelo, útil para previsualización"""
        return sum(detalle.subtotal for detalle in self.detalles.all().exclude(estado='cancelado'))
    
    @property
    def items_activos(self):
        """Devuelve solo los detalles del pedido que no están cancelados"""
        return self.detalles.all().exclude(estado='cancelado')
   
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']

class DetallePedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_preparacion', 'En Preparación'),
        ('listo', 'Listo'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado')
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('products.Producto', on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    preparado_por = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='items_preparados')
    hora_solicitud = models.DateTimeField(auto_now_add=True)
    hora_preparacion = models.DateTimeField(null=True, blank=True)
    hora_listo = models.DateTimeField(null=True, blank=True)
    hora_entrega = models.DateTimeField(null=True, blank=True)
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    @property
    def area_preparacion(self):
        """Devuelve el área de preparación del producto"""
        return self.producto.area_preparacion
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"
        
class Pago(models.Model):
    METODOS_PAGO = (
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
    )
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pagos')
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODOS_PAGO)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cambio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notas = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Pago {self.id} - Pedido {self.pedido.id}"