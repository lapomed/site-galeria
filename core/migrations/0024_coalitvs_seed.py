"""Popula a rede COALITVS com os 53 pesquisadores fundadores."""
from django.db import migrations
from django.utils.text import slugify


GROUPS = [
    {"slug": "internacional", "name": "Internacional", "short_label": "INT",
     "description": "Pesquisadores parceiros em universidades estrangeiras",
     "color": "#f0c300", "order": 1},
    {"slug": "nacional", "name": "Nacional", "short_label": "NAC",
     "description": "USP e demais universidades brasileiras",
     "color": "#5b9bd5", "order": 2},
]


# (name, role, institution, city, country, country_code, lat, lng, group_slug)
MEMBERS = [
    # ===== INTERNACIONAIS =====
    ("Ian Hodder", "Professor", "Stanford University", "Stanford", "Estados Unidos", "USA", 37.4275, -122.1697, "internacional"),
    ("Justin Leidwanger", "Professor", "Stanford University", "Stanford", "Estados Unidos", "USA", 37.4275, -122.1697, "internacional"),
    ("Andrea Berlin", "Professor", "Boston University", "Boston", "Estados Unidos", "USA", 42.3505, -71.1054, "internacional"),
    ("C Michael Barton", "Professor", "Arizona State University", "Tempe", "Estados Unidos", "USA", 33.4242, -111.9281, "internacional"),
    ("Jaś Elsner", "Professor", "University of Oxford", "Oxford", "Reino Unido", "GBR", 51.7548, -1.2544, "internacional"),
    ("Mark Altaweel", "Professor", "University College London", "Londres", "Reino Unido", "GBR", 51.5246, -0.1340, "internacional"),
    ("Carlos Augusto Ribeiro Machado", "Professor", "University of St Andrews", "St Andrews", "Reino Unido", "GBR", 56.3398, -2.7967, "internacional"),
    ("Gregg E. Gardner", "Professor", "University of British Columbia", "Vancouver", "Canadá", "CAN", 49.2606, -123.2460, "internacional"),
    ("Achim Litchenberger", "Professor", "Münster University", "Münster", "Alemanha", "DEU", 51.9636, 7.6133, "internacional"),
    ("Florian Janoscha Kreppner", "Professor", "Münster University", "Münster", "Alemanha", "DEU", 51.9636, 7.6133, "internacional"),
    ("Naoise Mac Sweeney", "Professor", "University of Vienna", "Viena", "Áustria", "AUT", 48.2131, 16.3596, "internacional"),
    ("Matteo Bigongiari", "Professor", "University of Florence", "Florença", "Itália", "ITA", 43.7710, 11.2480, "internacional"),
    ("Aris Ymir Politopoulos", "Professor", "Leiden University", "Leiden", "Países Baixos", "NLD", 52.1571, 4.4858, "internacional"),
    ("Marta Lorenzon", "Professor", "University of Helsinki", "Helsinque", "Finlândia", "FIN", 60.1701, 24.9527, "internacional"),
    ("Hannah M. Moots", "Professor", "Stockholm University", "Estocolmo", "Suécia", "SWE", 59.3631, 18.0573, "internacional"),
    ("Margozata Kajzer", "Pesquisadora", "Polish Academy of Sciences", "Varsóvia", "Polônia", "POL", 52.2389, 21.0166, "internacional"),
    ("Oren Tal", "Professor", "Tel Aviv University", "Tel Aviv", "Israel", "ISR", 32.1135, 34.8044, "internacional"),
    ("Alexander Fantalkin", "Professor", "Tel Aviv University", "Tel Aviv", "Israel", "ISR", 32.1135, 34.8044, "internacional"),
    ("Mordechai Aviam", "Professor", "Kinneret Academic College", "Tzemach", "Israel", "ISR", 32.7195, 35.5589, "internacional"),
    ("Carlos Jorge Soares Fabião", "Professor", "Universidade de Lisboa", "Lisboa", "Portugal", "PRT", 38.7530, -9.1573, "internacional"),
    ("Jose Remesal Rodriguez", "Professor", "Universitat de Barcelona", "Barcelona", "Espanha", "ESP", 41.3866, 2.1644, "internacional"),
    ("Jérémie Schiettecatte", "Pesquisador", "CNRS-Paris", "Paris", "França", "FRA", 48.8566, 2.3522, "internacional"),
    ("Benjamin Isakhan", "Professor", "Deakin University", "Geelong", "Austrália", "AUS", -38.1989, 144.3038, "internacional"),
    ("Rodrigo Laham Cohen", "Professor", "Universidad de Buenos Aires", "Buenos Aires", "Argentina", "ARG", -34.6037, -58.3816, "internacional"),
    ("Roberto R. Rodríguez", "Professor", "Universidad Nacional de la Patagonia", "Comodoro Rivadavia", "Argentina", "ARG", -45.8669, -67.4847, "internacional"),
    ("Bülent Arikan", "Professor", "Istanbul Technical University", "Istambul", "Turquia", "TUR", 41.1058, 29.0237, "internacional"),
    ("Ergün Lafli", "Professor", "Dokuz Eyül University", "Esmirna", "Turquia", "TUR", 38.4253, 27.1411, "internacional"),
    ("Hanan Charaf", "Professor", "Lebanese University", "Beirute", "Líbano", "LBN", 33.8869, 35.5131, "internacional"),

    # ===== NACIONAIS (USP   universidades brasileiras) =====
    ("Marcio Teixeira-Bastos", "Pesquisador Responsável", "DA, FFLCH, USP", "São Paulo", "Brasil", "BRA", -23.5594, -46.7298, "nacional"),
    ("Paulo Martins", "Professor", "DLCV, FFLCH, USP", "São Paulo", "Brasil", "BRA", -23.5594, -46.7298, "nacional"),
    ("Marcelo Knörich Zuffo", "Professor", "POLI, USP", "São Paulo", "Brasil", "BRA", -23.5557, -46.7320, "nacional"),
    ("João Felipe Ferreira Gonçalves", "Professor", "DA, FFLCH, USP", "São Paulo", "Brasil", "BRA", -23.5594, -46.7298, "nacional"),
    ("Suzana Chwarts", "Professora", "DLO/CEJ-USP, FFLCH", "São Paulo", "Brasil", "BRA", -23.5594, -46.7298, "nacional"),
    ("Júlio César Magalhães de Oliveira", "Professor", "DH, FFLCH, USP", "São Paulo", "Brasil", "BRA", -23.5594, -46.7298, "nacional"),
    ("Beatriz Piccolotto Siqueira Bueno", "Professora", "FAU, USP", "São Paulo", "Brasil", "BRA", -23.5614, -46.7268, "nacional"),
    ("Eliane Aparecida Del Lama", "Professora", "IGC-USP", "São Paulo", "Brasil", "BRA", -23.5648, -46.7283, "nacional"),
    ("Lucelene Martins", "Pesquisadora", "IGC-USP", "São Paulo", "Brasil", "BRA", -23.5648, -46.7283, "nacional"),
    ("Márcia de Almeida Rizzutto", "Professora", "IF-USP", "São Paulo", "Brasil", "BRA", -23.5610, -46.7320, "nacional"),
    ("Ximena Suarez Villagran", "Professora", "MAE-USP", "São Paulo", "Brasil", "BRA", -23.5615, -46.7273, "nacional"),
    ("Maria Isabel D'Agostino Fleming", "Professora", "MAE-USP", "São Paulo", "Brasil", "BRA", -23.5615, -46.7273, "nacional"),
    ("Vagner Carvalheiro Porto", "Professor", "MAE-USP", "São Paulo", "Brasil", "BRA", -23.5615, -46.7273, "nacional"),
    ("Juliana Figueira da Hora", "Pesquisadora", "MAE-USP", "São Paulo", "Brasil", "BRA", -23.5615, -46.7273, "nacional"),
    ("Pedro Paulo Funari", "Professor", "UNICAMP", "Campinas", "Brasil", "BRA", -22.8175, -47.0697, "nacional"),
    ("Ivan Esperança Rocha", "Professor", "UNESP-Assis", "Assis", "Brasil", "BRA", -22.6541, -50.4119, "nacional"),
    ("Margarida Maria de Carvalho", "Professora", "UNESP-Franca", "Franca", "Brasil", "BRA", -20.5474, -47.4011, "nacional"),
    ("Pedro Merlussi", "Professor", "PUC-RJ", "Rio de Janeiro", "Brasil", "BRA", -22.9789, -43.2341, "nacional"),
    ("Filipe Noé da Silva", "Professor", "UDESC", "Florianópolis", "Brasil", "BRA", -27.6052, -48.5249, "nacional"),
    ("Flávio de Leão Bastos Pereira", "Professor", "MACKENZIE", "São Paulo", "Brasil", "BRA", -23.5474, -46.6519, "nacional"),
    ("Claudio Walter Gomez Duarte", "Professor", "UNIMES", "Santos", "Brasil", "BRA", -23.9608, -46.3331, "nacional"),
    ("Márcia Severina Vasques", "Professora", "UFRN", "Natal", "Brasil", "BRA", -5.8442, -35.2031, "nacional"),
    ("Gilvan Ventura da Silva", "Professor", "UFES", "Vitória", "Brasil", "BRA", -20.2750, -40.3034, "nacional"),
    ("Lucio Menezes Ferreira", "Professor", "UFPEL", "Pelotas", "Brasil", "BRA", -31.7686, -52.3370, "nacional"),
    ("Kátia Maria Paim Pozzer", "Professora", "UFRGS", "Porto Alegre", "Brasil", "BRA", -30.0331, -51.2186, "nacional"),
]


