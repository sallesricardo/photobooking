from decimal import Decimal
from sqlalchemy import select
from app.db.session import Base, SessionLocal, engine
from app.models.package import SessionPackage
from app.models.session import PhotographySession

DATA = [
    (
        "feminino",
        "Ensaio Feminino / Aniversário",
        "Ensaios individuais para celebrar uma fase, aniversário ou momento especial.",
        [("Essencial", "Ensaio de 60 minutos com seleção de fotos.", Decimal("450.00"), 60),
         ("Premium", "Ensaio de 90 minutos com uma experiência mais completa.", Decimal("750.00"), 90)]
    ), (
        "familia",
        "Ensaio Família",
        "Registros naturais e afetivos para famílias e seus momentos especiais.",
        [("Essencial", "Ensaio de 60 minutos para a família.", Decimal("550.00"), 60),
         ("Premium", "Ensaio de 90 minutos com experiência completa.", Decimal("850.00"), 90)]
    ), (
        "corporativo",
        "Corporativo",
        "Retratos profissionais para equipes, profissionais e marcas.",
        [("Individual", "Retrato profissional individual.", Decimal("350.00"), 45),
         ("Equipe", "Sessão para equipes e empresas.", Decimal("900.00"), 120)]
    ), (
        "natal",
        "Natal",
        "Ensaios temáticos de Natal para famílias e crianças.",
        [("Mini Natal", "Sessão temática de 30 minutos.", Decimal("400.00"), 30),
         ("Natal Premium", "Sessão completa de 60 minutos.", Decimal("650.00"), 60)]
    )
]


def seed():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(PhotographySession.id).limit(1)) is not None:
            print("Seed já executado.")
            return
        for slug, name, description, packages in DATA:
            s = PhotographySession(slug=slug, name=name, description=description)
            for i, (n, d, p, dur) in enumerate(packages):
                s.packages.append(SessionPackage(name=n, description=d, price=p, duration_minutes=dur, display_order=i))
            db.add(s)
        db.commit()
        print("Catálogo inicial criado.")


if __name__ == "__main__":
    seed()
