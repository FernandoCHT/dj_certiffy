from django.core.validators import MinValueValidator
from django.db import models

# Create your models here.

class Customer(models.Model):
  name      = models.CharField(max_length=100)
  email     = models.EmailField(blank=True, null=True)
  is_active = models.BooleanField(default=True)

  def __str__(self):
    return self.name

class Order(models.Model):
  customer   = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='orders')
  folio      = models.CharField(max_length=100, unique=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.folio

class Remission(models.Model):
  STATUS = [
      ('open', 'Open'),
      ('closed', 'Closed'),
  ]

  order      = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='remissions')
  folio      = models.CharField(max_length=100, unique=True)
  status     = models.CharField(max_length=10, choices=STATUS, default='open')
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.folio


class Sale(models.Model):
  remission  = models.ForeignKey('Remission', on_delete=models.CASCADE, related_name='sales')
  subtotal   = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0.0)])
  tax        = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0.0)])
  created_at = models.DateTimeField(auto_now_add=True)

  @property
  def total(self):
    """
    Calcula el total de la venta sumando subtotal + impuestos.
    NO se almacena en BD para garantizar integridad de datos.
    """
    return self.subtotal + self.tax

class CreditAssignment(models.Model):
  remission  = models.ForeignKey('Remission', on_delete=models.CASCADE, related_name='credits')
  amount     = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0.1)])
  reason     = models.CharField(max_length=100)
  created_at = models.DateTimeField(auto_now_add=True)