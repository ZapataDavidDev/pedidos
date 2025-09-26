#  Procesador de Pedidos Asíncrono con Django y Huey

**Descripción del Proyecto**

Este proyecto es una solución para implementar un pipeline de procesamiento de pedidos. La aplicación utiliza Django como framework web y Huey como un gestor de colas de trabajo ligero y eficiente para realizar el procesamiento de forma asíncrona y concurrente con manejo de excepciones y generacion de logs.

El sistema simula la recepción de pedidos, los encola y los procesa en segundo plano a través de un flujo de 4 etapas, guardando un historial detallado de cada ejecución y el resultado final en una base de datos SQLite.

✨ Características Principales
Procesamiento Asíncrono: La recepción de pedidos y el procesamiento pesado están completamente desacoplados, garantizando que la aplicación web responda al instante.

Concurrencia Real: El sistema está configurado para usar 4 workers en paralelo (basados en hilos), permitiendo procesar múltiples pedidos simultáneamente.

Flujo de 4 Etapas: Cada pedido pasa por un pipeline robusto:

Validación de datos de entrada.

Enriquecimiento de productos consultando una API externa.

Cálculo de totales y descuentos.

Persistencia y validación en la unicidad de los pedidos.

Trazabilidad Completa: Se implementó un sistema de auditoría que guarda un registro permanente de cada tarea ejecutada, incluyendo su estado (Iniciada, Completada, Fallida), tiempos, worker asignado y un enlace directo al pedido que procesó.

Manejo de Errores y Reintentos: Huey gestiona automáticamente los reintentos para fallos transitorios (ej. errores de red). El código maneja de forma controlada los datos inválidos (ej. SKUs no existentes), registrándolos como tareas fallidas.

Se utiliza el panel de administración de Django para visualizar tanto los pedidos procesados finales como el historial detallado de las tareas.

El proyecto actualmente no utiliza variables de entorno (.env) para la configuración sensible pero es totalmente necesario para una aplicacion real.

🏗️ Arquitectura Conceptual
El flujo de datos sigue un patrón Productor/Consumidor clásico:

[Vista de Django (Productor)] -> [Cola de Tareas (huey.db)] -> [Workers de Huey (Consumidor)] -> [Base de Datos Principal (db.sqlite3)] -> [Visualizacion Pedidos y tareas desde Admin Django]

🚀 Requisitos Previos
Python 3.11 o superior
Instalación para Windows


Git

⚙️ Instalación y Configuración
Siga los siguientes pasos para poner en marcha el proyecto, ejecutar en terminal de PowerShell (recomendado):

Clonar el repositorio:

Bash

git clone https://github.com/ZapataDavidDev/pedidos.git
cd pedidos


Crear y activar un entorno virtual:

# Crear el entorno
python -m venv venv

# Activar en Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activar en Linux/macOS
source venv/bin/activate

Instalar las dependencias:
pip install -r requirements.txt

Configurar la base de datos y el superusuario:


# Aplicar las migraciones para crear las tablas
python manage.py migrate

# Crear un usuario para acceder al panel de administración
python manage.py createsuperuser   

▶️ Ejecución de la Aplicación
Para ejecutar la aplicación, es necesario tener dos terminales de PowerShell abiertas en la carpeta del proyecto, con el entorno virtual activado en cada una.

Terminal 1: Iniciar el Worker de Huey
Este proceso se encarga de escuchar y procesar las tareas de la cola.

python manage.py run_huey

Terminal 2: Iniciar el Servidor de Django
Este es el servidor web estándar de Django.


python manage.py runserver

🧪 Cómo Probar y Verificar
Lanzar las Tareas: Con ambos servicios corriendo, abra un navegador web y visite la siguiente URL para encolar una tanda de 10 pedidos dinámicos:

http://127.0.0.1:8000/pedidos/iniciar/

Observar el Worker: Inmediatamente, la terminal donde se está ejecutando run_huey mostrará en tiempo real los logs del procesamiento de los 10 pedidos en paralelo.

<img width="1918" height="282" alt="image" src="https://github.com/user-attachments/assets/f55edd58-843a-42c1-b726-ea4a7d15e0ca" />


Revisar los Resultados en el Admin:

Acceda al panel de administración: http://127.0.0.1:8000/admin/

Inicie sesión con las credenciales creadas.

Ver el Historial de Tareas:

Vaya a la sección "Pedidos_App" -> "Task historys".

<img width="1918" height="980" alt="image" src="https://github.com/user-attachments/assets/9f34cdb0-1b0a-4331-9216-45447eaa840a" />


Verá el registro de las 10 tareas ejecutadas. Algunas aparecerán como "Completada" y otras (las que tenían datos inválidos) como "Fallida", con su respectivo mensaje de error.

En las tareas completadas, la columna "Pedido Asociado" contiene un enlace directo al registro del pedido que procesó.

Ver los Pedidos Procesados:




Vaya a la sección "Pedidos_App" -> "Pedido procesados".

<img width="1917" height="972" alt="image" src="https://github.com/user-attachments/assets/61071486-c1fa-482f-a71b-33fb8439928c" />


Aquí verá únicamente los registros de los pedidos que se procesaron exitosamente.

Puede visitar la URL de inicio varias veces para generar y procesar nuevas tandas de pedidos.
