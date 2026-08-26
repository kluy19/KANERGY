import streamlit as st
import re

#Se precisar comente o markdown abaixo para retirar o estilo personalizado
st.markdown("""
<style>

/* SELECTBOX */
div[data-baseweb="select"] > div {
    background-color: #111827;
    color: white;
    border: 2px solid #f59e0b;
    border-radius: 10px;
}

/* TEXTO INTERNO */
div[data-baseweb="select"] span {
    color: white;
    font-weight: 600;
}

/* LABEL */
label {
    color: #f59e0b !important;
    font-size: 16px !important;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)



# ===== CONFIG =====
st.set_page_config(page_title="Sistema Energia Solar", layout="centered")

# ===== INPUT =====
def input_float(label, key):
    if key not in st.session_state:
        st.session_state[key] = ""

    valor = st.text_input(label, key=key)

    try:
        return float(valor.replace(",", "."))
    except:
        return None

# ===== FUNÇÕES =====
def calcular_potencia(qtd, pot):
    return qtd * pot / 1000

def calcular_geracao(kwp, fator):
    return kwp * fator

def calcular_string(qtd, tensao, corrente):
    v_total = qtd * tensao
    return f"{v_total:.2f}V/{corrente:.2f}A".replace(".", ",")

def calcular_area(ac, al, qtt):
    area = ac * al * qtt / 1000**2
    extra = ac * 0.02 * (qtt - 1) / 1000
    return area, area + extra

# ===== FORMATADOR MELHORADO =====
def formatar_endereco(texto):
    import re

    estados = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
        "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
        "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
        "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba",
        "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
        "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RS": "Rio Grande do Sul", "RO": "Rondônia",
        "RR": "Roraima", "SC": "Santa Catarina",
        "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
    }

    # ===== LIMPEZA =====
    texto = texto.replace("\r", "\n")

    linhas = []
    for l in texto.split("\n"):
        l = l.strip()

        if not l:
            continue

        # remove espaços duplos
        l = re.sub(r"\s+", " ", l)

        linhas.append(l)

    rua = ""
    bairro = ""
    cidade = ""
    estado = ""
    cep = ""

    # ===== CEP =====
    cep_match = re.search(r"\d{5}-?\d{3}", texto)

    if cep_match:
        cep = cep_match.group()

        # padroniza
        if "-" not in cep:
            cep = cep[:5] + "-" + cep[5:]

    # ===== RUA =====
    if linhas:
        rua = linhas[0].title()

    # ===== PROCESSA LINHAS =====
    for linha in linhas[1:]:

        linha_upper = linha.upper()

        # ignora linha CEP
        if "CEP" in linha_upper:
            continue

        # ===== BAIRRO / CIDADE / ESTADO =====
        if "/" in linha:

            partes = [p.strip() for p in linha.split("/")]

            if len(partes) >= 2:

                # bairro
                if not bairro:
                    bairro = partes[0].title()

                resto = partes[1]

                # cidade - UF
                match = re.search(r"(.+)-\s*([A-Z]{2})", resto)

                if match:
                    cidade = match.group(1).strip().title()

                    uf = match.group(2).strip().upper()

                    estado = estados.get(uf, uf)

                else:
                    cidade = resto.title()

        # ===== LINHA SOMENTE CIDADE - UF =====
        elif "-" in linha and not cidade:

            match = re.search(r"(.+)-\s*([A-Z]{2})", linha)

            if match:
                cidade = match.group(1).strip().title()

                uf = match.group(2).strip().upper()

                estado = estados.get(uf, uf)

        # ===== POSSÍVEL BAIRRO =====
        elif not bairro and len(linha.split()) <= 6:
            bairro = linha.title()

    # ===== REMOVE DUPLICAÇÕES =====
    campos = []

    for item in [rua, bairro, cidade, estado]:

        item = item.strip()

        if not item:
            continue

        # evita repetir
        if item.lower() not in [c.lower() for c in campos]:
            campos.append(item)

    endereco = ", ".join(campos)

    if cep:
        endereco += f", CEP {cep}"

    endereco += "."

    return endereco

def disjuntor_por_corrente(corrente_inversor):
    corrente_projeto = corrente_inversor * 1.25

    disjuntores = [6, 10, 16, 20, 25, 32, 40, 50, 63, 70, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]

    disj_escolhido = None
    for d in disjuntores:
        if d >= corrente_projeto:
            disj_escolhido = d
            break

    return disj_escolhido, corrente_projeto

def cabo_por_disjuntor(disjuntor):
    tabela_cabos = {
        6: "1,5 mm²",
        10: "1,5 mm²",
        16: "2,5 mm²",
        20: "2,5 mm²",
        25: "4 mm²",
        32: "6 mm²",
        40: "6 mm²",
        50: "10 mm²",
        63: "16 mm²",
        70: "16 mm²",
        80: "25 mm²",
        100: "35 mm²",
        125: "50 mm²",
        160: "70 mm²",
        200: "95 mm²",
        250: "120 mm²",
        315: "185 mm²",
        400: "240 mm²",
        500: "300 mm²",
        630: "400 mm²"
    }

    return tabela_cabos.get(disjuntor, "Consultar dimensionamento")

def formatar_telefone(k):
    try:
        k = k.strip()

        ddd, numero = k.split()

        primeiro = "9"
        resto = numero

        return f"({ddd}) {primeiro} {resto}"

    except:
        return "Formato inválido"

# ===== BANCO DE DADOS =====

PAINEIS = {
    "DAH": {
        "[620W] DHN-66Z16/DG-620W 620W": {
            "fabricante": "DAH SOLAR",
            "modelo": "DHN-66Z16/DG-620W",
            "potencia": 620,
            "eficiencia": "22,95%",
            "area": "2382x1134",
            "Imp": "15,01",
            "Vmp": "41,30",
            "Isc": "16,00",
            "Voc": "48,60",
        },
    },
    "DMEGC SOLAR": {
        "[620W] DM620G12RT-B66HSW 620W": {
            "fabricante": "DMEGC SOLAR",
            "modelo": "DM620G12RT-B66HSW",
            "potencia": 620,
            "eficiencia": "23,00%",
            "area": "2382x1134",
            "Imp": "15,20",
            "Vmp": "40,85",
            "Isc": "16,11",
            "Voc": "49,09",
        },
    },
    "ERA SOLAR": {
        "[620W] ERA-RC66HD620M(CF) 620W": {
            "fabricante": "ERA SOLAR",
            "modelo": "ERA-RC66HD620M(CF)",
            "potencia": 620,
            "eficiencia": "22,95%",
            "area": "2382x1134",
            "Imp": "15,45",
            "Vmp": "40,15",
            "Isc": "16,15",
            "Voc": "48,50",
        },
        "[630W] ERA-RC66HD630M(CF) 630W": {
            "fabricante": "ERA SOLAR",
            "modelo": "ERA-RC66HD630M(CF)",
            "potencia": 630,
            "eficiencia": "23,32%",
            "area": "2382x1134",
            "Imp": "15,57",
            "Vmp": "40,47",
            "Isc": "16,25",
            "Voc": "48,80",
        }
    },
    "GOKIN": {
        "[610W] GK-4-66HTBD-610M 610W": {
            "fabricante": "GOKIN",
            "modelo": "GK-4-66HTBD-610M",
            "potencia": 610,
            "eficiencia": "23,00%",
            "area": "2382x1134",
            "Imp": "15,18",
            "Vmp": "40,22",
            "Isc": "16,07",
            "Voc": "48,00",
        },
    },
    "HANERSUN": {
        "[610W] HN21RN-66HT610W 610W": {
            "fabricante": "HANERSUN",
            "modelo": "HN21RN-66HTT610W",
            "potencia": 610,
            "eficiencia": "22,6%",
            "area": "2382x1134",
            "Imp": "15,03",
            "Vmp": "40,59",
            "Isc": "15,94",
            "Voc": "48,72",
        },
    },
    "HONOR SOLAR": {
        "[600W] HY-M16/144H-600W 600W": {
            "fabricante": "HONOR SOLAR",
            "modelo": "HY-M16/144H-600W",
            "potencia": 600,
            "eficiencia": "22,2%",
            "area": "2382x1134",
            "Imp": "13,67",
            "Vmp": "43,90",
            "Isc": "14,53",
            "Voc": "52,34",
        },
    },
    "JINKO": {
        "[620W] JKM620N-66HL4M-BDV 620W": {
            "fabricante": "JINKO",
            "modelo": "JKM620N-66HL4M-BDV",
            "potencia": 620,
            "eficiencia": "23,32%",
            "area": "2382x1134",
            "Imp": "15,36",
            "Vmp": "41,02",
            "Isc": "16,20",
            "Voc": "49,48",
        },
        "[630W] JKM630N-66HL4M-BDV 630W": {
            "fabricante": "JINKO",
            "modelo": "JKM630N-66HL4M-BDV",
            "potencia": 630,
            "eficiencia": "23,32%",
            "area": "2382x1134",
            "Imp": "15,36",
            "Vmp": "41,02",
            "Isc": "16,20",
            "Voc": "49,48",
        },
    },
    "MAXEON": {
        "[550W] SPR-P6-550-UPP 550W": {
            "fabricante": "MAXEON",
            "modelo": "SPR-P6-550-UPP",
            "potencia": 550,
            "eficiencia": "21,10%",
            "area": "2384x1092",
            "Imp": "13,85",
            "Vmp": "39,70",
            "Isc": "14,68",
            "Voc": "47,10",
        },
    },
    "OSDA": {
        "[585W] ODA585-36V-MHD 585W": {
            "fabricante": "OSDA",
            "modelo": "ODA585-36V-MHD",
            "potencia": 585,
            "eficiencia": "22,6%",
            "area": "2382x1134",
            "Imp": "13,76",
            "Vmp": "42,52",
            "Isc": "14,55",
            "Voc": "51,16",
        },
        "[590W] ODA590-36V-MHD 590W": {
            "fabricante": "OSDA",
            "modelo": "ODA590-36V-MHD",
            "potencia": 590,
            "eficiencia": "22,83%",
            "area": "2278x1134",
            "Imp": "13,83",
            "Vmp": "42,67",
            "Isc": "14,63",
            "Voc": "51,41",
        },
        "[610W] ODA610-33V-MHDRz 610W": {
            "fabricante": "OSDA",
            "modelo": "ODA610-33V-MHDRz",
            "potencia": 610,
            "eficiencia": "22,6%",
            "area": "2382x1134",
            "Imp": "15,08",
            "Vmp": "40,46",
            "Isc": "15,96",
            "Voc": "48,68",
        },
    },
    "PULLING ENERGY": {
        "[585W] PU585SNM102 585W": {
            "fabricante": "PULLING ENERGY",
            "modelo": "PU585SNM102",
            "potencia": 585,
            "eficiencia": "22,65%",
            "area": "2382x1134",
            "Imp": "14,44",
            "Vmp": "40,51",
            "Isc": "15,27",
            "Voc": "48,42",
        },
        "[590W] PU590DNM102 590W": {
            "fabricante": "PULLING ENERGY",
            "modelo": "PU590DNM102",
            "potencia": 590,
            "eficiencia": "22,84%",
            "area": "2278x1134",
            "Imp": "14,49",
            "Vmp": "40,72",
            "Isc": "15,32",
            "Voc": "48,62",
        },
    },
    "RONMA": {
        "[585W] RM-585W-182M/144TB 585W": {
            "fabricante": "RONMA",
            "modelo": "RM-585W-182M/144TB",
            "potencia": 585,
            "eficiencia": "22,6%",
            "area": "2278×1134",
            "Imp": "13,52",
            "Vmp": "43,27",
            "Isc": "14,36",
            "Voc": "51,50",
        },
        "[590W] RM-590W-182M/144TB 590W": {
            "fabricante": "RONMA",
            "modelo": "RM-590W-182M/144TB",
            "potencia": 590,
            "eficiencia": "22,8%",
            "area": "2278×1134",
            "Imp": "13,06",
            "Vmp": "45,28",
            "Isc": "13,89",
            "Voc": "53,41",
        },
        "[620W] RM-620W-182R/132TB 620W": {
            "fabricante": "RONMA",
            "modelo": "RM-620W-182R/132TB",
            "potencia": 620,
            "eficiencia": "23,00%",
            "area": "2382x1134",
            "Imp": "14,99",
            "Vmp": "41,40",
            "Isc": "15,91",
            "Voc": "49,60",
        },
    },
    "TCL SOLAR": {
        "[610W] HSM-ND66-GR610 610W": {
            "fabricante": "TCL SOLAR",
            "modelo": "HSM-ND66-GR610",
            "potencia": 610,
            "eficiencia": "22,60%",
            "area": "2382x1134",
            "Imp": "15,03",
            "Vmp": "40,59",
            "Isc": "15,95",
            "Voc": "48,50",
        },
        "[615W] HSM-ND66-GR615 615W": {
            "fabricante": "TCL SOLAR",
            "modelo": "HSM-ND66-GR615",
            "potencia": 615,
            "eficiencia": "22,80%",
            "area": "2382x1134",
            "Imp": "15,08",
            "Vmp": "40,79",
            "Isc": "16,00",
            "Voc": "48,72",
        },
        "[620W] HSM-ND66-GR620 620W": {
            "fabricante": "TCL SOLAR",
            "modelo": "HSM-ND66-GR620",
            "potencia": 620,
            "eficiencia": "23,00%",
            "area": "2382x1134",
            "Imp": "15,13",
            "Vmp": "40,98",
            "Isc": "16,05",
            "Voc": "48,94",
        },
    },
    "TSUN": {
        "[600W] RIO600W-144BIF-2278 ": {
            "fabricante": "TSUN",
            "modelo": "RIO600W-144BIF-2278",
            "potencia": 600,
            "eficiencia": "23,2%",
            "area": "2278x1134",
            "Imp": "13,50",
            "Vmp": "44,45",
            "Isc": "13,50",
            "Voc": "53,30",
        }
    },
    "SOLAR N PLUS": {
        "[600W] SP-N16/156HG600W": {
            "fabricante": "SOLAR N PLUS",
            "modelo": "SP-N16/156HG600W",
            "potencia": 600,
            "eficiencia": "21,9%",
            "area": "2465x1134",
            "Imp": "12,56",
            "Vmp": "47,76",
            "Isc": "13,30",
            "Voc": "55,85",
        }
    }
}

INVERSORES = {
    "AUXSOL": {
        "[3kW] ASN-3SL": {
            "fabricante": "AUXSOL",
            "marca": "AUXSOL",
            "modelo": "ASN-3SL",
            "potencia": "3 kW",
            "faixa_cc": "40-550V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "18 A",
            "corrente_saida": "15,0 A",
            "registro": "003928/2025"
        },
        "[3,3kW] ASN-3.3SL": {
            "fabricante": "AUXSOL",
            "marca": "AUXSOL",
            "modelo": "ASN-3.3SL",
            "potencia": "3,3 kW",
            "faixa_cc": "40-550V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "18/18 A",
            "corrente_saida": "15,0 A",
            "registro": "003902/2025"
        },
        "[5kW] ASN-5SL-G2": {
            "fabricante": "AUXSOL",
            "marca": "AUXSOL",
            "modelo": "ASN-5SL-G2",
            "potencia": "5 kW",
            "faixa_cc": "40-550V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "18/18 A",
            "corrente_saida": "22,7 A",
            "registro": "003899/2025"
        },
        "[6kW] ASN-6SL-G2": {
            "fabricante": "AUXSOL",
            "marca": "AUXSOL",
            "modelo": "ASN-6SL-G2",
            "potencia": "6 kW",
            "faixa_cc": "40-550V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "18/18 A",
            "corrente_saida": "27,3 A",
            "registro": "003900/2025"
        },
        "[7,5kW] ASN-7.5SL": {
            "fabricante": "AUXSOL",
            "marca": "AUXSOL",
            "modelo": "ASN-7.5SL",
            "potencia": "7,5 kW",
            "faixa_cc": "80-600V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "27/16 A",
            "corrente_saida": "34 A",
            "registro": "018355/2024"
        },
        "[10kW] ASN-10SL": {
            "fabricante": "AUXSOL",
            "marca": "AUXSOL",
            "modelo": "ASN-10SL",
            "potencia": "10 kW",
            "faixa_cc": "40-600V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "32/16 A",
            "corrente_saida": "45,5 A",
            "registro": "018898/2024"
        },
        "[30kW] ASN-30TL-LV-G2": {
            "fabricante": "AUXSOL",
            "marca": "AUXSOL",
            "modelo": "ASN-30TL-LV-G2",
            "potencia": "30 kW",
            "faixa_cc": "180-800V",
            "faixa_ca": "220Vac",
            "corrente_cc": "48/48/48/48 A",
            "corrente_saida": "86,6 A",
            "registro": "015697/2024"
        },
    },
    "DEYE": {
        "[2,25kW] SUN-S225G4-EU-Q0": {
            "fabricante": "DEYE",
            "marca": "DEYE",
            "modelo": "SUN-S225G4-EU-Q0",
            "potencia": "2,25 kW",
            "faixa_cc": "20-60V",
            "faixa_ca": "180-280Vac",
            "corrente_cc": "16/16 A",
            "corrente_saida": "10,3 A",
            "registro": "012346/2025"
        },
        "[3kW] SUN-3K-G04P1-EU-AM1": {
            "fabricante": "DEYE",
            "marca": "DEYE",
            "modelo": "SUN-3K-G04P1-EU-AM1",
            "potencia": "3 kW",
            "faixa_cc": "80-550V",
            "faixa_ca": "220-230Vac",
            "corrente_cc": "20/20 A",
            "corrente_saida": "13,7 A",
            "registro": "016868/2024"
        },
    },
    "GOODWE": {
        "[3,3kW] GW3300-XS-30": {
            "fabricante": "GOODWE",
            "marca": "GOODWE",
            "modelo": "GW3300-XS-30",
            "potencia": "3,3 kW",
            "faixa_cc": "50-600V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "16/16 A",
            "corrente_saida": "15,0 A",
            "registro": "011052/2023"
        },
        "[5kW] GW5K-DNS-G40": {
            "fabricante": "GOODWE",
            "marca": "GOODWE",
            "modelo": "GW5K-DNS-G40",
            "potencia": "5 kW",
            "faixa_cc": "50-600V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "20/20 A",
            "corrente_saida": "22,8 A",
            "registro": "003256/2025"
        },
        "[23kW] GW23KLV-SDT-BR30": {
            "fabricante": "GOODWE",
            "marca": "GOODWE",
            "modelo": "GW23KLV-SDT-BR30",
            "potencia": "23 kW",
            "faixa_cc": "160-850V",
            "faixa_ca": "127/220 Vca (3F + N + T)",
            "corrente_cc": "20/20 A",
            "corrente_saida": "22,8 A",
            "registro": "016994/2024"
        },
    },
    "GROWATT": {
        "[2,25kW] NEO 2250M-X2": {
            "fabricante": "GROWATT",
            "marca": "GROWATT",
            "modelo": "NEO 2250M-X2",
            "potencia": "2,25 kW",
            "faixa_cc": "20-60V",
            "faixa_ca": "180-275Vac",
            "corrente_cc": "18/18 A",
            "corrente_saida": "10,23 A",
            "registro": "018187/2024"
        },
        "[3,3kW] MIC 3000TL-X2": {
            "fabricante": "GROWATT",
            "marca": "GROWATT",
            "modelo": "MIC 3000TL-X2",
            "potencia": "3,3 kW",
            "faixa_cc": "50-550V",
            "faixa_ca": "180-280Vac",
            "corrente_cc": "16/16 A",
            "corrente_saida": "14,3 A",
            "registro": "004395/2024"
        },
        "[10kW] MIN 10000TL-X2": {
            "fabricante": "GROWATT",
            "marca": "GROWATT",
            "modelo": "MIN 10000TL-X2",
            "potencia": "10 kW",
            "faixa_cc": "80-600V",
            "faixa_ca": "160-300Vac",
            "corrente_cc": "18/18/18 A",
            "corrente_saida": "45,5 A",
            "registro": "004497/2024"
        },
    },
    "HOYMILES": {
        "[1,875kW] HMS-1875DW-4T": {
            "fabricante": "HOYMILES",
            "marca": "HOYMILES",
            "modelo": "HMS-1875DW-4T",
            "potencia": "1,875 kW",
            "faixa_cc": "16-60V",
            "faixa_ca": "180-275Vac",
            "corrente_cc": "20/20 A",
            "corrente_saida": "8,52 A",
            "registro": "008997/2025"
        },
    },
    "HUAWEI": {
        "[5kW] SUN2000-5KTL-L1": {
            "fabricante": "HUAWEI",
            "marca": "HUAWEI",
            "modelo": "SUN2000-5KTL-L1",
            "potencia": "5 kW",
            "faixa_cc": "100-600V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "20/20 A",
            "corrente_saida": "25 A",
            "registro": "001173/2025"
        },
        "[6kW] SUN2000-6KTL-L1": {
            "fabricante": "HUAWEI",
            "marca": "HUAWEI",
            "modelo": "SUN2000-6KTL-L1",
            "potencia": "6 kW",
            "faixa_cc": "100-600V",
            "faixa_ca": "220-240Vac",
            "corrente_cc": "20/20 A",
            "corrente_saida": "27,3 A",
            "registro": "004091/2022"
        },
    },
    "SOFAR": {
        "[3,3kW] SOFAR 3.3KTL2-G3": {
            "fabricante": "SOFAR",
            "marca": "SOFAR",
            "modelo": "SOFAR 3.3KTL2-G3",
            "potencia": "3,3 kW",
            "faixa_cc": "70-550V",
            "faixa_ca": "180-276Vac",
            "corrente_cc": "15/15 A",
            "corrente_saida": "16 A",
            "registro": "000197/2024"
        },
        "[7,5kW] SOFAR 7.5KTLM-G3-BR": {
            "fabricante": "SOFAR",
            "marca": "SOFAR",
            "modelo": "SOFAR 7.5KTLM-G3-BR",
            "potencia": "7,5 kW",
            "faixa_cc": "90-600V",
            "faixa_ca": "180-276Vac",
            "corrente_cc": "25/25 A",
            "corrente_saida": "36,2 A",
            "registro": "003359/2020"
        },
    },
    "SUNGROW": {
        "[7,5kW] SUNGROW SG7.5RS-L": {
            "fabricante": "SUNGROW",
            "marca": "SUNGROW",
            "modelo": "SG7.5RS-L",
            "potencia": "7,5 kW",
            "faixa_cc": "40-600V",
            "faixa_ca": "154-276Vac",
            "corrente_cc": "16/32 A",
            "corrente_saida": "34,1 A",
            "registro": "018071/2024"
        },
    },
}

# ===== HISTÓRICOS =====
for key in ["hist_pot", "hist_area", "hist_ger", "hist_str", "hist_end", "hist_corr", "hist_conss", "hist_tel", "hist_doc"]:
    if key not in st.session_state:
        st.session_state[key] = []

def estimar_geracao_mensal(kwp, nivel="medio"):
    fatores = {
        "lucido": 115,
        "conservador": 130,
        "medio": 140,
        "otimista": 150
    }

    nivel = nivel.lower()

    if nivel not in fatores:
        nivel = "medio"

    fator = fatores[nivel]
    geracao = kwp * fator

    return geracao, fator

# ===== INTERFACE =====
st.title("⚡ Sistema de Energia Solar")

aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10, aba11 = st.tabs([
    "🔋 Potência",
    "📐 Área",
    "📈 Geração",
    "🔌 Strings",
    "📍 Endereço",
    "⚡ Disjuntor",
    "🏠 Consumo",
    "📞 Telefone",
    "🪪 CPF / CEP",
    "📦 Equipamentos",
    "🔄 Vírgula"
])
ct = 0

# ===== ABA 1 =====
with aba1:
    st.subheader("Potência")

    col1, col2 = st.columns(2)

    with col1:
        qtd1 = st.number_input("Módulos", step=1, key="qtd1")

    with col2:
        pot = input_float("Potência (W)", "pot")

    if st.button("Calcular Potência"):
        if pot is not None:
            r = calcular_potencia(qtd1, pot)
            txt = f"{r:.2f}".replace(".", ",") + " kWp"
            st.success(txt)
            st.code(txt)
            st.session_state.hist_pot.append(txt)

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_pot[-5:]):
        st.write(h)

# ===== ABA 2 =====
with aba2:
    st.subheader("Área")

    col1, col2, col3 = st.columns(3)

    with col1:
        ac = input_float("Comprimento (mm)", "ac")

    with col2:
        al = input_float("Largura (mm)", "al")

    with col3:
        qtt2 = st.number_input("Módulos", step=1, key="qtd2")

    if st.button("Calcular Área"):
        if ac is not None and al is not None:
            a, t = calcular_area(ac, al, qtt2)
            txt1 = f"{a:.2f}".replace(".", ",")
            txt2 = f"{t:.2f}".replace(".", ",")

            st.success(f"{txt1} m²")
            st.code(f"{txt1} m²")
            st.info(f"ÁREA MODIFICADA COMPLETA: {txt2} m²")
            st.code(f"{txt2} m²")

            st.session_state.hist_area.append(f"{txt1} | {txt2}")

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_area[-5:]):
        st.write(h)

# ===== ABA 3 =====
with aba3:
    st.subheader("Geração")

    kwp = input_float("kWp", "kwp")

    nivel_ui = st.selectbox("Nível", ["Lúcido", "Conservador", "Médio", "Otimista"])

    mapa_nivel = {
        "Lúcido": "lucido",
        "Conservador": "conservador",
        "Médio": "medio",
        "Otimista": "otimista"
    }

    if st.button("Calcular Geração"):
        if kwp is not None:

            nivel = mapa_nivel[nivel_ui]

            g, fator = estimar_geracao_mensal(kwp, nivel)

            txt = f"{g:.2f}".replace(".", ",") + " kWh/mês"

            st.success(txt)
            st.code(txt)

            info = f"{txt} (Fator: {fator} kWh/kWp)"
            st.session_state.hist_ger.append(info)

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_ger[-5:]):
        st.write(h)

# ===== ABA 4 =====
with aba4:
    st.subheader("Strings")

    col1, col2, col3 = st.columns(3)

    with col1:
        qtd3 = st.number_input("Módulos", step=1, key="qtd3")

    with col2:
        tensao = input_float("Tensão (V)", "ten")

    with col3:
        corrente = input_float("Corrente (A)", "cor")

    if st.button("Calcular String"):
        if tensao is not None and corrente is not None:
            txt = calcular_string(qtd3, tensao, corrente)
            st.success(txt)
            st.code(txt)
            st.session_state.hist_str.append(txt)

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_str[-5:]):
        st.write(h)

# ===== ABA 5 =====
with aba5:
    st.subheader("Endereço")

    texto = st.text_area("Cole o endereço aqui")

    if st.button("Formatar Endereço"):
        if texto.strip():
            res = formatar_endereco(texto)
            st.success(res)
            st.code(res)
            st.session_state.hist_end.append(res)

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_end[-5:]):
        st.write(h)

# ===== ABA 6 =====
with aba6:
    corrente_inv = input_float("Corrente do inversor (A)", "corrente_inv")

    if st.button("Dimensionar Disjuntor"):
        if corrente_inv:
            d, cp = disjuntor_por_corrente(corrente_inv)

            cabo = cabo_por_disjuntor(d)

            txt = f"{d} A | Cabo: {cabo} | Proj: {cp:.2f} A"

            st.write(f"Corrente projeto: {cp:.2f} A")

            st.success(f"Disjuntor: {d} A")
            st.code(f"{d} A")

            st.success(f"Cabo recomendado: {cabo}")
            st.code(f"{cabo}")

            st.session_state.hist_corr.append(txt)
        
    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_corr[-5:]):
        st.write(h)

# ===== ABA 7 =====
with aba7:
    st.subheader("Consumo Residencial")

    aparelhos = {
        "Geladeira":150,
        "Lâmpadas":10,
        "Chuveiro":5500,
        "TV":100,
        "Micro-ondas":1200
    }

    consumo_total = 0

    for nome, pot in aparelhos.items():
        st.markdown(f"### {nome} ({pot}W)")

        col1, col2, col3 = st.columns(3)

        qtd = col1.number_input("Qtd", min_value=0, key=f"q_{nome}")
        horas = col2.number_input("Horas/dia", min_value=0, step=1, key=f"h_{nome}")
        minutos = col3.number_input("Min/dia", min_value=0, step=1, key=f"m_{nome}")

        tempo_total = horas + (minutos / 60)

        consumo = (pot * tempo_total * qtd * 30) / 1000
        consumo_total += consumo

    if st.button("Calcular Consumo"):
        txt = f"{consumo_total:.2f}".replace(".", ",") + " kWh/mês"
        st.success(txt)
        st.code(txt)

        st.session_state.hist_conss.append(txt)

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_conss[-5:]):
        st.write(h)

# ===== ABA 8 =====
with aba8:
    st.subheader("Formatar Telefone")

    numero = st.text_input("Digite o número (ex: 32 9904-1697)")

    if st.button("Formatar Telefone"):
        res = formatar_telefone(numero)
        st.success(res)
        st.code(res)

        st.session_state.hist_tel.append(res)
        ct = ct + 1

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_tel[-5:]):
        st.write(f"Contato: {h}")

# ===== ABA 9 =====
with aba9:
    st.subheader("Limpar CPF e CEP")

    col1, col2 = st.columns(2)

    with col1:
        cep = st.text_input("Digite o CEP (ex: 36.500-000)")

    with col2:
        cpf = st.text_input("Digite o CPF (ex: 033.597.496-18)")

    if st.button("Limpar Dados"):
        def limpar(txt):
            return re.sub(r"\D", "", txt)

        cep_limpo = limpar(cep) if cep else ""
        cpf_limpo = limpar(cpf) if cpf else ""

        if cep:
            st.success(f"CEP: {cep_limpo}")
            st.code(cep_limpo)

        if cpf:
            st.success(f"CPF: {cpf_limpo}")
            st.code(cpf_limpo)

        if cep or cpf:
            st.session_state.hist_doc.append(f"CEP: {cep_limpo} | CPF: {cpf_limpo}")

    st.markdown("### 📜 Histórico")
    for h in reversed(st.session_state.hist_doc[-5:]):
        st.write(h)

# ===== ABA 10 =====
with aba10:
    st.subheader("📦 Equipamentos")

    col1, col2 = st.columns(2)

    # ===== PAINEL =====
    with col1:

        fabricante = st.selectbox(
            "Fabricante Painel",
            list(PAINEIS.keys())
        )

        modelo = st.selectbox(
            "Modelo Painel",
            list(PAINEIS[fabricante].keys())
        )

        painel = PAINEIS[fabricante][modelo]

        st.markdown("### 🔆 Dados do Módulo")

        st.write(f"**Fabricante:** {painel['fabricante']}")
        st.write(f"**Modelo:** {painel['modelo']}")
        st.write(f"**Potência:** {painel['potencia']} W")
        st.write(f"**Eficiência:** {painel['eficiencia']}")
        st.write(f"**Área:** {painel['area']} mmXmm")

        st.markdown("### ⚡ Características")

        st.write(f"**Imp:** {painel['Imp']} A")
        st.write(f"**Vmp:** {painel['Vmp']} V")
        st.write(f"**Isc:** {painel['Isc']} A")
        st.write(f"**Voc:** {painel['Voc']} V")

    # ===== INVERSOR =====
    with col2:

        fabricante_inv = st.selectbox(
            "Fabricante Inversor",
            list(INVERSORES.keys())
        )

        modelo_inv = st.selectbox(
            "Modelo Inversor",
            list(INVERSORES[fabricante_inv].keys())
        )

        inv = INVERSORES[fabricante_inv][modelo_inv]

        st.markdown("### ⚡ Dados do Inversor")

        st.write(f"**Fabricante:** {inv['fabricante']}")
        st.write(f"**Modelo:** {inv['modelo']}")
        st.write(f"**Potência:** {inv['potencia']}")

        st.markdown("### 🔌 Características")

        st.write(f"**Faixa CC:** {inv['faixa_cc']}")
        st.write(f"**Faixa CA:** {inv['faixa_ca']}")
        st.write(f"**Corrente Entrada CC:** {inv['corrente_cc']}")
        st.write(f"**Corrente Saída AC:** {inv['corrente_saida']}")
        st.write(f"**Registro INMETRO:** {inv['registro']}")

# ===== ABA 11 =====
with aba11:
    st.subheader("Substituir ponto por vírgula")

    numero = st.text_input(
        "Digite o número",
        placeholder="Ex: 9.45"
    )

    if st.button("Converter"):
        convertido = numero.replace(".", ",")

        st.success(convertido)
        st.code(convertido)

# ===== RODAPÉ =====
st.markdown("---")
st.markdown("Desenvolvido por Kluyvert ⚡ \n\n:yellow[Protótipo de sistema de energia solar para dimensionamento e cálculo de geração fotovoltaica:] \n\n **:green[KANERGY]**")