def seed(apps, schema_editor):
    Group = apps.get_model("core", "CoalitvsGroup")
    Member = apps.get_model("core", "CoalitvsMember")

    group_map = {}
    for g in GROUPS:
        obj, _ = Group.objects.get_or_create(
            slug=g["slug"],
            defaults={
                "name": g["name"],
                "short_label": g["short_label"],
                "description": g["description"],
                "color": g["color"],
                "order": g["order"],
            },
        )
        group_map[g["slug"]] = obj

    used_slugs = set()
    for index, (name, role, institution, city, country, code, lat, lng, group_slug) in enumerate(MEMBERS):
        base = slugify(name)[:200] or f"membro-{index}"
        slug = base
        i = 2
        while slug in used_slugs or Member.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        used_slugs.add(slug)

        member, created = Member.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "role": role,
                "institution": institution,
                "city": city,
                "country": country,
                "country_code": code,
                "latitude": lat,
                "longitude": lng,
                "order": index,
                "active": True,
            },
        )
        if created:
            member.groups.add(group_map[group_slug])


def unseed(apps, schema_editor):
    Group = apps.get_model("core", "CoalitvsGroup")
    Member = apps.get_model("core", "CoalitvsMember")
    Member.objects.all().delete()
    Group.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_coalitvs_models"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
