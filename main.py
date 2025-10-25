import json
import os
from fastapi import FastAPI, HTTPException
from abc import ABC, abstractmethod
from typing import Dict, Any

app = FastAPI()

# Constantes para las claves del JSON
STATUS = "status"
AMOUNT = "amount"
PAYMENT_METHOD = "payment_method"

# Constantes para los estados de pago
STATUS_REGISTRADO = "REGISTRADO"
STATUS_PAGADO = "PAGADO"
STATUS_FALLIDO = "FALLIDO"

# Path del archivo de datos
DATA_PATH = "data.json"


def initialize_data_file():
    """
    Asegura que el archivo data.json exista antes de intentar leerlo.
    Si no existe, lo crea con un diccionario vacío.
    """
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w") as f:
            json.dump({}, f)


def load_all_payments() -> Dict[str, Any]:
    """Carga todos los pagos desde el archivo JSON."""
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    return data


def save_all_payments(data: Dict[str, Any]):
    """Guarda el diccionario completo de pagos en el JSON."""
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)


def load_payment(payment_id: str) -> Dict[str, Any]:
    """Carga un pago específico por su ID."""
    all_payments = load_all_payments()
    if payment_id not in all_payments:
        raise HTTPException(status_code=404, detail="Payment not found")
    return all_payments[payment_id]


def save_payment_data(payment_id: str, data: Dict[str, Any]):
    """Guarda los datos de un pago específico."""
    all_data = load_all_payments()
    all_data[str(payment_id)] = data
    save_all_payments(all_data)


def save_payment(payment_id: str, amount: float, payment_method: str, status: str):
    """Crea y guarda la estructura de un nuevo pago."""
    data = {
        AMOUNT: amount,
        PAYMENT_METHOD: payment_method,
        STATUS: status,
    }
    save_payment_data(payment_id, data)


# Implementación del Patrón Strategy para Validación

class PaymentStrategy(ABC):
    """
    Interfaz abstracta (Strategy) para definir una estrategia de validación de pago.
    """

    @abstractmethod
    def validate(self, amount: float, all_payments: Dict[str, Any]) -> bool:
        """
        Valida un pago. Retorna True si es válido, False si no.
        """
        pass


class CreditCardStrategy(PaymentStrategy):
    """
    Strategy para Tarjeta de Crédito.
    """

    def validate(self, amount: float, all_payments: Dict[str, Any]) -> bool:
        # Condición 1: Verifica que el pago sea menor a $10.000
        if amount >= 10000:
            return False

        # Condición 2: Valida que no haya más de 1 pago con este medio en estado "REGISTRADO"
        registered_cc_count = 0
        for payment in all_payments.values():
            if (payment[PAYMENT_METHOD] == "Tarjeta de Crédito" and
                    payment[STATUS] == STATUS_REGISTRADO):
                registered_cc_count += 1

        # Si hay más de 1 la validación falla.
        # Si hay solo 1 (el que estamos intentando pagar), la validación pasa.
        if registered_cc_count > 1:
            return False

        return True


class PayPalStrategy(PaymentStrategy):
    """
    Strategy para PayPal.
    """

    def validate(self, amount: float, all_payments: Dict[str, Any]) -> bool:
        # Condición 1: Verifica que el pago sea menor de $5000 [cite: 47]
        if amount >= 5000:
            return False

        # No se necesitan los all_payments aquí, pero mantenemos la firma
        return True


class DefaultStrategy(PaymentStrategy):
    """
    Strategy por defecto para métodos desconocidos. Siempre falla.
    """

    def validate(self, amount: float, all_payments: Dict[str, Any]) -> bool:
        return False


def get_payment_strategy(method: str) -> PaymentStrategy:
    """
    Factory para obtener la estrategia de validación según el método de pago.
    """
    if method == "Tarjeta de Crédito":
        return CreditCardStrategy()
    elif method == "PayPal":
        return PayPalStrategy()
    else:
        # Si el metodo no se reconoce, usamos una estrategia que siempre falla.
        return DefaultStrategy()


