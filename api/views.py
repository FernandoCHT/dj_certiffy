from django.shortcuts import render
from rest_framework import viewsets
from api.models import Customer, Order, Remission, Sale
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F, Count
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date
from datetime import timedelta


from api.serializers import CustomerSerializer, OrderSerializer, RemissionSerializer
# Create your views here.

class CustomerViewSet(viewsets.ModelViewSet):
  queryset = Customer.objects.all()
  serializer_class = CustomerSerializer

class OrderViewSet(viewsets.ModelViewSet):
  queryset = Order.objects.all()
  serializer_class = OrderSerializer

class RemissionViewSet(viewsets.ModelViewSet):
  """
  ViewSet para manejar el CRUD de Remisiones.
  Incluye endpoints personalizados para cerrar remisiones y obtener resúmenes.
  """
  queryset = Remission.objects.all()
  serializer_class = RemissionSerializer

  @action(detail=True, methods=['post'])
  def close(self, request, pk=None):
    remission = self.get_object()

    serializer = self.get_serializer(remission, data={'status': 'closed'}, partial=True)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({'status': 'Remisión cerrada exitosamente'})

  @action(detail=True, methods=['get'])
  def summary(self, request, pk=None):
    remission = self.get_object()

    sales_data = remission.sales.aggregate(
      total_vendido=Sum(F('subtotal') + F('tax')),
      conteo=Count('id')
    )

    credits_data = remission.credits.aggregate(
      total_creditos=Sum('amount')
    )

    total_sales = sales_data['total_vendido'] or Decimal('0.00')
    total_credits = credits_data['total_creditos'] or Decimal('0.00')
    sales_count = sales_data['conteo']

    balance = total_sales - total_credits

    return Response({
      'total_sales': total_sales,
      'total_credits': total_credits,
      'balance': balance,
      'sales_count': sales_count
    })

  def get_queryset(self):
    """
    Sobrescribe el queryset original para optimizar consultas a BD.

    Optimización:
    - select_related: Trae 'order' y 'customer' en la misma query (evita N+1).
    - prefetch_related: Pre-carga 'sales' y 'credits' para cálculos rápidos.
    """
    queryset = Remission.objects.all()
    return queryset.select_related('order', 'order__customer').prefetch_related('sales', 'credits')


class DailySalesView(APIView):
  """
  Endpoint analítico para generar reportes de ventas diarias.
  Realiza agregaciones a nivel de base de datos para optimizar el rendimiento.
  """

  def get(self, request):
    """
    Obtiene el reporte de ventas agrupado por día dentro de un rango de fechas.

    Query Params:
        from (str): Fecha de inicio en formato YYYY-MM-DD (Obligatorio).
        to (str): Fecha de fin en formato YYYY-MM-DD (Obligatorio).

    Returns:
        Response: Lista de objetos JSON ordenados cronológicamente con:
            - date: Fecha del agrupamiento.
            - total_sales: Sumatoria monetaria (subtotal + impuestos).
            - total_tax: Sumatoria de impuestos.
            - sales_count: Conteo total de transacciones.

    Raises:
        ValidationError: Si faltan los parámetros 'from' o 'to'.
    """

    start_str = request.query_params.get('from')
    end_str = request.query_params.get('to')

    if not start_str or not end_str:
      raise ValidationError("'from' y  'to' son parámetros obligatorios")

    start_date = parse_date(start_str)
    end_date = parse_date(end_str)

    # LÓGICA DE FECHA INCLUSIVA:
    # Sumamos 1 día a la fecha final y usamos el operador 'lt' (menor que)
    # para asegurar que se incluyan todas las ventas del día final (hasta las 23:59:59).
    # Esto evita el problema común donde '2026-02-09' se interpreta como '00:00:00' y excluye el día.
    end_date_inclusive = end_date + timedelta(days=1)

    sales = Sale.objects.filter(
      created_at__gte=start_date,
      created_at__lt=end_date_inclusive
    )

    # AGREGACIÓN EN BASE DE DATOS:
    # 1. annotate(date=...): Truncamos la fecha para ignorar la hora y agrupar.
    # 2. values('date'): Equivale a un GROUP BY date en SQL.
    # 3. annotate(...): Calculamos métricas sobre cada grupo.
    report = (
      sales.annotate(date=TruncDate('created_at'))
      .values('date')
      .annotate(
        total_sales=Sum(F('subtotal') + F('tax')),
        total_tax=Sum('tax'),
        sales_count=Count('id'),
      ).order_by('date')
    )

    return Response(report)
