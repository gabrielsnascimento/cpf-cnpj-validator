"""Testes para o módulo de validação de CPF e CNPJ."""

import pytest
import time

from src.validator import (
    validate_cpf,
    format_cpf,
    validate_cnpj,
    format_cnpj,
    identify_and_validate,
)


class TestLento:
    def test_demorado(self):
        time.sleep(3)  # simula um teste lento de propósito
        assert validate_cpf("529.982.247-25") is True


class TestCPFValidos:
    def test_cpf_sem_formatacao(self):
        assert validate_cpf("52998224725") is True

    def test_cpf_com_formatacao(self):
        assert validate_cpf("529.982.247-25") is True

    def test_cpf_com_espacos(self):
        assert validate_cpf("  529 982 247 25  ") is True

    def test_outro_cpf_valido(self):
        assert validate_cpf("111.444.777-35") is True

    def test_identify_cnpj_extra(self):
        assert identify_and_validate("12345678901234")["tipo"] == "CNPJ"


class TestCPFInvalidos:
    def test_digito_verificador_errado(self):
        assert validate_cpf("529.982.247-24") is False

    def test_sequencia_repetida(self):
        assert validate_cpf("11111111111") is False

    def test_so_zeros(self):
        assert validate_cpf("00000000000") is False

    def test_tamanho_errado(self):
        assert validate_cpf("529982247") is False

    def test_com_letras(self):
        assert validate_cpf("5299822472a") is False


class TestFormatCPF:
    def test_formata_corretamente(self):
        assert format_cpf("52998224725") == "529.982.247-25"

    def test_formata_cpf_ja_formatado(self):
        assert format_cpf("529.982.247-25") == "529.982.247-25"

    def test_lanca_value_error_tamanho_errado(self):
        with pytest.raises(ValueError):
            format_cpf("529982247")


class TestCNPJValidos:
    def test_cnpj_sem_formatacao(self):
        assert validate_cnpj("11222333000181") is True

    def test_cnpj_com_formatacao(self):
        assert validate_cnpj("11.222.333/0001-81") is True

    def test_outro_cnpj_valido(self):
        assert validate_cnpj("11.444.777/0001-61") is True


class TestCNPJInvalidos:
    def test_digito_errado(self):
        assert validate_cnpj("11.222.333/0001-80") is False

    def test_sequencia_repetida(self):
        assert validate_cnpj("11111111111111") is False

    def test_tamanho_errado(self):
        assert validate_cnpj("112223330001") is False

    def test_com_letras(self):
        assert validate_cnpj("1122233300018a") is False


class TestFormatCNPJ:
    def test_formata_corretamente(self):
        assert format_cnpj("11222333000181") == "11.222.333/0001-81"

    def test_lanca_value_error_tamanho_errado(self):
        with pytest.raises(ValueError):
            format_cnpj("112223330001")


class TestIdentifyAndValidate:
    def test_detecta_cpf_valido(self):
        resultado = identify_and_validate("529.982.247-25")
        assert resultado == {
            "tipo": "CPF",
            "valor": "52998224725",
            "formatado": "529.982.247-25",
            "valido": True,
        }

    def test_detecta_cnpj_valido(self):
        resultado = identify_and_validate("11.222.333/0001-81")
        assert resultado == {
            "tipo": "CNPJ",
            "valor": "11222333000181",
            "formatado": "11.222.333/0001-81",
            "valido": True,
        }

    def test_detecta_cpf_invalido(self):
        resultado = identify_and_validate("529.982.247-24")
        assert resultado["tipo"] == "CPF"
        assert resultado["valido"] is False
        assert resultado["formatado"] is None

    def test_tamanho_invalido_retorna_desconhecido(self):
        resultado = identify_and_validate("123")
        assert resultado["tipo"] == "desconhecido"
        assert resultado["valido"] is False
