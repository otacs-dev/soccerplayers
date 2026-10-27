-- 1. Tabela clube
IF OBJECT_ID('dbo.clube', 'U') IS NULL
BEGIN
    CREATE TABLE clube (
        clube_id INT IDENTITY(1,1) PRIMARY KEY,
        nome VARCHAR(150) NOT NULL UNIQUE,
        pais VARCHAR(100) NOT NULL DEFAULT 'Desconhecido'
    );
END;
GO

-- 2. Tabela jogador
IF OBJECT_ID('dbo.jogador', 'U') IS NULL
BEGIN
    CREATE TABLE jogador (
        player_id INT IDENTITY(1,1) PRIMARY KEY,
        nome VARCHAR(150) NOT NULL,
        position VARCHAR(50),
        sub_position VARCHAR(50),
        date_of_birth DATE,
        height_in_cm FLOAT CHECK (height_in_cm IS NULL OR height_in_cm > 0),
        estreia DATE,
        minutos_profissionais INT CHECK (minutos_profissionais IS NULL OR minutos_profissionais >= 0),
        jogos_profissionais INT CHECK (jogos_profissionais IS NULL OR jogos_profissionais >= 0),
        url_perfil VARCHAR(500)
    );
END;
GO

-- 3. Tabela passagem_base
IF OBJECT_ID('dbo.passagem_base', 'U') IS NULL
BEGIN
    CREATE TABLE passagem_base (
        passagem_id INT IDENTITY(1,1) PRIMARY KEY,
        player_id INT NOT NULL,
        clube_id INT NOT NULL,
        inicio DATE,
        fim DATE,
        formado_confirmado TINYINT NOT NULL DEFAULT 0 CHECK (formado_confirmado IN (0, 1)),
        fonte_conferencia VARCHAR(255),
        CONSTRAINT FK_passagem_jogador FOREIGN KEY (player_id) REFERENCES jogador(player_id) ON DELETE CASCADE,
        CONSTRAINT FK_passagem_clube FOREIGN KEY (clube_id) REFERENCES clube(clube_id),
        CONSTRAINT UQ_player_clube UNIQUE (player_id, clube_id)
    );
END;
GO

-- 4. Tabela estatistica_temporada
IF OBJECT_ID('dbo.estatistica_temporada', 'U') IS NULL
BEGIN
    CREATE TABLE estatistica_temporada (
        estatistica_id INT IDENTITY(1,1) PRIMARY KEY,
        player_id INT NOT NULL,
        temporada VARCHAR(20) NOT NULL,
        torneio VARCHAR(100) NOT NULL DEFAULT '',
        metrica VARCHAR(100) NOT NULL,
        valor FLOAT,
        minutos FLOAT,
        valor_por90 FLOAT,
        amostra_suficiente TINYINT CHECK (amostra_suficiente IS NULL OR amostra_suficiente IN (0, 1)),
        fonte VARCHAR(100) NOT NULL,
        CONSTRAINT FK_estatistica_jogador FOREIGN KEY (player_id) REFERENCES jogador(player_id) ON DELETE CASCADE,
        CONSTRAINT UQ_estatistica_unica UNIQUE (player_id, temporada, torneio, metrica, fonte)
    );
END;
GO

-- 5. Tabela indice_jogador
IF OBJECT_ID('dbo.indice_jogador', 'U') IS NULL
BEGIN
    CREATE TABLE indice_jogador (
        player_id INT PRIMARY KEY,
        indice_tecnico FLOAT CHECK (indice_tecnico IS NULL OR (indice_tecnico >= 0 AND indice_tecnico <= 100)),
        indice_explosivo FLOAT CHECK (indice_explosivo IS NULL OR (indice_explosivo >= 0 AND indice_explosivo <= 100)),
        cobertura_tecnico FLOAT CHECK (cobertura_tecnico IS NULL OR (cobertura_tecnico >= 0 AND cobertura_tecnico <= 1)),
        cobertura_explosivo FLOAT CHECK (cobertura_explosivo IS NULL OR (cobertura_explosivo >= 0 AND cobertura_explosivo <= 1)),
        n_metricas_tecnico INT,
        n_metricas_explosivo INT,
        CONSTRAINT FK_indice_jogador FOREIGN KEY (player_id) REFERENCES jogador(player_id) ON DELETE CASCADE
    );
END;
GO