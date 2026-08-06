# Claude AI Guard — Frontend

Interfaz conversacional protegida, inspirada en la estructura visual de Claude. Cada mensaje pasa
por las políticas locales de Claude antes de llegar al modelo; además, la aplicación permite
revisar contenido directamente y consultar la auditoría explicable.

## Ejecutar

Requiere Node.js estable, npm y el backend en `http://127.0.0.1:8000` (configurable con
`VITE_API_BASE_URL`).

```powershell
npm install
npm run dev
```

La aplicación se sirve por defecto en `http://localhost:5173`.

## Experiencia

- **Nuevo chat**: compositor central y conversaciones persistentes.
- **Chats**: búsqueda, selección visual y listado completo de conversaciones.
- **Sidebar**: chats recientes, acceso a todos los chats, estado del backend y perfil IAM.
- **Consulta segura**: mensaje y adjunto opcional JSON, PNG o JPEG con decisión ALLOWED/BLOCKED.
- **Análisis**: revisión directa de mensajes o de un documento registrado, historial y detalle.
- **Auditoría**: decisiones, riesgo, generación, evidencia enmascarada y enlaces a los análisis.
- **IAM**: registro, login, restauración de sesión con `/auth/me` y logout local.

## Arquitectura DDD

Los componentes React viven exclusivamente en `interfaces`. Cada bounded context mantiene sus
capas de dominio, aplicación, interfaces e infraestructura:

```text
src/contexts/
  analysis/
    domain/ application/ interfaces/ infrastructure/
  chat/
    domain/ application/ interfaces/ infrastructure/
  decision/
    domain/ application/ interfaces/ infrastructure/
  iam/
    domain/ application/ interfaces/ infrastructure/
```

`domain` define modelos y puertos, `application` contiene casos de uso, `infrastructure` adapta el
contrato REST y `interfaces` contiene páginas, componentes y hooks. El cliente HTTP y los recursos
wire compartidos viven en `shared/infrastructure`.

## Cobertura del backend

El frontend conecta los 16 endpoints expuestos actualmente:

- Health: `GET /api/v1/health`.
- IAM: `POST /auth/login`, `POST /auth/register`, `GET /auth/me`.
- Chat: crear/listar conversaciones, obtener detalle y enviar mensajes.
- Analysis: analizar mensaje/documento, listar análisis, obtener detalle y hallazgos.
- Decision: consulta segura, listado de interacciones y detalle de auditoría.

La prueba `src/contexts/backend-contract-coverage.test.ts` ejecuta los repositorios y compara el
conjunto completo de método + ruta para evitar que un endpoint del backend quede sin adaptador.

## Calidad

```powershell
npm run lint
npm run test
npm run build
```

Las pruebas no acceden a la red: sustituyen `fetch` y cubren navegación, IAM, manejo seguro de
errores y el contrato completo de endpoints. El frontend nunca recalcula una decisión de seguridad
ni intenta reconstruir valores sensibles; sólo presenta el veredicto y la evidencia enmascarada que
devuelve el backend.
