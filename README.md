# TFM — Modelo de Machine Learning para la identificación de oportunidades inmobiliarias en Ámsterdam

## Descripción del proyecto

Este repositorio contiene la implementación completa de un sistema que detecta propiedades infravaloradas en el mercado inmobiliario de Ámsterdam. El proyecto combina un *scraper* de [Funda.nl](https://www.funda.nl/), un *backend* Django REST con PostgreSQL, un *pipeline* de *Machine Learning* que entrena un modelo de predicción de precios y un *frontend* con React y TypeScript que visualiza las oportunidades detectadas. Una propiedad se considera **oportunidad** cuando su precio es al menos un 10 % inferior al precio predicho por el modelo.

## Autor

**Carlos Ibáñez Sánchez**

Máster Universitario en Data Science, Universitat Oberta de Catalunya (UOC)

Email: carlosibasam@uoc.edu

## Fecha

Mayo de 2026

## Arquitectura del sistema

El sistema está formado por cuatro servicios independientes orquestados mediante Docker Compose:

1. **Scraper** (Python + Selenium + BeautifulSoup): Extrae propiedades de Funda.nl y las envía al *backend* vía API REST.
2. **Backend** (Django + Django REST Framework): Valida los datos, los persiste en PostgreSQL y expone la API para el *frontend* y el *pipeline* de ML.
3. **Base de datos** (PostgreSQL): Almacena las propiedades, modelos ML, predicciones y estadísticas de barrios.
4. **ML Pipeline** (Python): Entrena el modelo con propiedades históricas y detecta oportunidades sobre las activas.
5. **Frontend** (React + TypeScript): Consume la API y visualiza las oportunidades inmobiliarias en Ámsterdam.

## Estructura del proyecto

```plaintext
TFM Repo/
│
├── backend/                          # API REST Django
│   ├── config/                       # Settings, URLs, health checks
│   ├── properties/                   
│   │   ├── models.py                 # Property, MLModel, Prediction, NeighborhoodStats
│   │   ├── views.py                  # ViewSets + Acción opportunities
│   │   ├── serializers.py            # Serializers
│   │   ├── constants.py              # Validaciones y choices
│   │   ├── admin.py                  # Panel de administración
│   │   ├── management/commands/      # Comandos personalizados
│   │   │   ├── run_ml_pipeline.py
│   │   │   ├── load_neighborhood_stats.py
│   │   │   └── load_properties.py
│   │   └── tests/                    # Tests del backend
│   ├── requirements.txt              # Requirements específicos el backend en Docker
│   └── Dockerfile
│
├── scraper/                          # Scraper de Funda.nl
│   ├── clients/                      # Cliente HTTP y Selenium
│   ├── processors/                   # Parsers de listados
│   ├── config/                       # Configuración del scraper
│   ├── scraper.py                    # Punto de entrada (modo manual)
│   ├── tests/                        # Tests unitarios del scraper
│   ├── requirements.txt              # Requirements específicos el scraper en Docker
│   └── Dockerfile
│
├── ml_pipeline/                      # Pipeline de Machine Learning
│   ├── data_preparation/
│   │   └── data_transformer.py       # Limpieza + feature engineering
│   ├── modeling/
│   │   ├── model_trainer.py          # Comparación + CV-5
│   │   ├── hyperparameter_tuner.py   # RandomizedSearchCV
│   │   ├── opportunity_detector.py   # Detección de oportunidades
│   │   └── hyperparameter_tuning.ipynb
│   ├── eda/
│   │   ├── eda_helper.py
│   │   └── eda.ipynb                 # Análisis exploratorio
│   ├── tests/                        # Tests del pipeline ML
│   ├── ml_config.py                  # Configuración centralizada
│   └── main_pipeline.py              # Orquestador del pipeline
│
├── frontend/                         # Frontend React + TypeScript
│   ├── src/
│   │   ├── components/               # PropertyMap, PropertyCard, Filters, ...
│   │   ├── services/api.ts           # Cliente Axios de la API
│   │   ├── hooks/                    # useOpportunities, useProperties
│   │   ├── types/                    # Tipos TypeScript
│   │   └── App.tsx
│   ├── package.json
│   ├── .env 
│   ├── .env.example
│   └── Dockerfile
│
├── data/                             # Datasets y resultados
│   ├── properties.csv                # CSV de propiedades
│   ├── property_images.csv           # CSV de las imágenes de las propiedades
│   ├── amsterdam_neighborhood_stats.csv  # Stats WOZ por barrio
│   └── ml_results/                   # Resultados del pipeline (CSVs, .pkl, JSON)
│
├── docker-compose.yml                # Orquestación de servicios
├── .env                              # Variables de entorno
├── .env.example                      # Template de variables de entorno
├── .gitignore
├── requirements.txt                  # Dependencias Python centralizadas (36 paquetes)
├── LICENSE
└── README.md
```

## Requisitos previos

Antes de empezar, tener instalado:

- **Docker** ≥ 20.10 y **Docker Compose** ≥ 2.0

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd "TFM_ML_Oportunidades_Inmobiliarias_Amsterdam_"
```

### 2. Configurar variables de entorno

Copiar la plantilla y rellenar los valores:

```bash
cp .env.example .env
```

Edita `.env` con tus valores.


### 3. Despliegue con Docker

Construir y arrancar todos los servicios:

```bash
docker compose up --build
```

La primera ejecución:

- Construye las imágenes de *scraper*, *backend* y *frontend*.
- Levanta PostgreSQL.
- Arranca el *backend* y el *frontend*.

Una vez todo levantado:

- *Frontend*: <http://localhost:3000>
- *Backend* API: <http://localhost:8000/api/>
- Panel de administración Django: <http://localhost:8000/admin/>
- *Health check*: <http://localhost:8000/health/>

## Configuración inicial

Una vez los servicios estén levantados, hay tres tareas iniciales que se ejecutan **una sola vez**.

### 1. Aplicar migraciones de la base de datos

Crear las tablas en PostgreSQL a partir de los modelos de Django:

```bash
docker exec tfm_backend python manage.py migrate
```

Este comando crea las tablas `Property`, `MLModel`, `Prediction`, `NeighborhoodStats` y `PropertyImage` en la base de datos.

### 2. Crear superusuario de Django

Necesario para acceder al panel de administración (`/admin/`):

```bash
docker exec -it tfm_backend python manage.py createsuperuser
```

Pedirá nombre de usuario, email y contraseña.

### 3. Cargar las estadísticas de barrios (WOZ)

Estas estadísticas oficiales del Ayuntamiento de Ámsterdam (2025) alimentan tres *features* del modelo (`neighborhood_avg_price`, `neighborhood_avg_area`, `neighborhood_property_count`). Solo se cargan una vez:

```bash
docker exec -it tfm_backend python manage.py load_neighborhood_stats
```

Lee `data/amsterdam_neighborhood_stats.csv` y lo persiste en la tabla `NeighborhoodStats`.

### 4. (Opcional) Cargar propiedades e imágenes desde CSV

Si se quiere empezar con el *dataset* existente (sin tener que esperar al *scraper*) y reproducir los resultados del proyecto:

```bash
docker exec -it tfm_backend python manage.py load_properties
```

Este comando:
- Lee `data/properties.csv` y lo persiste en la tabla `Property` usando *upsert* por URL.
- Lee `data/property_images.csv` y carga las imágenes asociadas a cada propiedad en la tabla `PropertyImage`.

## Flujo de uso

### 1. Extraer datos con el *scraper*

El *scraper* se ejecuta para scrapear propiedades de Funda.nl:

```bash
docker exec -it tfm_scraper python scraper.py
```

El *scraper*:

1. Marca automáticamente las propiedades existentes como inactivas.
2. Recorre Funda.nl página a página extrayendo propiedades activas.
3. Envía cada anuncio al *backend* mediante `POST /api/properties/` con patrón *upsert* por URL.
4. Las propiedades ya existentes se actualizan; las nuevas se crean con `is_active=True`.


### 2. Ejecutar el *pipeline* de Machine Learning

Cuando haya suficientes propiedades en la base de datos (activas e inactivas), se entrena el modelo y detecta oportunidades:

```bash
docker exec -it tfm_backend python manage.py run_ml_pipeline --source postgresql
```

**Argumentos opcionales:**

- `--source csv`: Carga propiedades desde `data/properties.csv` (útil para reproducibilidad).
- `--no-save`: No exporta CSVs locales (solo actualiza PostgreSQL).

### 3. Visualizar resultados en el navegador

Abrir <http://localhost:3000> para la visualización de:

- **Oportunidades**: Propiedades infravaloradas con su precio predicho, descuento y ahorro potencial, sobre un mapa interactivo e individualmente.
- **Modelo ML**: Métricas del modelo activo, tabla comparativa de modelos e importancia de variables.
- **Todas las Propiedades**: Catálogo completo de propiedades activas con filtros.

### 4. (Opcional) Ejecutar los *notebooks* para análisis

Los *notebooks* de EDA y de *hyperparameter tuning* están en `ml_pipeline/`. Ejecutarlos para obtener los resultados de los análisis desarrollados.


## Dependencias Python

El proyecto usa un **único archivo `requirements.txt`** con los paquetes necesarios para ejecutar el proyecto.

El proyecto utiliza **tres archivos de dependencias** para cada servicio:

- **`requirements.txt`**: Dependencias completas para utilizar en local.
- **`backend/requirements.txt`**: Dependencias para el backend en Docker.
- **`scraper/requirements.txt`**: Dependencias para el scraper en Docker.

### Instalación

**Con Docker**: Los Dockerfiles instalan automáticamente las dependencias necesarias al hacer `docker compose up --build`.

**Sin Docker** (para ejecutar localmente):

```bash
pip install -r requirements.txt
```


## Tests

El proyecto incluye tests unitarios y de integración:

```bash
# Tests del backend
docker exec -it tfm_backend python manage.py test

# Tests del pipeline ML
docker exec -it tfm_backend pytest /ml_pipeline/tests/

# Tests del scraper
docker exec -it tfm_scraper pytest /app/tests/
```


## Comandos útiles

```bash
# Ver logs de un servicio
docker logs -f tfm_backend
docker logs -f tfm_scraper

# Acceder a la shell de Django
docker exec -it tfm_backend python manage.py shell

# Acceder a PostgreSQL
docker exec -it tfm_database psql -U tfm_user -d amsterdam_properties

# Reiniciar un servicio
docker restart tfm_backend

# Detener todo
docker compose down

# Detener y eliminar también el volumen de la base de datos (BORRA los datos)
docker compose down -v

# Reconstruir contenedores después de cambios en código
docker compose up --build -d

# Ver estado de servicios
docker compose ps

# Ver logs de todos los servicios
docker compose logs -f
```

## Licencia

All rights reserved.
