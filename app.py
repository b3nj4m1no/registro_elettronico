from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, time, timedelta
from sqlalchemy.orm import validates
from sqlalchemy.exc import OperationalError, IntegrityError
import os
import time
import logging
from dotenv import load_dotenv

# Per debug
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('registro')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
login_manager = LoginManager(app)

load_dotenv()

# Connessione al database, prende i parametri dal docker
if os.environ.get('DB_HOST'):
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_HOST = os.environ.get('DB_HOST', 'db')
    DB_NAME = os.environ.get('DB_NAME', 'registro')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
        '?charset=utf8mb4&connect_timeout=30'
    )
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'registro.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.context_processor
def inject_today_date():
    return {'today': datetime.now()}

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

class Utente(BaseModel, UserMixin):
    __tablename__ = 'utenti'
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    ruolo = db.Column(db.String(20), nullable=False)
    
    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

class Classe(BaseModel):
    __tablename__ = 'classi'
    nome = db.Column(db.String(50), unique=True, nullable=False)
    studenti = db.relationship('Studente', back_populates='classe', lazy=True) 
    docenti = db.relationship('ClasseDocente', back_populates='classe')

class Studente(Utente):
    __tablename__ = 'studenti'
    id = db.Column(db.Integer, db.ForeignKey('utenti.id'), primary_key=True)
    classe_id = db.Column(db.Integer, db.ForeignKey('classi.id'))
    classe = db.relationship('Classe', back_populates='studenti') 

    voti = db.relationship('Voto', back_populates='studente')
    note = db.relationship('Nota', back_populates='studente')
    presenze = db.relationship('Presenza', back_populates='studente')

    # Per evitare che uno studente sia assegnato a più classi
    @property
    def classe_ref(self):
        return self.classe

class Docente(Utente):
    __tablename__ = 'docenti'
    id = db.Column(db.Integer, db.ForeignKey('utenti.id'), primary_key=True)
    classi = db.relationship('ClasseDocente', back_populates='docente')
    voti = db.relationship('Voto', back_populates='docente')
    note = db.relationship('Nota', back_populates='docente')
    presenze = db.relationship('Presenza', back_populates='docente')

class Vicepreside(Utente):
    __tablename__ = 'vicepresidi'
    id = db.Column(db.Integer, db.ForeignKey('utenti.id'), primary_key=True)

class ClasseDocente(BaseModel):
    __tablename__ = 'classi_docenti'
    classe_id = db.Column(db.Integer, db.ForeignKey('classi.id'))
    docente_id = db.Column(db.Integer, db.ForeignKey('docenti.id'))
    classe = db.relationship('Classe', back_populates='docenti')
    docente = db.relationship('Docente', back_populates='classi')

class Voto(BaseModel):
    __tablename__ = 'voti'
    valore = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    materia = db.Column(db.String(50), nullable=False)
    studente_id = db.Column(db.Integer, db.ForeignKey('studenti.id'))
    docente_id = db.Column(db.Integer, db.ForeignKey('docenti.id'))
    studente = db.relationship('Studente', back_populates='voti')
    docente = db.relationship('Docente', back_populates='voti')

