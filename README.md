# Proyectos en /var/home/joss/Proyectos

Este repositorio agrupa varias iniciativas activas. Usa este README para orientarte rápidamente y saltar al proyecto que necesites.

## Tabla rápida

| Proyecto | Objetivo | Tecnologías principales |
|----------|----------|-------------------------|
| [TamingTechnology](./TamingTechnology) | Sistema de orquestación para aprendizaje y trabajo asistido por IA. | Guías Markdown, prompts especializados, workflows para AI assistants. |
| [eino1](./eino1) | Proxy de memoria dinámica para consultas corporativas a LLMs. | Go + CloudWeGo Eino, Nuxt 3 + Pinia, Postgres, Qdrant, Redis. |
| [nanocoder-go](./nanocoder-go) | Agente de código local-first con CLI/TUI y arquitectura Eino. | Go 1.25, Bubble Tea, Eino flows, PWA Go/WebAssembly. |

---

## TamingTechnology
- **Descripción**: Metodología completa para orquestar múltiples AIs según perfil y objetivo (desarrollo, investigación, management). Incluye perfiles de usuario, prompts guiados y adaptaciones por dominio.
- **Puntos de entrada**: `README.md` (guía interactiva), `USER-PROFILE.md`, `PROMPTS/`, `RESEARCH-PATHWAY/`.
- **Uso típico**: Copiar el README en un LLM para recibir instrucciones personalizadas y rutas de aprendizaje.

## eino1 (Dynamic Memory Proxy)
- **Descripción**: Plataforma que observa consultas a LLMs, enriquece el contexto con memoria persistente y aplica refuerzo selectivo basado en feedback humano y evaluaciones automáticas.
- **Stack**: Backend Go/Eino (handlers → use cases), frontend Nuxt 3, base de datos Postgres + Qdrant para embeddings, Redis opcional.
- **Documentación clave**: `Docs/` (arquitectura, PRD, plan), `backend/` y `frontend/` con estructuras claras, `.env.example` + `configs/.env.example` para configuración.
- **Para comenzar**: Revisar `Docs/README.md`, preparar variables de entorno y usar `docker-compose.yml` para levantar la pila completa.

## nanocoder-go
- **Descripción**: Reimplementación terminal-first de Nanocoder como agente AI local, con CLI/TUI moderna, herramientas automáticas y migración progresiva a la arquitectura Eino (60% completada).
- **Características**: Flujos SimpleChat y ReAct con tool calling, historial de diffs interactivo, dashboard web PWA, integración con proxies OpenAI-compatibles.
- **Documentación clave**: `README.md`, `INICIO_RAPIDO.md`, `flows/README.md`, `WEB_DASHBOARD_README.md`, numerosos guías de sesiones y migración.
- **Uso sugerido**: Consultar `INICIO_RAPIDO.md` para configurar entorno y ejecutar binarios TUI, o explorar `flows/` para entender las implementaciones Eino.

---

Mantén este README actualizado cuando cambie el estado de algún proyecto (nuevos hitos, stacks o documentos relevantes).# aprender_ai
