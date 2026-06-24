from tasks import fatorial,somar

def test_somar_dois_numeros():
    response = somar.apply(args=[10,5]).get()
    assert response == 15

def test_fatorial_passando_como_paramentro_um_numero_normal():
    response = fatorial.apply(args=[5]).get()
    assert response == 120

def test_fatorial_passando_como_paramentro_zero():
    response = fatorial.apply(args=[0]).get()
    assert response == 1
