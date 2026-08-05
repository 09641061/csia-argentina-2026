# Sentinel AI Guard — Frontend

Interfaz de consulta segura de una sola interacción: creas una cuenta local, escribes una consulta
y opcionalmente adjuntas un JSON, PNG o JPEG. Sentinel lo revisa y solo entonces la IA local puede
responder.

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

**Acceso** — registro e inicio de sesión local. La sesión usa el JWT Bearer emitido por el backend;
las pantallas funcionales no son accesibles sin un token válido.

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

DDD pragmático alineado con los bounded contexts públicos del backend. Los componentes React viven
exclusivamente en capas `interfaces`; `application` coordina casos de uso, `domain` conserva las
reglas y contratos, e `infrastructure` implementa HTTP, almacenamiento y mapeadores.

```text
src/
  app/                          composición, rutas, interfaces del shell y estilos
  contexts/
    iam/
      domain/                   AuthSession
      application/              coordinación de identidad dentro del provider
      infrastructure/           repositorio HTTP y persistencia local del token
      interfaces/               acceso, registro, guardas, perfil y sesión
    analysis-and-decision/
      domain/                   análisis, decisiones, consulta segura e historial
      application/              SubmitSecureQuery, GetInteractionHistory, GetInteraction
      infrastructure/           repositorios HTTP y mapeadores REST
      interfaces/               compositor, resultado, historial, detalle y sidebar
  shared/
    infrastructure/             cliente HTTP, recursos REST y configuración
    interfaces/                 primitivas y componentes visuales compartidos
    lib/                        formato de fechas y tamaños
```

No hay módulo `documents`: en el MVP el documento se envía dentro de la consulta segura y no existe
una pantalla propia de documentos. Crear ese módulo sería una carpeta sin función.

## Integración

Un único punto de entrada (`shared/infrastructure/api/http-client.ts`) hacia el backend. Traduce cada resultado de
red a un `ApiError` con mensaje para personas, aplica timeout, cancela con `AbortController` al
desmontar y evita solicitudes duplicadas mientras una consulta está en curso.

Endpoints consumidos:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/secure-queries`
- `GET /api/v1/interactions`
- `GET /api/v1/interactions/{id}`
- `GET /api/v1/analyses/{id}`

## Pruebas

47 pruebas con Vitest y Testing Library, sin red: `fetch` siempre está sustituido por un doble.

Cubren consulta sin documento, documento sin consulta, consulta con documento, formatos admitidos,
retirada del archivo, estado de análisis, resultado permitido, resultado bloqueado, respuesta del
modelo, bloqueo sin respuesta, hallazgos enmascarados, error de análisis, error de generación,
historial, paginación, navegación, ausencia de contenido sanitizado, ausencia de dashboard,
ausencia de interfaz de chat y backend caído.

## Diseño

Sistema visual construido con Tailwind CSS y componentes shadcn/ui sobre Radix: tipografía Geist,
paleta monocromática, foco visible, navegación por teclado y componentes reutilizables para
formularios, alertas, tablas, menús y navegación móvil.

## Nota de dependencias

`npm audit` reporta un aviso alto sobre `react-router` referido a su **modo RSC** (React Server
Components). Esta aplicación es un SPA con `BrowserRouter` y no usa RSC, por lo que el aviso no
aplica. Todas las versiones 7.x publicadas están dentro de algún rango afectado, así que se usa la
más reciente en lugar de fijar una versión antigua con más avisos.
