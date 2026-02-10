from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import Customer, Order, Remission, Sale, CreditAssignment
import random
from decimal import Decimal


class Command(BaseCommand):
  help = 'Llena la base de datos con datos de prueba'

  def handle(self, *args, **kwargs):
    self.stdout.write('Iniciando proceso de seeding')

    # Crear Clientes
    clientes = []
    for i in range(5):
      c = Customer.objects.create(
        name=f'Cliente de Prueba {i + 1}',
        email=f'cliente{i + 1}@test.com'
      )
      clientes.append(c)
    self.stdout.write(f'{len(clientes)} Clientes creados.')

    # Crear Órdenes y Remisiones
    for cliente in clientes:
      orden = Order.objects.create(
        customer=cliente,
        folio=f'ORD-{cliente.id}-{random.randint(1000, 9999)}'
      )

      # Crear una remisión para esa orden
      remision = Remission.objects.create(
        order=orden,
        folio=f'REM-{orden.id}-{random.randint(1000, 9999)}',
        status='open'
      )

      # 4. Agregar Ventas a la remisión
      for _ in range(random.randint(1, 5)):
        dias_atras = random.randint(0, 30)
        fecha_random = timezone.now() - timedelta(days=dias_atras)

        venta = Sale.objects.create(
          remission=remision,
          subtotal=Decimal(random.randint(100, 1000)),
          tax=Decimal('16.00')
        )

        # Usamos update() directo para bypassear auto_now_add
        Sale.objects.filter(id=venta.id).update(created_at=fecha_random)

      # 5. Agregar Créditos
      if random.choice([True, False]):
        CreditAssignment.objects.create(
          remission=remision,
          amount=Decimal('50.00'),
          reason='Devolución parcial'
        )

    self.stdout.write(self.style.SUCCESS('Base de datos poblada exitosamente.'))