Documents: Este bounded context se encarga de recibir, guardar y registrar los archivos que

  sube el usuario. Su función es aceptar documentos JSON (único tipo soportado), validar que el

  archivo exista y que cumpla con reglas básicas como tipo permitido y tamaño máximo,

  almacenar su ruta o referencia en el sistema y dejarlo en un estado inicial como uploaded.

  Requiere como mínimo el archivo, el usuario autenticado, el nombre del documento, el tipo

  MIME, el tamaño y una marca de estado para saber si ya fue analizado o no.



  Analysis: Este bounded context toma el documento guardado y lo procesa para entender su

  contenido. Primero extrae el texto del archivo, luego busca información sensible con reglas

  simples, como correos, contraseñas, tarjetas o claves API, y después usa Ollama para

  reforzar el análisis y dar contexto sobre el riesgo real del contenido. Requiere poder leer

  el archivo, convertirlo a texto, tener reglas de detección básicas y conexión con Ollama

  para obtener una interpretación del contenido. Su salida principal es una lista de

  hallazgos, una explicación breve y un nivel de riesgo.



  Decision & Audit: Este bounded context decide qué pasa con el documento y deja registro de

  todo lo ocurrido. Con base en el análisis, define si el archivo se permite, se advierte, se

  oculta parcialmente o se bloquea, y además guarda evidencia para seguridad y trazabilidad.

  Requiere el resultado del análisis, una regla de decisión basada en riesgo y un

  almacenamiento de auditoría donde queden registrados el usuario, el documento, los

  hallazgos, el nivel de riesgo, la decisión tomada y la fecha. Su objetivo es que el sistema

  no solo actúe, sino que también pueda explicar después por qué actuó así.


El problema es que muchos empleados utilizan herramientas de inteligencia artificial para resumir contratos, revisar informes, analizar datos o crear contenido. Sin darse cuenta, pueden subir documentos que contienen información confidencial, como datos de clientes, números de tarjetas, contratos, credenciales, código privado o información financiera. Esta fuga de información puede generar pérdidas económicas, sanciones legales y daños graves para la empresa.

Nuestra solución será Claude AI Guard, una plataforma segura por la que deberán pasar los documentos antes de ser utilizados con una IA. El sistema analizará cada archivo localmente con reglas de seguridad y Ollama, identificará la información sensible y asignará un riesgo: muy bajo, bajo, moderado, alto o muy alto. Dependiendo del resultado, podrá permitir el documento, mostrar una advertencia, ocultar los datos sensibles, solicitar aprobación o bloquear completamente su envío.

La aplicación tendrá un espacio para subir documentos, escribir consultas y utilizar un chatbot seguro con los archivos permitidos. Antes de que el chatbot procese el contenido, Claude explicará qué información encontró y por qué representa un riesgo. Por ejemplo, si detecta nombres y correos podrá ofrecer anonimizarlos; si encuentra contraseñas, tarjetas o claves API, bloqueará el documento y avisará al usuario.

También tendrá un centro de seguridad para la empresa. Allí se mostrarán los documentos analizados, los intentos bloqueados, los usuarios con mayor riesgo y los tipos de información detectados. La IA ayudará al equipo de seguridad a resumir los eventos y reconocer comportamientos sospechosos. Así, la empresa podrá utilizar inteligencia artificial sin perder el control de sus datos.