# Plan Progresivo: Enterprise RAG con Graph + Vector

## Descripción Global
Este proyecto consiste en el desarrollo de un sistema **Enterprise RAG (Retrieval-Augmented Generation)** diseñado para centralizar y consultar eficientemente el conocimiento interno de una organización disparado en diversos formatos (PDF, Markdown, Office). El sistema utiliza una arquitectura híbrida que combina la precisión de la **búsqueda vectorial** con la profundidad semántica de una **base de datos de grafos**, garantizando respuestas precisas y trazables.

## Objetivo Principal
Optimizar el acceso a la documentación interna mediante una IA capaz de generar respuestas con **citación verificable**, reduciendo el tiempo de búsqueda en un **65%** y minimizando los costes operativos mediante estrategias avanzadas de cache y control de tokens.

---
Este documento se construirá paso a paso a medida que se respondan las preguntas funcionales.

## Fase 1: Ingesta de Datos y Configuración de Entorno

### Objetivos:
Configurar la base del proyecto y el mecanismo para leer archivos locales en diversos formatos.

### Tareas:
*   **Tarea 1.1: Inicialización del Proyecto [COMPLETADA]**
    *   Crear la estructura de carpetas estándar: `/data` (para los archivos locales), `/src` (código fuente) y `/config`.
    *   Definir el archivo `requirements.txt` con las librerías base (LlamaIndex, FastAPI, Qdrant-client).
*   **Tarea 1.2: Configuración del Lector de Archivos Locales [COMPLETADA]**
    *   Implementar `SimpleDirectoryReader` de LlamaIndex configurado para filtrar tipos de archivos `.pdf`, `.md`, `.docx`, `.xlsx`.
    *   Validar la carga recursiva de la carpeta `/data`.
*   **Tarea 1.3: Gestión de Variables de Entorno [COMPLETADA]**
    *   Crear `.env.example` y `.env` para manejar la ruta de la carpeta local y las API Keys de OpenAI/Anthropic.
*   **Tarea 1.4: Lógica de Versionado e Historial de Auditoría [COMPLETADA]**
    *   Implementar un sistema de hashing (SHA-256) para detectar cambios.
    *   Crear una base de datos de auditoría (SQLite o similar) que registre: `hash`, `file_path`, `author`, `timestamp` y `version_number`.
    *   Diseñar el flujo de captura del usuario/autor del cambio (vía API o metadatos del sistema de archivos).
*   **Tarea 1.5: Dockerización Inicial [COMPLETADA]**
    *   Crear `Dockerfile` y `docker-compose.yml` para levantar la instancia de Qdrant y el entorno de desarrollo.

## Fase 2: Pipeline RAG y Búsqueda Vectorial

### Objetivos:
Implementar el núcleo de búsqueda utilizando modelos comerciales (GPT-4/Claude), persistencia en Qdrant y soporte para múltiples versiones.

### Tareas:
*   **Tarea 2.1: Modelado de Embeddings y Chunking [COMPLETADA]**
    *   Implementar una estrategia de chunking semántico (300-500 tokens).
    *   Configurar el modelo de embeddings (ej. `text-embedding-3-small` de OpenAI).
*   **Tarea 2.2: Construcción del Índice Vectorial con Historial Completo [COMPLETADA]**
    *   Implementar la inserción de vectores en Qdrant asegurando la **no-sobreescritura** de versiones antiguas.
    *   Enriquecer metadatos: `file_name`, `page`, `version_id`, `author`, `updated_at` y label `is_active`.
    *   Lógica de filtrado dinámico para que las búsquedas estándar usen `is_active=true` y las de auditoría puedan acceder a todo el historial.
*   **Tarea 2.3: Motor de Consulta (Query Engine) [COMPLETADA]**
    *   Crear el pipeline de consulta básico que recupere contexto de Qdrant y genere respuestas con GPT-4/Claude.

## Fase 3: Capa de Conocimiento (Graph RAG)

### Objetivos:
Enriquecer el contexto con relaciones semánticas usando FalkorDB y Graphity.

### Tareas:
*   **Tarea 3.1: Configuración de FalkorDB**
    *   Añadir el servicio de FalkorDB al `docker-compose.yml`.
*   **Tarea 3.2: Modelado del Grafo de Conocimiento**
    *   Definir el esquema de entidades: **Documento**, **Tema**, **Proyecto**, **Tecnología** y **Autor**.
    *   Implementar la lógica de extracción automática de estas entidades usando Graphity y prompts especializados.
*   **Tarea 3.3: Búsqueda Híbrida (Vector + Graph)**
    *   Integrar la travesía del grafo en el pipeline de recuperación para mejorar la precisión en consultas complejas.

## Fase 4: API de Servicio y Control de Costes

### Objetivos:
Exponer el sistema mediante una API segura, eficiente y con control de consumo.

### Tareas:
*   **Tarea 4.1: Endpoints de FastAPI y Auditoría**
    *   Implementar `/query` (consulta RAG con filtro de versión opcional).
    *   Implementar `/audit/{file_name}` para obtener el historial completo de cambios, quién y cuándo.
    *   Endpoints `/health` y `/sources`.
*   **Tarea 4.2: Capa de Caching y Rate Limiting**
    *   Implementar un sistema de caché de respuestas (Redis o in-memory) para consultas repetitivas.
    *   Configurar límites de peticiones por usuario para asegurar el control de costes del LLM.
*   **Tarea 4.3: Manejo de Citas y Trazabilidad**
    *   Asegurar que cada respuesta incluya metadatos verificables del origen de la información.

## Fase 5: Despliegue e Instancia Prod-Ready

### Objetivos:
Asegurar que el sistema sea fácil de desplegar y cumpla con métricas básicas de calidad.

### Tareas:
*   **Tarea 5.1: Orquestación Final**
    *   Refinar el `docker-compose.yml` para incluir volumenes persistentes y configuración productiva de Qdrant/FalkorDB.
*   **Tarea 5.2: Evaluación de Calidad (RAGAS)**
    *   Ejecutar pruebas automatizadas de fidelidad y relevancia de las respuestas.

## Fase 6: Interfaz de Usuario (Frontend)

### Objetivos:
Crear una interfaz moderna, responsiva y de alto impacto visual para interactuar con el RAG y consultar la auditoría.

### Tareas:
*   **Tarea 6.1: Diseño y Prototipado (Look & Feel)**
    *   Definir una estética "Premium": Dark mode, glassmorphism y micro-animaciones.
*   **Tarea 6.2: Desarrollo del Dashboard de Consulta**
    *   Implementar la interfaz de chat con soporte para streaming de respuestas y visualización de citas.
*   **Tarea 6.3: Panel de Auditoría e Historial**
    *   Crear una vista para navegar por las versiones de los documentos y ver el timeline de cambios.
*   **Tarea 6.4: Integración con la API**
    *   Conectar el frontend con `/query` y `/audit` usando comunicación asíncrona.

---
## Estado Actual: Verificando Fases 1 y 2 con Pruebas Unitarias antes de iniciar Fase 3.
