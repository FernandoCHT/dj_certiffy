from rest_framework import serializers
from django.db.models import Q, Sum, F, DecimalField
from decimal import Decimal
from api.models import Remission, Customer, Order

class CustomerSerializer(serializers.ModelSerializer):
  class Meta:
    model = Customer
    fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
  class Meta:
    model = Order
    fields = '__all__'

class RemissionSerializer(serializers.ModelSerializer):
  class Meta:
        model = Remission
        fields = '__all__'

  def validate(self, data):
    """
    Aplica las reglas de negocio de cierre de remisiones.

    Reglas validadas:
    1. No se permite crear una remisión directamente con estado 'closed'.
    2. Para cerrar una remisión (UPDATE):
       - Debe tener al menos una venta asociada.
       - El monto total de créditos no puede exceder el total de ventas.

    Args:
        data (dict): Datos crudos enviados por el usuario.

    Returns:
        data (dict): Datos validados listos para guardar.

    Raises:
        serializers.ValidationError: Si alguna regla de negocio no se cumple.
    """

    new_status = data.get('status')

    if not self.instance:
      if new_status == 'closed':
        raise serializers.ValidationError('No se puede crear una remisión directamente como cerrada.')
      return data

    if new_status == 'closed':

      if not self.instance.sales.exists():
        raise serializers.ValidationError('No se puede cerrar una remisión sin ventas.')

      total_vendido = self.instance.sales.aggregate(
        total=Sum(F('subtotal') + F('tax'), output_field=DecimalField())
      )['total'] or Decimal('0.00')

      total_creditos = self.instance.credits.aggregate(
        total=Sum('amount', output_field=DecimalField())
      )['total'] or Decimal('0.00')


      if total_creditos > total_vendido:
        raise serializers.ValidationError(
          f"Los créditos ({total_creditos}) exceden el total vendido ({total_vendido})."
        )

    return data
