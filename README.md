# 🎾 ADAF Tennis Simulator

[![UCM](https://img.shields.io/badge/UCM-Universidad_Complutense_de_Madrid-red?style=flat-square)](https://www.ucm.es/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

**ADAF Tennis Simulator** es un simulador estadístico de partidos de tenis con interfaz web interactiva. Este proyecto constituye nuestro **Trabajo de Fin de Grado (TFG)** para el 4º año del Grado en Ingeniería de Software en la **Universidad Complutense de Madrid (UCM)**.

## 👥 Autores

- **Álvaro Adrada Martínez-Flórez**
- **Diego Fernández Albert**

---

## 📖 Descripción del Proyecto

El simulador permite recrear partidos y torneos de tenis utilizando modelos matemáticos y probabilísticos basados en atributos configurables de los jugadores. Desde el saque y el resto hasta la consistencia, la movilidad, el estado físico y el clutch en momentos de tensión, cada punto se calcula teniendo en cuenta las características de los tenistas y el contexto del partido.

La aplicación ofrece un **Modo Estratégico**, en el que el usuario puede tomar decisiones tácticas durante el encuentro, y una sección de **Big Data** para analizar tendencias mediante simulaciones masivas. Además, cuenta con un sistema de autenticación de usuarios que permite crear jugadores personalizados, organizar torneos y conservar el historial de simulaciones.

## ✨ Características Principales

- **Simulación punto a punto:** Motor de juego que no se limita a generar un ganador, sino que simula el desarrollo del partido mediante fases como saque, resto y peloteo.
- **Modo Estratégico:** Permite intervenir durante el partido seleccionando estrategias como agresiva, neutral o defensiva, modificando el desarrollo del punto siguiente.
- **Panel de Estadísticas y Big Data:** Historial de resultados, desglose estadístico de partidos y simulaciones masivas para analizar tendencias.
- **Gestión de Torneos:** Creación, emparejamiento y simulación de torneos eliminatorios de 4, 8 o 16 jugadores.
- **Gestión de Jugadores y Usuarios:** Registro e inicio de sesión, creación de tenistas personalizados y almacenamiento de resultados.
- **Modo Invitado:** Acceso rápido para usuarios no registrados mediante partidos de prueba predefinidos.

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.10+, FastAPI, Uvicorn
- **Frontend:** Jinja2 (Server-Side Rendering), HTML5, Tailwind CSS, JavaScript Vanilla
- **Base de Datos:** PostgreSQL
- **ORM & Seguridad:** SQLAlchemy, Passlib, bcrypt, Python-JOSE (JWT)
- **Pruebas:** pytest

---

## 🚀 Guía de Instalación y Ejecución

Sigue estos pasos para preparar el entorno y ejecutar la aplicación localmente.

### 📋 Requisitos Previos

1. Tener **Python 3.10 o superior** instalado.
2. Tener el motor de base de datos **PostgreSQL** instalado y ejecutándose (por defecto en el puerto `5432`).
3. Tener **Git** instalado para clonar el repositorio.

### ⚙️ 1. Preparación de la Base de Datos

El backend necesita conectarse a una base de datos de PostgreSQL.

1. Abre la terminal de PostgreSQL (`psql`) o utiliza una herramienta gráfica como `pgAdmin`.
2. Crea una base de datos vacía llamada `adaf`:

   ```sql
   CREATE DATABASE adaf;
   ```

3. Ejecuta el script de inicialización (`database/newDB.sql`) para crear las tablas y añadir los jugadores por defecto. Desde la terminal, en la raíz del proyecto, puedes usar:

   ```bash
   psql -U postgres -d adaf -f database/newDB.sql
   ```

   Nota: por defecto, la aplicación asume que el usuario es `postgres` y la contraseña es `root` (`postgresql://postgres:root@localhost:5432/adaf`). Si tu configuración es distinta, configura la variable de entorno `DATABASE_URL` con tu cadena de conexión.

### 💻 2. Preparación del Entorno Virtual

Es recomendable usar un entorno virtual para las dependencias de Python.

1. Abre una terminal y sitúate en el directorio raíz del proyecto:

   ```bash
   cd ADAF_Tennis_Simulator
   ```

2. Crea el entorno virtual llamado `.venv`:

   **Windows:**

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

   **Linux/Mac:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instala los requerimientos:

   ```bash
   pip install -r requirements.txt
   ```

### ▶️ 3. Ejecución del Servidor Web

Con la base de datos operativa y el entorno virtual activado, levanta el servidor backend con Uvicorn:

```bash
uvicorn backend.app.main:app --reload
```

Si todo es correcto, verás un mensaje indicando que el servidor ha arrancado. Abre tu navegador y accede a:

http://localhost:8000

---

## 🧪 Ejecución de pruebas

Con el entorno virtual activado, puedes ejecutar las pruebas automatizadas con:

```bash
pytest
```

---

## 📁 Estructura Principal del Proyecto

```text
ADAF_Tennis_Simulator/
├── backend/                # Lógica de servidor y API
│   ├── app/                # Controladores, modelos y rutas de FastAPI
│   │   ├── auth/           # Autenticación JWT y configuración de base de datos
│   │   ├── bigdata/        # Lógica del modo Big Data
│   │   ├── estrategico/    # Lógica del modo estratégico
│   │   ├── matches/        # Simulación y almacenamiento de partidos
│   │   ├── players/        # Creación y gestión de tenistas
│   │   ├── routes/         # Rutas para renderizar plantillas HTML
│   │   ├── tournaments/    # Creación y simulación de torneos
│   │   └── main.py         # Punto de entrada de FastAPI
│   └── simulator/          # Motor probabilístico de simulación
├── database/               # Scripts SQL
├── static/                 # Recursos estáticos: CSS, JS e imágenes
├── templates/              # Vistas HTML renderizadas con Jinja2
├── tests/                  # Pruebas automáticas con pytest
├── requirements.txt        # Dependencias de Python
└── README.md               # Documentación del proyecto
```

---

*Desarrollado por Álvaro y Diego.*
