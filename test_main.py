#Importacion de clases
from main import (
    CreditCardStrategy, 
    PayPalStrategy, 
    STATUS_REGISTRADO, 
    PAYMENT_METHOD,
    STATUS
)

# Primer testeo: Paypal
def test_paypal_strategy_valid():
    """
    Prueba que la estrategia de PayPal apruebe un monto válido.
    Condición: menor a $5000
    """
    strategy = PayPalStrategy()
    is_valid = strategy.validate(amount=4999, all_payments={})
    assert is_valid == True

#Segundo testeo: Paypal
def test_paypal_strategy_invalid_amount():
    """
    Prueba que la estrategia de PayPal rechace un monto inválido.
    Condición: mayor a $5000
    """
    strategy = PayPalStrategy()
    is_valid = strategy.validate(amount=5001, all_payments={})

    assert is_valid == False

#Tercer testeo: Tarjeta de crédito
def test_credit_card_strategy_invalid_multiple_registered():
    """
    Prueba que la estrategia de Tarj de Cred rechace un pago si ya hay otro REGISTRADO.
    """
    strategy = CreditCardStrategy()

    # Creamos un estado en el que ya existe un pago registrado.
    mock_all_payments = {
        "pago-existente": {
            STATUS: STATUS_REGISTRADO,
            PAYMENT_METHOD: "Tarjeta de Crédito",
            "amount": 100
        },
        # Este es el nuevo pago que estamos intentando validar.
        "pago-nuevo": {
            STATUS: STATUS_REGISTRADO,
            PAYMENT_METHOD: "Tarjeta de Crédito",
            "amount": 200
        }
    }

    # Validamos un monto que sería válido pero que debe fallar por la otra condición

    is_valid = strategy.validate(amount=1000, all_payments=mock_all_payments)

    assert is_valid == False