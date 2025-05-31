-- Rimuovo tabelle esistenti, mi serve solo per test
DROP TABLE IF EXISTS presenze;
DROP TABLE IF EXISTS note;
DROP TABLE IF EXISTS voti;
DROP TABLE IF EXISTS classi_docenti;
DROP TABLE IF EXISTS studenti;
DROP TABLE IF EXISTS docenti;
DROP TABLE IF EXISTS vicepresidi;
DROP TABLE IF EXISTS classi;
DROP TABLE IF EXISTS utenti;

-- Tabelle principali
CREATE TABLE utenti (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    ruolo VARCHAR(20) NOT NULL
);

CREATE TABLE classi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE studenti (
    id INT PRIMARY KEY,
    classe_id INT,
    FOREIGN KEY (id) REFERENCES utenti(id),
    FOREIGN KEY (classe_id) REFERENCES classi(id)
);

CREATE TABLE docenti (
    id INT PRIMARY KEY,
    FOREIGN KEY (id) REFERENCES utenti(id)
);

CREATE TABLE vicepresidi (
    id INT PRIMARY KEY,
    FOREIGN KEY (id) REFERENCES utenti(id)
);

CREATE TABLE classi_docenti (
    id INT AUTO_INCREMENT PRIMARY KEY,
    classe_id INT NOT NULL,
    docente_id INT NOT NULL,
    FOREIGN KEY (classe_id) REFERENCES classi(id),
    FOREIGN KEY (docente_id) REFERENCES docenti(id)
);

CREATE TABLE voti (
    id INT AUTO_INCREMENT PRIMARY KEY,
    valore FLOAT NOT NULL,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    materia VARCHAR(50) NOT NULL,
    studente_id INT NOT NULL,
    docente_id INT NOT NULL,
    FOREIGN KEY (studente_id) REFERENCES studenti(id),
    FOREIGN KEY (docente_id) REFERENCES docenti(id)
);

CREATE TABLE note (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,
    descrizione TEXT NOT NULL,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    studente_id INT NOT NULL,
    docente_id INT NOT NULL,
    FOREIGN KEY (studente_id) REFERENCES studenti(id),
    FOREIGN KEY (docente_id) REFERENCES docenti(id)
);

CREATE TABLE presenze (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    giustificato BOOLEAN DEFAULT FALSE,
    confermato BOOLEAN DEFAULT FALSE,
    studente_id INT NOT NULL,
    docente_id INT NULL,
    FOREIGN KEY (studente_id) REFERENCES studenti(id),
    FOREIGN KEY (docente_id) REFERENCES docenti(id),
    UNIQUE KEY unique_daily_presence (data, studente_id)  
);

-- Dati di test
INSERT INTO utenti (nome, cognome, email, password, ruolo) VALUES
('Matthew', 'Gasparetti', 'studente@scuola.it', 'password', 'studente'),
('Cadel', 'Hi Ldo Patoh', 'docente@scuola.it', 'password', 'docente'),
('Davide', 'Usberti', 'vicepreside@scuola.it', 'password', 'vicepreside');

-- Classi 
INSERT INTO classi (nome) VALUES 
('3A Informatica'),
('4A Informatica'),
('5A Informatica');

-- Assegna
INSERT INTO studenti (id, classe_id) VALUES (1, 1);
INSERT INTO docenti (id) VALUES (2);
INSERT INTO vicepresidi (id) VALUES (3);

-- Assegna i docenti alla classi
INSERT INTO classi_docenti (classe_id, docente_id) VALUES 
(1, 2),
(2, 2),
(3, 2);

-- Voti
INSERT INTO voti (valore, materia, studente_id, docente_id) VALUES
(8.5, 'Informatica', 1, 2),
(7.0, 'Storia', 1, 2),
(2.0, 'Matematica', 1, 2); 

-- Note
INSERT INTO note (tipo, descrizione, studente_id, docente_id) VALUES
('Comportamento', 'Arriva perennemente in ritardo', 1, 2),
('Merito', 'Primo a bucare webuser', 1, 2);

-- Presenze
INSERT INTO presenze (data, tipo, studente_id, docente_id, confermato) VALUES
(CURDATE(), 'presente', 1, 2, TRUE),
(CURDATE() - INTERVAL 1 DAY, 'ritardo', 1, 2, FALSE),
(CURDATE() - INTERVAL 2 DAY, 'assente', 1, 2, TRUE);

SELECT 'Utenti' AS Tabella;
SELECT * FROM utenti;

SELECT 'Classi' AS Tabella;
SELECT * FROM classi;

SELECT 'Studenti' AS Tabella;
SELECT s.id, u.nome, u.cognome, c.nome AS classe 
FROM studenti s
JOIN utenti u ON s.id = u.id
JOIN classi c ON s.classe_id = c.id;

SELECT 'Docenti' AS Tabella;
SELECT d.id, u.nome, u.cognome 
FROM docenti d
JOIN utenti u ON d.id = u.id;

SELECT 'Classi-Docenti' AS Tabella;
SELECT cd.id, c.nome AS classe, u.nome, u.cognome 
FROM classi_docenti cd
JOIN classi c ON cd.classe_id = c.id
JOIN docenti d ON cd.docente_id = d.id
JOIN utenti u ON d.id = u.id;

SELECT 'Voti' AS Tabella;
SELECT v.id, v.valore, v.materia, v.data, 
       CONCAT(u_s.nome, ' ', u_s.cognome) AS studente,
       CONCAT(u_d.nome, ' ', u_d.cognome) AS docente
FROM voti v
JOIN studenti s ON v.studente_id = s.id
JOIN docenti d ON v.docente_id = d.id
JOIN utenti u_s ON s.id = u_s.id
JOIN utenti u_d ON d.id = u_d.id;

SELECT 'Note' AS Tabella;
SELECT n.id, n.tipo, n.descrizione, n.data,
       CONCAT(u_s.nome, ' ', u_s.cognome) AS studente,
       CONCAT(u_d.nome, ' ', u_d.cognome) AS docente
FROM note n
JOIN studenti s ON n.studente_id = s.id
JOIN docenti d ON n.docente_id = d.id
JOIN utenti u_s ON s.id = u_s.id
JOIN utenti u_d ON d.id = u_d.id;

SELECT 'Presenze' AS Tabella;
SELECT p.id, p.data, p.tipo, p.giustificato, p.confermato,
       CONCAT(u.nome, ' ', u.cognome) AS studente,
       CONCAT(u_d.nome, ' ', u_d.cognome) AS docente
FROM presenze p
JOIN studenti s ON p.studente_id = s.id
JOIN docenti d ON p.docente_id = d.id
JOIN utenti u ON s.id = u.id
JOIN utenti u_d ON d.id = u_d.id;