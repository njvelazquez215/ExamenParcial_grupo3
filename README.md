# API de Gestión de Pagos (Examen Unidad 1)

Este proyecto implementa una API pública en FastAPI para gestionar un sistema de pagos en línea, siguiendo las pautas de un examen académico. La API maneja el registro, pago, actualización y reversión de pagos, implementando lógicas de validación específicas para diferentes métodos de pago.

## URLs del Proyecto

* **API Desplegada (Render):** `https://ejercicioredes-mia.onrender.com/docs`
* **Repositorio (GitHub):** `https://github.com/njvelazquez215/ExamenParcial_grupo3`

---

## 1. Instrucciones de Instalación y Ejecución

Sigue estos pasos para correr el proyecto en un entorno local.

### Prerrequisitos

* Python 3.10 o superior
* Git

### Instalación

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/njvelazquez215/ExamenParcial_grupo3.git](https://github.com/njvelazquez215/ExamenParcial_grupo3.git)
    cd ExamenParcial_grupo3
    ```
2.  Crea y activa un entorno virtual:
    ```bash
    # En macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    
    # En Windows
    python -m venv .venv
    .\.venv\Scripts\activate
    ```
3.  Instala las dependencias del proyecto:
    ```bash
    pip install -r requirements.txt
    ```

### Ejecución (Desarrollo Local)

Para correr la API en modo de desarrollo con recarga automática, utiliza el siguiente comando:

```bash
fastapi dev main.py
```

a API estará disponible en http://127.0.0.1:8000. La documentación interactiva (Swagger) estará en http://127.0.0.1:8000/docs.

Ejecución (Tests Automáticos)

Para ejecutar los tests unitarios y de integración, corre el siguiente comando:

```bash
pytest
```

2. Decisiones de Diseño y Arquitectura 

Para resolver el requisito de que cada método de pago tiene una lógica de validación y ejecución específica, se implementó una arquitectura de software limpia basada en dos patrones de diseño clásicos: Strategy y Factory.

Patrón Strategy

Decidimos usar el Patrón Strategy para encapsular las reglas de validación de cada método de pago en clases separadas.

Creamos una interfaz abstracta PaymentStrategy que define un único método: validate().

Creamos clases concretas para cada método de pago (CreditCardStrategy, PayPalStrategy) que implementan esta interfaz .

Trade-off: Esto añade más clases al proyecto en lugar de un solo método con if-else. Sin embargo, el beneficio es un código mucho más limpio, desacoplado y que cumple con el Principio de Abierto/Cerrado. El endpoint /pay no necesita ser modificado si se agregan nuevos métodos de pago.

Patrón Factory

Para evitar que el endpoint /pay tenga la responsabilidad de decidir qué estrategia crear, usamos un Simple Factory.

La función get_payment_strategy(method) actúa como una fábrica.

Recibe un string con el nombre del método (ej: "PayPal") y devuelve la instancia del objeto de estrategia correspondiente (ej: PayPalStrategy()).

Esta combinación nos da un código limpio y fácil de extender. Si mañana se agrega un nuevo método de pago "Transferencia", solo necesitaríamos crear la clase TransferStrategy y añadir una línea en la fábrica, sin tocar el código de la API.

Diagrama de Clases

El siguiente diagrama ilustra la arquitectura de patrones implementada:

![Diagrama de Clases de la API de Pagos](./diagrama/DiagramaClases.png)

Explicación del Diagrama:

PaymentAPI (la app FastAPI) recibe una llamada en /pay. Para validar, le pide una estrategia a...

PaymentStrategyFactory. Esta "fábrica" crea y devuelve un objeto que cumple con la interfaz...

PaymentStrategy.

Las clases concretas CreditCardStrategy y PayPalStrategy implementan esta interfaz, cada una con su lógica de validate().

La PaymentAPI finalmente usa el método validate() del objeto que recibió, sin saber (ni importarle) de qué tipo concreto es.

3. Flujo de Pago y Transiciones de Estado
El sistema maneja un flujo de estados simple para cada pago, como se describe en la consigna .

Registrar (POST /payments/{id}): Crea un pago en estado REGISTRADO.

Pagar (POST /payments/{id}/pay):

Si la validación (Strategy) es exitosa, pasa a PAGADO.

Si la validación es fallida, pasa a FALLIDO.

Revertir (POST /payments/{id}/revert): Un pago FALLIDO puede volver a REGISTRADO.

Actualizar (POST /payments/{id}/update): Los datos de un pago solo pueden cambiarse si está en estado REGISTRADO.

Diagrama de Estados

```bash
stateDiagram-v2
    direction LR
    [*] --> REGISTRADO : /payments/{id}
    
    REGISTRADO --> PAGADO : /pay (Validación OK)
    REGISTRADO --> FALLIDO : /pay (Validación Falla)
    REGISTRADO --> REGISTRADO : /update
    
    FALLIDO --> REGISTRADO : /revert
    
    PAGADO --> [*]
```

4. Suposiciones Asumidas
Persistencia: Se utiliza un archivo data.json como capa de persistencia, según el código de referencia. Es una solución simple adecuada para un examen, pero en producción se reemplazaría por una base de datos real (ej. PostgreSQL).

Validación de Tarjeta de Crédito: La consigna indica "Valida que no haya más de 1 pago con este medio de pago en estado 'REGISTRADO'" . Asumimos que "más de 1" significa que si ya existe 1 pago (pago-A) y se intenta validar uno nuevo (pago-B), el conteo total es 2, y por lo tanto pago-B debe fallar.

Métodos Desconocidos: Cualquier método de pago que no sea "Tarjeta de Crédito" o "PayPal" es considerado inválido y fallará la validación (se usa DefaultStrategy).

Atomicidad: En un sistema real, las operaciones de lectura y escritura sobre data.json deberían ser atómicas (usando locks) para prevenir race conditions. Para este proyecto, se omite esa complejidad.

5. Integración Continua y Despliegue Continuo (CI/CD)
El repositorio está configurado con GitHub Actions para automatizar los procesos de testing y despliegue.

Workflow 1: Tests Automáticos en Pull Requests (run-tests.yml)

Trigger: Se ejecuta automáticamente en cada pull_request que apunta a la rama main.

Acción: Levanta un entorno de Python, instala las dependencias (requirements.txt) y ejecuta la suite completa de pytest.

Objetivo: Asegurar que ningún cambio que se integre a main rompa la funcionalidad existente.

Workflow 2: Despliegue Automático a Producción (deploy.yml)

Trigger: Se ejecuta automáticamente en cada push (o merge) a la rama production.

Acción: Ejecuta un comando curl que "llama" a un Deploy Hook de Render, el cual está guardado de forma segura en los Secretos de GitHub.

Objetivo: Desplegar la nueva versión de la API de forma automática en el entorno de producción (Render) solo cuando los cambios han sido aprobados e integrados en la rama de despliegue.