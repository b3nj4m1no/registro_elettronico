# Registro Elettronico Scolastico

Un registro elettronico per la gestione di studenti, docenti, vicepreside e presenze, sviluppato con Python (Flask), MySQL e frontend responsive.

---

## Sommario

- [Descrizione](#descrizione)
- [Funzionalità](#funzionalità)
- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Avvio del progetto](#avvio-del-progetto)
- [Struttura del progetto](#struttura-del-progetto)
- [Ruoli e Permessi](#ruoli-e-permessi)
- [Database](#database)
- [Sicurezza](#sicurezza)
- [Contributi](#contributi)
- [Licenza](#licenza)

---

## Descrizione

Il Registro Elettronico Scolastico è una piattaforma web che consente la gestione digitale di voti, presenze, ritardi, note disciplinari e sospensioni. È pensato per essere utilizzato da scuole di ogni ordine e grado, con interfacce dedicate per studenti, docenti e vicepreside.

---

## Funzionalità

- **Login** per tutti i ruoli (studente, docente, vicepreside)
- **Gestione presenze**: segnalazione di presenza, assenza, ritardo
- **Gestione voti**: inserimento e visualizzazione dei voti per materia
- **Gestione note disciplinari**: inserimento e consultazione note
- **Gestione sospensioni**: il vicepreside può sospendere studenti, con motivazione e durata
- **Dashboard personalizzate** per ogni ruolo
- **Visualizzazione statistiche** (medie voti, presenze, assenze)
- **Responsive design** per utilizzo da desktop e mobile

---

## Requisiti

- Python 3.8+
- MySQL 5.7+ o MariaDB
- Docker (opzionale, consigliato per sviluppo rapido)
- Librerie Python: vedi `requirements.txt`

---

## Installazione

### 1. Clona il repository

```bash
git clone https://github.com/b3nj4m1no/registro_elettronico.git
cd registro_elettronico
```

### 2. Crea e configura il database

- Crea un database MySQL chiamato `registro`
- Esegui lo script `init.sql` per creare le tabelle e i dati di test:

```bash
mysql -u root -p registro < init.sql
```

### 3. Installa le dipendenze Python

```bash
pip install -r requirements.txt
```

### 4. Configura le variabili d’ambiente

Crea un file `.env` con le seguenti variabili:

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=una-chiave-segreta
DATABASE_URL=mysql+pymysql://root:password@localhost/registro
```

---

## Avvio del progetto

```bash
flask run
```

Oppure con Docker:

```bash
docker-compose up --build
```

---

## Struttura del progetto

```
registro_elettronico/
│
├── templates/            # Templates HTML Jinja2
├── app.py                # Applicazione Flask principale
├── docker-compose.yml    # Composer per Docker
├── Dockerfile            # Definizione del Docker
├── requirements.txt      # Dipendenze Python
├── init.sql              # Script di inizializzazione database
└── README.md             # Documentazione
```

---

## Ruoli e Permessi

- **Studente**: Visualizza voti, presenze, note, sospensioni
- **Docente**: Inserisce voti, presenze, note per le proprie classi
- **Vicepreside**: Gestisce sospensioni, conferma ritardi, visualizza statistiche globali

---

## Database

- **Tabelle principali**: utenti, studenti, docenti, vicepresidi, classi, presenze, voti, note, sospensioni

---

## Sicurezza

- Sessioni sicure Flask-Login
- Protezione CSRF nei form
- Validazione dati lato server

---

## Contributi

Contributi, segnalazioni di bug e suggerimenti sono benvenuti!  
Apri una issue o una pull request su GitHub.

---

## Licenza

Questo progetto è distribuito sotto licenza MIT.

---
