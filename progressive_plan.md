# Plan Progresivo: Enterprise RAG con Graph + Vector

## Descripción Global
Este proyecto consiste en el desarrollo de un sistema **Enterprise RAG (Retrieval-Augmented Generation)** diseñado para centralizar y consultar eficientemente el conocimiento interno de una organización disparado en diversos formatos (PDF, Markdown, Office). El sistema utiliza una arquitectura híbrida que combina la precisión de la **búsqueda vectorial** con la profundidad semántica de una **base de datos de grafos**, garantizando respuestas precisas y trazables.

## Objetivo Principal
Optimizar el acceso a la documentación interna mediante una IA capaz de generar respuestas con **citación verificable**, reduciendo el tiempo de búsqueda en un **65%** y minimizando los costes operativos mediante estrategias avanzadas de cache y control de tokens.

---
Este documento se construirá paso a paso a medida que se respondan las preguntas funcionales.

## Fase 1: Ingesta de Datos y Configuración de Entorno ✅
- Tarea 1.1: Inicialización del Proyecto ✅
- Tarea 1.2: Configuración del Lector de Archivos Locales ✅
- Tarea 1.3: Gestión de Variables de Entorno ✅
- Tarea 1.4: Lógica de Versionado e Historial de Auditoría ✅
- Tarea 1.5: Dockerización Inicial ✅

## Fase 2: Pipeline RAG y Búsqueda Vectorial ✅
- Tarea 2.1: Modelado de Embeddings y Chunking ✅
- Tarea 2.2: Construcción del Índice Vectorial con Historial Completo ✅
- Tarea 2.3: Motor de Consulta (Query Engine) ✅

## Fase 3: Capa de Conocimiento (Graph RAG) ✅
- Tarea 3.1: Infraestructura y Conectividad (FalkorDB) ✅
- Tarea 3.2: Modelado y Extracción del Grafo (Entidades y Relaciones) ✅
- Tarea 3.3: Búsqueda Híbrida Integrada (Vector + Graph) ✅

## Fase 4: API de Servicio y Control de Costes ✅
- **Tarea 4.1: Endpoints de FastAPI y Auditoría** ✅
    - Implementar `/query` (Híbrido) y `/audit`.
- **Tarea 4.2: Capa de Caching y Rate Limiting** ✅
    - Configurar límites y optimización de tokens.
- **Tarea 4.3: Manejo de Citas y Trazabilidad** ✅
    - Inclusión de metadatos en las respuestas de la API.

## Fase 5: Despliegue e Instancia Prod-Ready ✅
- **Tarea 5.1: Orquestación Final** ✅
    - Docker Compose completo con todos los servicios
    - Nginx reverse proxy con rate limiting
    - Prometheus + Grafana para monitoreo
- **Tarea 5.2: Evaluación de Calidad (RAGAS)** ✅
    - Sistema completo de evaluación con RAGAS
    - Métricas de calidad automatizadas
    - Comparación entre motores híbrido y vector-only

## Fase 6: Interfaz de Usuario (Frontend) ⏳
- **Tarea 6.1: Configuración del Proyecto (Vite + Vanilla JS)**
    - Inicialización de estructura optimizada.
    - Definición del sistema de diseño **"Cyber-Vibrant"** (Neon/Dark Glassmorphism).
- **Tarea 6.2: Implementación de Dashboard Premium**
    - **Chat Widget**: Soporte para Markdown, streaming y visualización de fuentes.
    - **Control Panel**: Gestión de ingesta de archivos y visualización de auditoría.
    - **Stats Monitor**: Métricas en tiempo real de uso de tokens y costes.
- **Tarea 6.3: Integración y Despliegue**
    - Conexión con endpoints de FastAPI (`/query`, `/ingest`, `/stats`).
    - Containerización con Nginx (Multi-stage build).
    - Actualización de `docker-compose.yml` para unificación de servicios.

---
## Estado Actual: Fase 5 completada. Sistema producción-ready con orquestación completa y evaluación de calidad.
