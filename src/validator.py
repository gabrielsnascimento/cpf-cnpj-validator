"""Validação e formatação de CPF e CNPJ."""
# validador de documentos brasileiros
import re


def _strip(value):
    """Remove pontos, traços, barras e espaços de uma string."""
    return re.sub(r"[.\-/\s]", "", str(value))


def _check_digit(digits, weights):
    """Calcula um dígito verificador a partir dos pesos oficiais."""
    total = sum(int(d) * w for d, w in zip(digits, weights))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def validate_cpf(cpf):
    """Valida um CPF usando os dois dígitos verificadores oficiais."""
    cpf = _strip(cpf)
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    # Rejeita sequências repetidas como 111.111.111-11
    if cpf == cpf[0] * 11:
        return False

    first = _check_digit(cpf[:9], range(10, 1, -1))
    if first != int(cpf[9]):
        return False

    second = _check_digit(cpf[:10], range(11, 1, -1))
    if second != int(cpf[10]):
        return False

    return True


def format_cpf(cpf):
    """Retorna o CPF no formato 123.456.789-09."""
    cpf = _strip(cpf)
    if len(cpf) != 11 or not cpf.isdigit():
        raise ValueError("CPF deve conter 11 dígitos")
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def validate_cnpj(cnpj):
    """Valida um CNPJ usando os dois dígitos verificadores oficiais."""
    cnpj = _strip(cnpj)
    if len(cnpj) != 14 or not cnpj.isdigit():
        return False
    # Rejeita sequências repetidas como 11.111.111/1111-11
    if cnpj == cnpj[0] * 14:
        return False

    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first = _check_digit(cnpj[:12], first_weights)
    if first != int(cnpj[12]):
        return False

    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second = _check_digit(cnpj[:13], second_weights)
    if second != int(cnpj[13]):
        return False

    return True


def format_cnpj(cnpj):
    """Retorna o CNPJ no formato 11.222.333/0001-81."""
    cnpj = _strip(cnpj)
    if len(cnpj) != 14 or not cnpj.isdigit():
        raise ValueError("CNPJ deve conter 14 dígitos")
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def identify_and_validate(value):
    """Detecta se é CPF (11 dígitos) ou CNPJ (14 dígitos), valida e formata.

    Retorna um dict com as chaves: tipo, valor, formatado e valido.
    Para entradas que não tenham 11 nem 14 dígitos, tipo é "desconhecido".
    """
    digits = _strip(value)

    if len(digits) == 11:
        valido = validate_cpf(digits)
        return {
            "tipo": "CPF",
            "valor": digits,
            "formatado": format_cpf(digits) if valido else None,
            "valido": valido,
        }

    if len(digits) == 14:
        valido = validate_cnpj(digits)
        return {
            "tipo": "CNPJ",
            "valor": digits,
            "formatado": format_cnpj(digits) if valido else None,
            "valido": valido,
        }

    return {
        "tipo": "desconhecido",
        "valor": digits,
        "formatado": None,
        "valido": False,
    }
