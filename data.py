"""Dados das seleções e helpers de bandeira.

Sorteio oficial da Copa do Mundo de 2026 (EUA/Canadá/México): 48 seleções em
12 grupos (A–L), 4 cada. Os slots de repescagem (playoffs UEFA e intercontinental,
decididos em março/2026) já estão resolvidos para as seleções classificadas.
"""

# Cada grupo tem 4 seleções, cada uma com nome e código ISO-2 (para o emoji).
# Ordem dentro do grupo = ordem dos potes do sorteio (pote 1 → pote 4).
GRUPOS = {
    "A": [{"nome": "México", "iso2": "MX"}, {"nome": "África do Sul", "iso2": "ZA"},
          {"nome": "Coreia do Sul", "iso2": "KR"}, {"nome": "Tchéquia", "iso2": "CZ"}],
    "B": [{"nome": "Canadá", "iso2": "CA"}, {"nome": "Bósnia e Herzegovina", "iso2": "BA"},
          {"nome": "Catar", "iso2": "QA"}, {"nome": "Suíça", "iso2": "CH"}],
    "C": [{"nome": "Brasil", "iso2": "BR"}, {"nome": "Marrocos", "iso2": "MA"},
          {"nome": "Escócia", "iso2": "SCT"}, {"nome": "Haiti", "iso2": "HT"}],
    "D": [{"nome": "Estados Unidos", "iso2": "US"}, {"nome": "Paraguai", "iso2": "PY"},
          {"nome": "Austrália", "iso2": "AU"}, {"nome": "Turquia", "iso2": "TR"}],
    "E": [{"nome": "Alemanha", "iso2": "DE"}, {"nome": "Curaçao", "iso2": "CW"},
          {"nome": "Costa do Marfim", "iso2": "CI"}, {"nome": "Equador", "iso2": "EC"}],
    "F": [{"nome": "Holanda", "iso2": "NL"}, {"nome": "Japão", "iso2": "JP"},
          {"nome": "Suécia", "iso2": "SE"}, {"nome": "Tunísia", "iso2": "TN"}],
    "G": [{"nome": "Bélgica", "iso2": "BE"}, {"nome": "Egito", "iso2": "EG"},
          {"nome": "Irã", "iso2": "IR"}, {"nome": "Nova Zelândia", "iso2": "NZ"}],
    "H": [{"nome": "Espanha", "iso2": "ES"}, {"nome": "Cabo Verde", "iso2": "CV"},
          {"nome": "Arábia Saudita", "iso2": "SA"}, {"nome": "Uruguai", "iso2": "UY"}],
    "I": [{"nome": "França", "iso2": "FR"}, {"nome": "Senegal", "iso2": "SN"},
          {"nome": "Iraque", "iso2": "IQ"}, {"nome": "Noruega", "iso2": "NO"}],
    "J": [{"nome": "Argentina", "iso2": "AR"}, {"nome": "Argélia", "iso2": "DZ"},
          {"nome": "Áustria", "iso2": "AT"}, {"nome": "Jordânia", "iso2": "JO"}],
    "K": [{"nome": "Portugal", "iso2": "PT"}, {"nome": "RD Congo", "iso2": "CD"},
          {"nome": "Uzbequistão", "iso2": "UZ"}, {"nome": "Colômbia", "iso2": "CO"}],
    "L": [{"nome": "Inglaterra", "iso2": "ENG"}, {"nome": "Croácia", "iso2": "HR"},
          {"nome": "Gana", "iso2": "GH"}, {"nome": "Panamá", "iso2": "PA"}],
}

# Emojis que não derivam de um ISO-2 simples (nações do Reino Unido usam tag sequences).
_EMOJI_ESPECIAL = {
    "ENG": "🏴\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",
    "SCT": "🏴\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F",
}


def flag_emoji(iso2: str) -> str:
    """Converte um código ISO-2 no emoji da bandeira (regional indicator symbols)."""
    if iso2 in _EMOJI_ESPECIAL:
        return _EMOJI_ESPECIAL[iso2]
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())


def rotulo(time: dict) -> str:
    """Rótulo curto com bandeira + nome, ex.: '🇧🇷 Brasil'."""
    return f"{flag_emoji(time['iso2'])} {time['nome']}"
