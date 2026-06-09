"""Dados das seleções e helpers de bandeira.

Conjunto plausível para a Copa de 2026: 48 seleções em 12 grupos (A–L), 4 cada.
Projeto educacional — não corresponde a um sorteio oficial.
"""

# Cada grupo tem 4 seleções, cada uma com nome e código ISO-2 (para o emoji).
GRUPOS = {
    "A": [{"nome": "Brasil", "iso2": "BR"}, {"nome": "Suíça", "iso2": "CH"},
          {"nome": "Camarões", "iso2": "CM"}, {"nome": "Catar", "iso2": "QA"}],
    "B": [{"nome": "Argentina", "iso2": "AR"}, {"nome": "Dinamarca", "iso2": "DK"},
          {"nome": "Arábia Saudita", "iso2": "SA"}, {"nome": "Austrália", "iso2": "AU"}],
    "C": [{"nome": "França", "iso2": "FR"}, {"nome": "Sérvia", "iso2": "RS"},
          {"nome": "Tunísia", "iso2": "TN"}, {"nome": "Peru", "iso2": "PE"}],
    "D": [{"nome": "Inglaterra", "iso2": "ENG"}, {"nome": "Senegal", "iso2": "SN"},
          {"nome": "Equador", "iso2": "EC"}, {"nome": "Irã", "iso2": "IR"}],
    "E": [{"nome": "Espanha", "iso2": "ES"}, {"nome": "Polônia", "iso2": "PL"},
          {"nome": "Gana", "iso2": "GH"}, {"nome": "Costa Rica", "iso2": "CR"}],
    "F": [{"nome": "Portugal", "iso2": "PT"}, {"nome": "Marrocos", "iso2": "MA"},
          {"nome": "Nigéria", "iso2": "NG"}, {"nome": "Panamá", "iso2": "PA"}],
    "G": [{"nome": "Alemanha", "iso2": "DE"}, {"nome": "Japão", "iso2": "JP"},
          {"nome": "Argélia", "iso2": "DZ"}, {"nome": "Nova Zelândia", "iso2": "NZ"}],
    "H": [{"nome": "Holanda", "iso2": "NL"}, {"nome": "México", "iso2": "MX"},
          {"nome": "Egito", "iso2": "EG"}, {"nome": "Mali", "iso2": "ML"}],
    "I": [{"nome": "Bélgica", "iso2": "BE"}, {"nome": "Estados Unidos", "iso2": "US"},
          {"nome": "Costa do Marfim", "iso2": "CI"}, {"nome": "Noruega", "iso2": "NO"}],
    "J": [{"nome": "Itália", "iso2": "IT"}, {"nome": "Coreia do Sul", "iso2": "KR"},
          {"nome": "Chile", "iso2": "CL"}, {"nome": "Áustria", "iso2": "AT"}],
    "K": [{"nome": "Uruguai", "iso2": "UY"}, {"nome": "Canadá", "iso2": "CA"},
          {"nome": "Turquia", "iso2": "TR"}, {"nome": "Paraguai", "iso2": "PY"}],
    "L": [{"nome": "Croácia", "iso2": "HR"}, {"nome": "Colômbia", "iso2": "CO"},
          {"nome": "Suécia", "iso2": "SE"}, {"nome": "Ucrânia", "iso2": "UA"}],
}

# Emojis que não derivam de um ISO-2 simples (nações do Reino Unido usam tag sequences).
_EMOJI_ESPECIAL = {
    "ENG": "🏴\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",
}


def flag_emoji(iso2: str) -> str:
    """Converte um código ISO-2 no emoji da bandeira (regional indicator symbols)."""
    if iso2 in _EMOJI_ESPECIAL:
        return _EMOJI_ESPECIAL[iso2]
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())


def rotulo(time: dict) -> str:
    """Rótulo curto com bandeira + nome, ex.: '🇧🇷 Brasil'."""
    return f"{flag_emoji(time['iso2'])} {time['nome']}"
