from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import Customer, Order, Remission, Sale, CreditAssignment

# Create your tests here.
class RemissionFlowTests(APITestCase):
  """
  Suite de pruebas de integración para el flujo de Remisiones.
  Valida las reglas de negocio críticas de cierre y la exactitud de los reportes.
  """

  def setUp(self):
    """
    Configuración inicial: Se ejecuta antes de cada test.
    Crea un entorno base con Cliente, Orden y Remisión lista para probar.
    """
    self.customer = Customer.objects.create(name='Test Client')
    self.order = Order.objects.create(customer=self.customer, folio='ORD-001')
    self.remission = Remission.objects.create(order=self.order, folio='REM-001')

    self.close_url = f'/api/remissions/{self.remission.id}/close/'

  def test_close_fails_without_sales(self):
    """
    Valida Regla de Negocio #1:
    Una remisión no puede cerrarse si no tiene ventas asociadas.
    Se espera un error 400 Bad Request.
    """
    # Intentamos cerrar la remisión vacía (recién creada en setUp)
    response = self.client.post(self.close_url)

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

  def test_close_fails_if_credits_exceed_sales(self):
    """
    Valida Regla de Negocio #2:
    El monto total de créditos no puede ser mayor al total vendido.
    Se espera un error 400 Bad Request.
    """
    # 1. Creamos una venta de $100
    Sale.objects.create(remission=self.remission, subtotal=100, tax=0)

    # 2. Creamos un crédito de $150 (Rompe la regla)
    CreditAssignment.objects.create(remission=self.remission, amount=150, reason="Error")

    # 3. Intentamos cerrar
    response = self.client.post(self.close_url)

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

  def test_daily_sales_report_groups_correctly(self):
    """
    Valida el reporte de ventas diarias y la correcta agrupación por fecha.

    Estrategia:
    Se insertan ventas forzando fechas pasadas (Ayer) y actuales (Hoy) para
    verificar que el endpoint las separe correctamente en el JSON de respuesta.
    """

    now = timezone.now()
    today_date = now.date()
    yesterday_date = today_date - timedelta(days=1)

    # CASO 1: Venta de HOY
    s1 = Sale.objects.create(remission=self.remission, subtotal=100, tax=0)

    # Forzamos la hora a mediodía para evitar problemas de zona horaria (Flaky Tests)
    # Si ejecutamos el test a las 23:59, podría fallar sin esto.
    safe_today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    Sale.objects.filter(id=s1.id).update(created_at=safe_today)

    # CASO 2: Venta de AYER
    s2 = Sale.objects.create(remission=self.remission, subtotal=200, tax=0)
    safe_yesterday = safe_today - timedelta(days=1)
    # Usamos .update() directo para saltarnos la restricción auto_now_add de Django
    Sale.objects.filter(id=s2.id).update(created_at=safe_yesterday)

    # Rango de solicitud: Desde Ayer hasta Mañana (inclusivo)
    tomorrow_date = today_date + timedelta(days=1)
    url = f'/api/reports/daily-sales/?from={yesterday_date}&to={tomorrow_date}'
    response = self.client.get(url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    data = response.json()

    # Debe haber 2 grupos: Uno para ayer, uno para hoy
    self.assertEqual(len(data), 2)

    # Validamos montos específicos por día
    # Nota: Asumimos que la API devuelve ordenado por fecha
    self.assertEqual(float(data[0]['total_sales']), 200.00)
    self.assertEqual(float(data[1]['total_sales']), 100.00)