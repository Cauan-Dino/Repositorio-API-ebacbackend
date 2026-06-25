def test_fatorial():
    resultado = 1
    for i in range(2,6):
        resultado *= i
    assert resultado == 120

def test_soma():
    resultado = 5 + 5
    assert resultado == 10