class Nota(BaseModel):
    __tablename__ = 'note'
    tipo = db.Column(db.String(20), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    studente_id = db.Column(db.Integer, db.ForeignKey('studenti.id'))
    docente_id = db.Column(db.Integer, db.ForeignKey('docenti.id'))
    studente = db.relationship('Studente', back_populates='note')
    docente = db.relationship('Docente', back_populates='note')

class Presenza(BaseModel):
    __tablename__ = 'presenze'
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    # Presente, Assente, Ritardo
    tipo = db.Column(db.String(20), nullable=False)  
    giustificato = db.Column(db.Boolean, default=False)
    confermato = db.Column(db.Boolean, default=False)
    studente_id = db.Column(db.Integer, db.ForeignKey('studenti.id'))

    """
    nullable=True mi serve per quando assegno la sospensione
    """
    docente_id = db.Column(db.Integer, db.ForeignKey('docenti.id'), nullable=True)  

    # Vincolo per evitare duplicati giornalieri
    __table_args__ = (
        db.UniqueConstraint('data', 'studente_id', name='unique_daily_presence'),
    )
    
    studente = db.relationship('Studente', back_populates='presenze')
    docente = db.relationship('Docente', back_populates='presenze')

class Sospensione(BaseModel):
    __tablename__ = 'sospensioni'
    data_inizio = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    giorni = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    studente_id = db.Column(db.Integer, db.ForeignKey('studenti.id'))
    studente = db.relationship('Studente', backref='sospensioni') 

# Autenticazione
@login_manager.user_loader
def load_user(user_id):
    user = Utente.query.get(int(user_id))
    if user:
        if user.ruolo == 'studente':
            return Studente.query.get(user_id)
        elif user.ruolo == 'docente':
            return Docente.query.get(user_id)
        elif user.ruolo == 'vicepreside':
            return Vicepreside.query.get(user_id)
    return None

class AuthController:
    @staticmethod
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            logger.debug(f"Tentativo di login: {email}")
            
            user = Utente.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                logger.debug(f"User found: {user.email} ({user.ruolo})")
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                logger.debug("Credenziali non valide")
                flash('Credenziali non valide')
        return render_template('login.html')

    @staticmethod
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.ruolo == 'studente':
        studente = db.session.query(Studente).options(
            db.joinedload(Studente.classe)
        ).get(current_user.id)
        if not studente:
            studente = current_user

        oggi = datetime.now().date()
        sospensione = Sospensione.query.filter(
            Sospensione.studente_id == studente.id
        ).order_by(Sospensione.data_inizio.desc()).first()

        # Verifica se la sospensione è attiva
        sospensione_attiva = None
        if sospensione:
            data_fine = sospensione.data_inizio + timedelta(days=sospensione.giorni)
            if sospensione.data_inizio <= oggi < data_fine:
                sospensione_attiva = sospensione

        # Ottieni la presenza di oggi
        presenza_oggi = Presenza.query.filter_by(
            data=oggi,
            studente_id=studente.id
        ).first()
        
        # Calcola statistiche 
        presenze = Presenza.query.filter_by(studente_id=studente.id).all()
        presenze_totali = len(presenze)
        presenze_presenti = len([p for p in presenze if p.tipo == 'presente'])
        
        return render_template('studente_dashboard.html',
                              studente=studente,
                              presenza_oggi=presenza_oggi,
                              voti=Voto.query.filter_by(studente_id=studente.id).limit(5).all(),
                              note=Nota.query.filter_by(studente_id=studente.id).limit(5).all(),
                              presenze_totali=presenze_totali,
                              presenze_presenti=presenze_presenti,
                              sospensione=sospensione_attiva)
    
    elif current_user.ruolo == 'docente':
        docente = current_user
        classi = [cd.classe for cd in docente.classi]
        return render_template('docente_dashboard.html', 
                              docente=docente,
                              classi=classi)
    
    elif current_user.ruolo == 'vicepreside':
        ritardi = Presenza.query.filter_by(tipo='ritardo', confermato=False).all()
        classi = Classe.query.all()
        return render_template('vicepreside_dashboard.html', 
                              vicepreside=current_user,
                              ritardi=ritardi,
                              classi=classi)
    
    return redirect(url_for('login'))

# Docente
class DocenteController:
    @staticmethod
    @login_required
    def gestisci_presenze(classe_id):
        if current_user.ruolo != 'docente':
            return redirect(url_for('dashboard'))
        
        classe = Classe.query.get_or_404(classe_id)
        oggi = datetime.now().date()

        if request.method == 'POST':
            for studente in classe.studenti:
                # Controlla se lo studente è sospeso oggi
                sospeso = False
                for sosp in studente.sospensioni:
                    data_fine = sosp.data_inizio + timedelta(days=sosp.giorni)
                    if sosp.data_inizio <= oggi < data_fine:
                        sospeso = True
                        break

                if sospeso:
                    stato = 'assente'
                else:
                    stato = request.form.get(f'presenza_{studente.id}')

                if stato in ['presente', 'assente', 'ritardo']:
                    presenza = Presenza.query.filter_by(
                        data=oggi,
                        studente_id=studente.id
                    ).first()
                    if presenza:
                        presenza.tipo = stato
                        presenza.docente_id = current_user.id
                    else:
                        presenza = Presenza(
                            tipo=stato,
                            data=oggi,
                            studente_id=studente.id,
                            docente_id=current_user.id
                        )
                        db.session.add(presenza)
            db.session.commit()
            flash('Presenze registrate per oggi!', 'success')
            return redirect(url_for('dashboard'))
        
        # Carica le presenze di oggi
        presenze_oggi = {
            p.studente_id: p.tipo
            for p in Presenza.query.filter_by(data=oggi).all()
        }
        
        return render_template('gestione_presenze.html', 
                              classe=classe,
                              presenze_oggi=presenze_oggi,
                              oggi=oggi.strftime('%d/%m/%Y'))

    @staticmethod
    @login_required
    def inserisci_voto():
        if current_user.ruolo != 'docente':
            return redirect(url_for('dashboard'))

        # Trova tutti gli studenti di tutte le classi del docente
        classi_docente = ClasseDocente.query.filter_by(docente_id=current_user.id).all()
        studenti = []
        for cd in classi_docente:
            studenti += cd.classe.studenti

        if request.method == 'POST':
            studente_id = request.form.get('studente_id')
            valore = request.form.get('valore')
            try:
                valore = float(valore)
            except Exception:
                flash('Voto non valido', 'danger')
                return redirect(url_for('inserisci_voto'))

            voto = Voto(
                valore=valore,
                materia='Educazione Fisica',
                studente_id=studente_id,
                docente_id=current_user.id
            )
            db.session.add(voto)
            db.session.commit()
            flash('Voto inserito con successo!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('inserisci_voto.html', studenti=studenti)

    @staticmethod
    @login_required
    def inserisci_nota():
        if current_user.ruolo != 'docente':
            return redirect(url_for('dashboard'))

        # Trova tutti gli studenti di tutte le classi del docente
        classi_docente = ClasseDocente.query.filter_by(docente_id=current_user.id).all()
        studenti = []
        for cd in classi_docente:
            studenti += cd.classe.studenti

        if request.method == 'POST':
            studente_id = request.form.get('studente_id')
            tipo = request.form.get('tipo')
            descrizione = request.form.get('descrizione')
            if not tipo or not descrizione:
                flash('Compila tutti i campi', 'danger')
                return redirect(url_for('inserisci_nota'))

            nota = Nota(
                tipo=tipo,
                descrizione=descrizione,
                studente_id=studente_id,
                docente_id=current_user.id
            )
            db.session.add(nota)
            db.session.commit()
            flash('Nota inserita con successo!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('inserisci_nota.html', studenti=studenti)

# Vicepreside
class VicepresideController:
    @staticmethod
    @login_required
    def conferma_ritardi():
        if current_user.ruolo != 'vicepreside':
            return redirect(url_for('dashboard'))
        
        ritardi = Presenza.query.filter_by(tipo='ritardo', confermato=False).all()
        
        if request.method == 'POST':
            for ritardo in ritardi:
                if request.form.get(f'conferma_{ritardo.id}') == 'on':
                    ritardo.confermato = True
            db.session.commit()
            flash('Ritardi confermati!', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('conferma_ritardi.html', ritardi=ritardi)
    
    @staticmethod
    @login_required
    def sospensioni():
        if current_user.ruolo != 'vicepreside':
            return redirect(url_for('dashboard'))

        studenti = Studente.query.all()

        if request.method == 'POST':
            studente_id = request.form.get('studente_id')
            giorni = request.form.get('giorni')
            motivo = request.form.get('motivo')
            try:
                giorni = int(giorni)
            except Exception:
                flash('Numero di giorni non valido', 'danger')
                return redirect(url_for('sospensioni'))

            oggi = datetime.now().date()
            sosp = Sospensione(
                data_inizio=oggi,
                giorni=giorni,
                motivo=motivo,
                studente_id=studente_id
            )
            db.session.add(sosp)
            db.session.commit()

            # Sospensione
            for i in range(giorni):
                giorno = oggi + timedelta(days=i)
                presenza = Presenza.query.filter_by(
                    data=giorno,
                    studente_id=studente_id
                ).first()
                if presenza:
                    presenza.tipo = 'assente'
                    presenza.docente_id = None  # Nessun docente, è una sospensione
                else:
                    presenza = Presenza(
                        data=giorno,
                        tipo='assente',
                        studente_id=studente_id,
                        docente_id=None  # Nessun docente, è una sospensione
                    )
                    db.session.add(presenza)
                
            db.session.commit()

            flash('Sospensione registrata!', 'success')
            return redirect(url_for('sospensioni'))

        return render_template('sospensioni.html', studenti=studenti)

@app.route('/studente/note')
@login_required
def studente_note():
    if current_user.ruolo != 'studente':
        return redirect(url_for('dashboard'))
    
    # Carica le note dello studente con i dettagli del docente
    note = Nota.query.filter_by(studente_id=current_user.id)\
                    .options(db.joinedload(Nota.docente))\
                    .order_by(Nota.data.desc())\
                    .all()
    
    return render_template('studente_note.html', note=note)

# Route
app.add_url_rule('/login', view_func=AuthController.login, methods=['GET', 'POST'])
app.add_url_rule('/logout', view_func=AuthController.logout)
app.add_url_rule('/docente/presenze/<int:classe_id>', view_func=DocenteController.gestisci_presenze, methods=['GET', 'POST'])
app.add_url_rule('/vicepreside/ritardi', view_func=VicepresideController.conferma_ritardi, methods=['GET', 'POST'])
app.add_url_rule('/docente/inserisci_voto', view_func=DocenteController.inserisci_voto, methods=['GET', 'POST'])
app.add_url_rule('/docente/inserisci_nota', view_func=DocenteController.inserisci_nota, methods=['GET', 'POST'], endpoint='inserisci_nota')
app.add_url_rule('/vicepreside/sospensioni', view_func=VicepresideController.sospensioni, methods=['GET', 'POST'], endpoint='sospensioni')

# Inizializzo il db
def init_db():
    try:
        db.create_all()
        
        # Chiede vincolo unico
        if not os.environ.get('DB_HOST'):
            try:
                db.engine.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS unique_daily_presence "
                    "ON presenze (data, studente_id);"
                )
            except Exception as e:
                print(f"Errore creazione indice: {str(e)}")
        
        # Dati di test
        if not Utente.query.first():
            # Utenti
            studente = Utente(
                nome='Matthew',
                cognome='Gasparetti',
                email='studente@scuola.it',
                password='password',
                ruolo='studente'
            )
            db.session.add(studente)
            
            docente = Utente(
                nome='Cadel',
                cognome='Hi Ldo Patoh',
                email='docente@scuola.it',
                password='password',
                ruolo='docente'
            )
            db.session.add(docente)
            
            vicepreside = Utente(
                nome='Davide',
                cognome='Usberti',
                email='vicepreside@scuola.it',
                password='password',
                ruolo='vicepreside'
            )
            db.session.add(vicepreside)
            
            db.session.commit()
            
            # Classi
            classe1 = Classe(nome='3A Informatica')
            classe2 = Classe(nome='4A Informatica')
            classe3 = Classe(nome='5A Informatica')
            db.session.add_all([classe1, classe2, classe3])
            db.session.commit()
            
            stud = Studente(id=studente.id, classe_id=classe1.id)
            doc = Docente(id=docente.id)
            vp = Vicepreside(id=vicepreside.id)
            db.session.add_all([stud, doc, vp])
            
            cd1 = ClasseDocente(classe_id=classe1.id, docente_id=docente.id)
            cd2 = ClasseDocente(classe_id=classe2.id, docente_id=docente.id)
            cd3 = ClasseDocente(classe_id=classe3.id, docente_id=docente.id)
            db.session.add_all([cd1, cd2, cd3])
            
            # Voti
            v1 = Voto(
                valore=8.5,
                materia='Informatica',
                studente_id=studente.id,
                docente_id=docente.id
            )
            v2 = Voto(
                valore=7.0,
                materia='Storia',
                studente_id=studente.id,
                docente_id=docente.id
            )
            v3 = Voto(
                valore=2.0,
                materia='Matematica',
                studente_id=studente.id,
                docente_id=docente.id
            )
            db.session.add_all([v1, v2, v3])
            
            # Note
            n1 = Nota(
                tipo='Comportamento',
                descrizione='Arriva perennemente in ritardo',
                studente_id=studente.id,
                docente_id=docente.id
            )
            n2 = Nota(
                tipo='Merito',
                descrizione='Primo a bucare webuser',
                studente_id=studente.id,
                docente_id=docente.id
            )
            db.session.add_all([n1, n2])
            
            # Presenze
            oggi = datetime.now().date()
            p1 = Presenza(
                data=oggi,
                tipo='presente',
                studente_id=studente.id,
                docente_id=docente.id,
                confermato=True
            )
            p2 = Presenza(
                data=oggi - timedelta(days=1),
                tipo='ritardo',
                studente_id=studente.id,
                docente_id=docente.id
            )
            p3 = Presenza(
                data=oggi - timedelta(days=2),
                tipo='assente',
                studente_id=studente.id,
                docente_id=docente.id,
                confermato=True
            )
            db.session.add_all([p1, p2, p3])
            
            db.session.commit()
            logger.info("Dati di test inseriti con successo")
            
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Errore di integrità: {str(e)}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Errore durante l'inizializzazione: {str(e)}")

# Sostituisci la funzione create_tables_with_retry con:
def create_tables_with_retry():
    max_retries = 5  # Aumenta a 30 tentativi
    retry_delay = 1  # 10 secondi tra i tentativi
    
    for attempt in range(max_retries):
        try:
            db.create_all()
            
            # Verifica se il database è vuoto
            if not Utente.query.first():
                init_db()
                
            print("Database inizializzato con successo!")
            return
        except OperationalError as e:
            print(f"Tentativo {attempt+1}/{max_retries}: Errore connessione DB - {str(e)}")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"Tentativo {attempt+1}/{max_retries}: Errore - {str(e)}")
            time.sleep(retry_delay)
    
    print("ERRORE CRITICO: Impossibile inizializzare il database")
    exit(1)

if __name__ == '__main__':
    with app.app_context():
        create_tables_with_retry()
    app.run(host='0.0.0.0', port=5000, debug=True)