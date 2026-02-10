# API de Gestión de Ventas y Remisiones

API REST desarrollada en Django + Django REST Framework (DRF) para administrar el flujo de Clientes, Órdenes, Remisiones, Ventas y Créditos.

## Requisitos Previos

- Python 3.8+
- Virtualenv (recomendado)

## Instalación y Configuración

Sigue estos pasos para levantar el proyecto localmente:

### 1. Clonar y preparar entorno
```bash
git clone https://github.com/FernandoCHT/dj_certiffy.git
cd dj_certiffy
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar migraciones
```bash
python manage.py migrate
```

### 4. Poblar base de datos (Seeds)
```bash
python manage.py seed_db
```

### 5. Correr el servidor
```bash
python manage.py seed_db
```

## Ejecución de Pruebas
El proyecto incluye tests automatizados para validar reglas de negocio y reportes.

```bash
python manage.py test api
```

## Decisiones Técnicas Relevantes
```text
Campo total calculado: Se decidió no persistir el total de la venta en la base de datos, 
sino calcularlo como una @property en el modelo (subtotal + tax).
Esto prioriza la integridad de los datos sobre la optimización prematura de lectura.
```

```text
Validación Atómica en Serializers: Las reglas de negocio críticas (ej. "créditos no pueden exceder ventas") 
se alojaron en el método validate() del Serializer. Esto aprovecha el ciclo de vida de DRF para asegurar 
que ninguna transacción inválida llegue siquiera a intentar guardarse en la base de datos.
```

```text
Estrategia de Testing Determinista (Time-Safe): Para evitar flaky tests (pruebas intermitentes) causados por 
la ejecución cerca de la medianoche o diferencias de zona horaria, se optó por 
fijar explícitamente la hora de los registros de prueba a las 12:00 PM. 
Esto garantiza que las pruebas de agrupación por fecha sean estables y predecibles en cualquier entorno de CI/CD.
```

```text
Manejo de Fechas "User-Friendly" (Inclusivo): Para el endpoint de reportes, se implementó una lógica 
de filtrado inclusivo en el rango final (to). 
Internamente, la API suma un día a la fecha solicitada y utiliza el operador __lt (menor que). 
Esto resuelve la ambigüedad habitual en bases de datos donde 2026-02-09 se interpreta como 00:00:00, asegurando 
que el usuario reciba los datos de todo el día solicitado sin tener que pedir "hasta mañana".
```

```text
Simulación de Datos Históricos (Bypass ORM): Dado que el campo created_at utiliza auto_now_add=True (inmutable al crear), 
se implementó el uso de .update() directo sobre el QuerySet en los tests y seeds. Esto permite 
insertar datos con fechas pasadas para validar correctamente los reportes, sin necesidad de modificar 
la definición estricta del modelo.
```
