# Sentinel AI Guard — Frontend

Interfaz de consulta segura de una sola interacción: escribes una consulta, opcionalmente adjuntas
un JSON, PDF, Word, Excel o imagen, Sentinel lo revisa y solo entonces la IA local puede responder.

No es un chatbot. No hay conversaciones, ni lista de mensajes, ni memoria. No hay dashboard.

## Requisitos

- Node.js estable (verificado con 24.11.1) y npm.
- El backend en ejecución (por defecto `http://127.0.0.1:8000`).

## Ejecutar

```powershell
npm install
npm run dev
```

- Aplicación: `http://localhost:5173`

Copia [.env.example](.env.example) a `.env` si tu backend no está en el puerto por defecto:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

El backend debe permitir este origen con `FRONTEND_ORIGIN`.

## Comandos

```powershell
npm run lint     # ESLint
npm run test     # Vitest + Testing Library
npm run build    # tsc -b && vite build
npm run preview  # sirve el build de producción
```

## Pantallas

**Consultar** — campo de consulta con contador de caracteres, zona opcional para adjuntar un archivo
(nombre, tamaño y opción de retirarlo), y un botón que se adapta: `Analizar y consultar` cuando hay
pregunta, `Analizar documento` cuando solo hay archivo.

- Resultado permitido con pregunta: veredicto, nivel de riesgo, explicación, respuesta del modelo,
  fecha y opción de nueva consulta.
- Resultado permitido sin pregunta: veredicto y riesgo, sin respuesta de IA, porque no se preguntó
  nada.
- Resultado bloqueado: motivo, riesgo, tipos de información detectados, hallazgos enmascarados,
  aviso explícito de que el contenido no se envió al generador y opción de editar y reintentar.

**Historial** — tabla con tipo, referencia, fecha, riesgo, decisión, estado de generación y acceso
al detalle. Incluye paginación, estado vacío, estado de carga y error recuperable.

**Detalle** — explica por qué una interacción fue permitida o bloqueada, con las revisiones
asociadas (consulta y documento), su vista previa enmascarada y sus hallazgos.

## Lo que la interfaz nunca hace

- No calcula la decisión: la autoridad es el backend. El frontend solo la representa.
- No ofrece una versión segura o sanitizada del contenido bloqueado, ni botones para copiarla o
  descargarla.
- No muestra valores originales: solo la evidencia enmascarada que envía el backend.
- No expone stack traces, rutas internas ni configuración. Todo fallo se traduce a un mensaje en
  español comprensible para una persona no técnica.

## Arquitectura

DDD pragmático. Cada módulo contiene solo las capas que realmente usa; no hay carpetas vacías ni
clases ceremoniales.

```text
src/
  app/                          layout, rutas y estilos
  modules/
    analysis/
      domain/                   RiskLevel, Decision, AnalysisStatus, GenerationStatus,
                                ContentType, Finding, SecurityAnalysis
      infrastructure/           mapeadores de recursos REST a dominio
    secure-query/
      domain/                   SecureInteraction, AssistantResponse, SecureQueryDraft, contrato
      application/              SubmitSecureQuery
      infrastructure/           HttpSecureQueryRepository, mapeadores
      presentation/             página, formulario, resultado y hook
    history/
      domain/                   InteractionRepository, InteractionPage
      application/              GetInteractionHistory, GetInteraction
      infrastructure/           HttpInteractionRepository
      presentation/             historial, detalle y hooks
  shared/
    api/                        cliente HTTP, ApiError, tipos de los recursos REST
    config/                     variables de entorno
    lib/                        formato de fechas y tamaños
    ui/                         componentes de presentación reutilizables
```

No hay módulo `documents`: en el MVP el documento se envía dentro de la consulta segura y no existe
una pantalla propia de documentos. Crear ese módulo sería una carpeta sin función.

## Integración

Un único punto de entrada (`shared/api/http-client.ts`) hacia el backend. Traduce cada resultado de
red a un `ApiError` con mensaje para personas, aplica timeout, cancela con `AbortController` al
desmontar y evita solicitudes duplicadas mientras una consulta está en curso.

Endpoints consumidos:

- `POST /api/v1/secure-queries`
- `GET /api/v1/interactions`
- `GET /api/v1/interactions/{id}`
- `GET /api/v1/analyses/{id}`

## Pruebas

42 pruebas con Vitest y Testing Library, sin red: `fetch` siempre está sustituido por un doble.

Cubren consulta sin documento, documento sin consulta, consulta con documento, formatos admitidos,
retirada del archivo, estado de análisis, resultado permitido, resultado bloqueado, respuesta del
modelo, bloqueo sin respuesta, hallazgos enmascarados, error de análisis, error de generación,
historial, paginación, navegación, ausencia de contenido sanitizado, ausencia de dashboard,
ausencia de interfaz de chat y backend caído.

## Diseño

Fuente del sistema (`-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
"Segoe UI", Roboto, Helvetica, Arial, sans-serif`), fondo neutro, bordes discretos, colores de
riesgo sobrios, ancho de lectura acotado, foco visible y navegación por teclado. Sin gradientes,
glow, glassmorphism, hero sections ni gráficos.

## Nota de dependencias

`npm audit` reporta un aviso alto sobre `react-router` referido a su **modo RSC** (React Server
Components). Esta aplicación es un SPA con `BrowserRouter` y no usa RSC, por lo que el aviso no
aplica. Todas las versiones 7.x publicadas están dentro de algún rango afectado, así que se usa la
más reciente en lugar de fijar una versión antigua con más avisos.
