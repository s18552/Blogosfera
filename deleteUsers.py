from app import app, db, User

# Utwórz kontekst aplikacji
with app.app_context():
    # Usuń wszystkich użytkowników
    User.query.delete()

    # Zatwierdź zmiany w bazie danych
    db.session.commit()

    # Pobierz liczbę użytkowników
    user_count = User.query.count()

    # Wyświetl liczbę użytkowników
    print("Liczba użytkowników:", user_count)
    
