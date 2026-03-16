DROP TABLE IF EXISTS torneo_partidos;
DROP TABLE IF EXISTS torneos;
DROP TABLE IF EXISTS estadisticas_partido;
DROP TABLE IF EXISTS partidos;
DROP TABLE IF EXISTS jugadores;
DROP TABLE IF EXISTS usuarios;

-- 2. TABLA DE USUARIOS
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,                  -- Identificador único autoincremental
    username VARCHAR(50) UNIQUE NOT NULL,   -- Nombre de usuario único (ej: "rafa_nadal")
    email VARCHAR(100) UNIQUE NOT NULL,     -- Email único
    password_hash VARCHAR(255) NOT NULL,    -- Contraseña encriptada (nunca texto plano)
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    nacionalidad VARCHAR(50),               -- Ej: "España", "USA"
    genero VARCHAR(20),                     -- Ej: "M", "F", "Otro"
    foto_perfil_url VARCHAR(255),           -- Ruta a la imagen (ej: "/uploads/avatar1.jpg")
    activo BOOLEAN DEFAULT TRUE,            -- Borrado lógico (TRUE = activo, FALSE = dado de baja)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Fecha de registro automática
);

-- 3. TABLA DE JUGADORES
CREATE TABLE jugadores (
    id SERIAL PRIMARY KEY,
    
    -- Datos Personales
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    nacionalidad CHAR(3),                   -- Código ISO (ej: ESP, FRA, USA)
    altura_cm INT,                          -- Altura en centímetros
    brazo_bueno CHAR(1) CHECK (brazo_bueno IN ('R', 'L')), -- R = Right (Diestro), L = Left (Zurdo)
    
    -- Relación con Usuario
    -- Si id_creador es NULL, se considera un jugador del SISTEMA (Bot/Default)
    -- ON DELETE CASCADE: Si se borra el usuario, se borran sus jugadores creados.
    id_creador INT REFERENCES usuarios(id) ON DELETE CASCADE,
    
    -- ATRIBUTOS DE TENIS (Escala 1-100)
    -- Usamos CHECK para garantizar que nadie meta un 101 o un -1.
    attr_primer_saque INT CHECK (attr_primer_saque BETWEEN 1 AND 100),
    attr_segundo_saque INT CHECK (attr_segundo_saque BETWEEN 1 AND 100),
    attr_resto INT CHECK (attr_resto BETWEEN 1 AND 100),
    
    attr_derecha INT CHECK (attr_derecha BETWEEN 1 AND 100),
    attr_reves INT CHECK (attr_reves BETWEEN 1 AND 100),
    
    attr_movilidad INT CHECK (attr_movilidad BETWEEN 1 AND 100),
    attr_consistencia INT CHECK (attr_consistencia BETWEEN 1 AND 100),
    attr_clutch INT CHECK (attr_clutch BETWEEN 1 AND 100), -- Mente fría
    attr_fisico INT CHECK (attr_fisico BETWEEN 1 AND 100),
    
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE partidos (
    id SERIAL PRIMARY KEY,
    
    -- Quién jugó
    id_jugador_1 INT REFERENCES jugadores(id) ON DELETE CASCADE,
    id_jugador_2 INT REFERENCES jugadores(id) ON DELETE CASCADE,
    id_ganador INT REFERENCES jugadores(id) ON DELETE CASCADE, -- Importante para saber quién ganó rápido
    id_usuario_creador INT REFERENCES usuarios(id) ON DELETE SET NULL, -- Quién creó el partido (puede ser NULL si fue el sistema)
    -- Detalles del Partido
    marcador_final VARCHAR(50) NOT NULL, -- Ej: "6-4, 6-2, 7-6"
    duracion_minutos INT,                -- Ej: 145 (minutos)
    fecha_jugado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Configuración
    superficie VARCHAR(20) CHECK (superficie IN ('Dura', 'Arcilla', 'Hierba')),
    formato_sets INT CHECK (formato_sets IN (1, 3, 5)), -- Solo permite partidos a 1, 3 o 5 sets
    tiebreak_ultimo_set BOOLEAN DEFAULT TRUE, -- TRUE = hay tiebreak, FALSE = hay que ganar por 2 juegos
    
    activo BOOLEAN DEFAULT TRUE -- Por si quieres "borrar" un partido sin eliminarlo de la BD
);

-- IMPORTANTE: Se generarán 2 filas por cada partido (una por jugador)
CREATE TABLE estadisticas_partido (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones (Claves Foráneas)
    id_partido INT REFERENCES partidos(id) ON DELETE CASCADE, -- Si se borra el partido, se borran sus stats
    id_jugador INT REFERENCES jugadores(id) ON DELETE CASCADE, -- De quién son estos números
    id_usuario INT REFERENCES usuarios(id) ON DELETE SET NULL, -- Qué usuario generó estas estadísticas
    
    -- BLOQUE A: SERVICIO (SAQUE)
    aces INT DEFAULT 0,
    dobles_faltas INT DEFAULT 0,
    
    primeros_saques_in INT DEFAULT 0,    -- Cantidad de primeros que entraron
    primeros_saques_total INT DEFAULT 0, -- Total de primeros intentados (para sacar el %)
    
    puntos_ganados_1er_saque INT DEFAULT 0, -- De los que entraron, cuántos ganó
    puntos_ganados_2do_saque INT DEFAULT 0, -- Puntos ganados con segundo saque
    
    -- BLOQUE B: JUEGO / RESTO
    winners INT DEFAULT 0,             -- Golpes ganadores
    errores_no_forzados INT DEFAULT 0, -- Unforced Errors
    
    puntos_ganados_resto INT DEFAULT 0, -- Puntos ganados cuando sacaba el rival
    total_puntos_ganados INT DEFAULT 0, -- La suma total de puntos del partido
    
    -- BLOQUE C: MOMENTOS CLAVE (BREAK POINTS)
    break_points_convertidos INT DEFAULT 0,   -- Cuántas veces rompió el saque
    break_points_oportunidades INT DEFAULT 0, -- Cuántas oportunidades tuvo (ej: 3 de 10)
    
    -- Restricción de seguridad: no puede haber stats negativas
    CHECK (aces >= 0),
    CHECK (dobles_faltas >= 0),
    CHECK (primeros_saques_in <= primeros_saques_total), -- No puedes meter más saques de los que tiras
    CHECK (break_points_convertidos <= break_points_oportunidades) -- No puedes convertir más BPs de los que tienes
);

-- ==========================================================
-- 6. TABLA DE TORNEOS
-- ==========================================================
CREATE TABLE torneos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    id_usuario_creador INT REFERENCES usuarios(id) ON DELETE SET NULL,
    superficie VARCHAR(20) CHECK (superficie IN ('Dura', 'Arcilla', 'Hierba')),
    formato_sets INT CHECK (formato_sets IN (1, 3, 5)) DEFAULT 3,
    tiebreak_ultimo_set BOOLEAN DEFAULT TRUE,
    num_jugadores INT NOT NULL CHECK (num_jugadores IN (4, 8, 16)),
    id_ganador INT REFERENCES jugadores(id) ON DELETE SET NULL,
    ids_jugadores TEXT,                      -- IDs de jugadores participantes separados por coma (ej: '1,3,5,7')
    ids_partidos TEXT,                       -- IDs de partidos generados separados por coma (ej: '10,11,12')
    completado BOOLEAN DEFAULT FALSE,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- ==========================================================
-- 7. TABLA DE PARTIDOS DE TORNEO (une torneos con partidos)
-- ==========================================================
CREATE TABLE torneo_partidos (
    id SERIAL PRIMARY KEY,
    id_torneo INT REFERENCES torneos(id) ON DELETE CASCADE,
    id_partido INT REFERENCES partidos(id) ON DELETE CASCADE,
    ronda INT NOT NULL,          -- 1 = final, 2 = semifinal, 4 = cuartos, 8 = octavos...
    posicion INT NOT NULL,       -- Posición dentro de la ronda (1, 2, 3...)
    id_jugador_1 INT REFERENCES jugadores(id) ON DELETE CASCADE,
    id_jugador_2 INT REFERENCES jugadores(id) ON DELETE CASCADE,
    id_ganador INT REFERENCES jugadores(id) ON DELETE SET NULL,
    completado BOOLEAN DEFAULT FALSE
);

-- ==========================================================
-- INSERCIÓN DE JUGADORES LEYENDA Y ACTUALES
-- ==========================================================

INSERT INTO jugadores (
    nombre, apellido, nacionalidad, altura_cm, brazo_bueno, id_creador,
    attr_primer_saque, attr_segundo_saque, attr_resto,
    attr_derecha, attr_reves,
    attr_movilidad, attr_consistencia, attr_clutch, attr_fisico
) VALUES 

-- 1. NOVAK DJOKOVIC (La Máquina Perfecta)
-- Destaca en: Resto (el mejor de la historia), Revés, Consistencia y Mente (Clutch).
('Novak', 'Djokovic', 'SRB', 188, 'R', NULL,
 92, 94, 99,  -- Saque sólido, Resto legendario (99)
 93, 98,      -- Derecha muy buena, Revés muro (98)
 95, 99, 99, 96 -- Movilidad elástica, Consistencia y Clutch máximos
),

-- 2. RAFAEL NADAL (El Rey de la Tierra)
-- Destaca en: Derecha (Spin), Físico, Mentalidad y Consistencia. Zurdo.
('Rafael', 'Nadal', 'ESP', 185, 'L', NULL,
 88, 92, 94,  -- Saque colocado, buen segundo
 99, 90,      -- La mejor derecha de la historia (99), Revés sólido
 94, 97, 99, 99 -- Físico inagotable y Mente de acero
),

-- 3. ROGER FEDERER (El Maestro)
-- Destaca en: Primer saque (precisión), Derecha y Talento ofensivo. Movilidad fluida.
('Roger', 'Federer', 'CHE', 185, 'R', NULL,
 97, 93, 88,  -- Primer saque letal por colocación
 98, 89,      -- Derecha increíble, Revés a una mano (baja un poco por bolas altas)
 93, 90, 95, 88 -- Movilidad flotante, Físico bueno pero no de maratón
),

-- 4. CARLOS ALCARAZ (El Prodigio Físico)
-- Destaca en: Potencia, Movilidad explosiva y Derecha. Un poco menos de consistencia por arriesgar.
('Carlos', 'Alcaraz', 'ESP', 183, 'R', NULL,
 90, 91, 93,
 97, 92,      -- Derecha cañón
 99, 89, 94, 96 -- Movilidad eléctrica (99), Físico bestial
),

-- 5. JANNIK SINNER (El Golpeo Limpio)
-- Destaca en: Velocidad de bola, Revés y Derecha (ambos lados muy fuertes). Frialdad.
('Jannik', 'Sinner', 'ITA', 188, 'R', NULL,
 93, 92, 95,
 96, 97,      -- De los mejores golpeos de fondo actuales
 92, 94, 96, 93 -- Muy regular y mente fría reciente
),

-- 6. ANDY MURRAY (El Estratega)
-- Destaca en: Resto, Revés y defensa. Su punto débil relativo es el segundo saque.
('Andy', 'Murray', 'GBR', 191, 'R', NULL,
 89, 78, 97,  -- Segundo saque atacable (78), Resto élite
 88, 95,      -- Revés buenísimo
 94, 96, 92, 92 -- Defensor increíble y muy consistente
);