# Endpoints de la API

@app.on_event("startup")
async def startup_event():
    """
    Al iniciar la aplicación, nos aseguramos que el data.json exista.
    """
    initialize_data_file()


@app.get("/payments")
async def get_payments():
    """
    Endpoint para obtener todos los pagos del sistema.
    """
    return load_all_payments()


@app.post("/payments/{payment_id}")
async def register_payment(payment_id: str, amount: float, payment_method: str):
    """
    Endpoint para registrar un pago con su información.
    El pago se crea en estado "REGISTRADO".
    """
    try:
        # Verificamos si el pago ya existe para no sobrescribirlo
        load_payment(payment_id)
        raise HTTPException(status_code=400, detail="Payment ID already exists")
    except HTTPException as e:
        # Si el error es 404 (no encontrado), podemos crearlo.
        if e.status_code != 404:
            raise e

    # Guardamos el nuevo pago en estado REGISTRADO
    save_payment(payment_id, amount, payment_method, STATUS_REGISTRADO)
    return {"message": "Payment registered", "payment_id": payment_id, STATUS: STATUS_REGISTRADO}


@app.post("/payments/{payment_id}/update")
async def update_payment(payment_id: str, amount: float, payment_method: str):
    """
    Endpoint para actualizar la información (monto y metodo) de un pago existente.
    Solo se puede actualizar si está en estado "REGISTRADO".
    """
    payment = load_payment(payment_id)

    # Flujo 4: Solo se puede updatear si está en REGISTRADO
    if payment[STATUS] != STATUS_REGISTRADO:
        raise HTTPException(status_code=400,
                            detail=f"Cannot update payment in status {payment[STATUS]}")

    # Actualizamos los datos
    payment[AMOUNT] = amount
    payment[PAYMENT_METHOD] = payment_method

    save_payment_data(payment_id, payment)
    return {"message": "Payment updated", "payment_id": payment_id, "data": payment}


@app.post("/payments/{payment_id}/pay")
async def pay_payment(payment_id: str):
    """
    Endpoint para marcar un pago como pagado.
    Acá se ejecuta la lógica de validación (Strategy).
    """
    payment = load_payment(payment_id)

    # Solo podemos pagar algo que esté registrado
    if payment[STATUS] != STATUS_REGISTRADO:
        raise HTTPException(status_code=400,
                            detail=f"Payment cannot be paid from status {payment[STATUS]}")

    all_payments = load_all_payments()

    # Usamos el Patrón Strategy
    # Obtenemos la estrategia correspondiente
    strategy = get_payment_strategy(payment[PAYMENT_METHOD])

    # Ejecutamos la validación
    is_valid = strategy.validate(payment[AMOUNT], all_payments)

    # Cambiamos el estado según el resultado
    if is_valid:
        payment[STATUS] = STATUS_PAGADO
        message = "Payment successful"
    else:
        payment[STATUS] = STATUS_FALLIDO
        message = "Payment failed validation"

    save_payment_data(payment_id, payment)
    return {"message": message, "payment_id": payment_id, STATUS: payment[STATUS]}


@app.post("/payments/{payment_id}/revert")
async def revert_payment(payment_id: str):
    """
    Endpoint para revertir un pago al estado registrado.
    Solo se puede revertir si está en estado "FALLIDO".
    """
    payment = load_payment(payment_id)

    # Solo se puede revertir un pago FALLIDO
    if payment[STATUS] != STATUS_FALLIDO:
        raise HTTPException(status_code=400,
                            detail=f"Cannot revert payment in status {payment[STATUS]}")

    payment[STATUS] = STATUS_REGISTRADO
    save_payment_data(payment_id, payment)

    return {"message": "Payment reverted to REGISTRADO", "payment_id": payment_id, STATUS: payment[STATUS]}