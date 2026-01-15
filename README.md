# Enterprise-RAG

Enterprise-RAG es una plataforma de Retrieval-Augmented Generation (RAG) para gestionar y consultar de forma eficiente el conocimiento interno de una organización. Combina búsqueda vectorial con una base de grafos para respuestas trazables y citables.

## Colaboración y alcance
- Arquitectura híbrida: embeddings + grafos.
- Endpoints de servicio para ingestión, consulta y auditoría.
- Capa de caching y control de costes (tokens, rate limiting).
- Frontend moderno con diseño Cyber-Vibrant, listo para despliegue.

## Arquitectura (alto nivel)
- Backend: API en FastAPI + módulos de almacenamiento vectorial (Qdrant), grafos (FalkorDB) y embeddings.
- Frontend: SPA modular construido con Vite, servido detrás de Nginx.
- Monitoreo: Prometheus + Grafana.
- Orquestación: Docker Compose con servicios interconectados.

## Requisitos previos
- Docker y Docker Compose
- Node.js 18+ y npm (para el frontend)
- Acceso a las claves de API necesarias (OpenAI, etc.)

## Inicio rápido
1) Clonar el repositorio y entrar al directorio del proyecto.
2) Levantar la pila: `docker-compose up -d --build`.
3) Acceder a: 
   - API: http://localhost:8000
   - Dashboard: http://localhost/ (servicio Nginx)

## Endpoints principales
- GET /health: servicio operativo
- POST /query: ejecución híbrida o vector-only; cuerpo: {"query": "texto", "engine_type": "hybrid|vector"}
- POST /ingest: ingest de datos; cuerpo: {"data_path": "/ruta", "author": "Usuario"}
- GET /audit: trazabilidad de auditoría de documentos
- GET /stats/cache: métricas de caching
- GET /stats/costs: métricas de coste por cliente
- GET /stats/usage: uso actual (rate limits, tokens, etc.)
- DELETE /cache?pattern=...: limpieza de caché
- POST /evaluate: ejecuta evaluación de calidad con RAGAS
- GET /evaluate/compare: compara rendimiento entre motores

## Estructura del repositorio (extracto)
- backend: src/ (FastAPI)
- frontend: frontend/ (Vite + Nginx)
- docker-compose.yml
- progressive_plan.md (Fases)
- README.md (este documento)

## Despliegue y operaciones
- Variables de entorno: usa `.env` para Redis, FalkorDB, Qdrant, etc.
- Para producción: considerar orquestación adicional (Kubernetes) y separación de secrets.

## Notas de mantenimiento
- Mantener consistencia entre frontend y backend al cambiar endpoints.
- Ejecutar pruebas de integración tras cambios relevantes.

## Contribuciones
- Abre issues para mejoras y parches; se recomienda usar branches por features y Pull Requests para merges.

## Estado actual
- Fase 6: Frontend migrado, integración completa y despliegue en Docker Compose
- Fase 5: Producción ready y monitoreo activo
