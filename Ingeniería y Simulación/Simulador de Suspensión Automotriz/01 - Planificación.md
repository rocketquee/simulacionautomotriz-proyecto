
### **1.1. DESCRIPCION GENERAL**
El proyecto consiste en el desarrollo de una simulacion computacional del sistema de suspencion de un automovil, con el proposito de estudiar y visualizar su comportamiento dinamico ante diferentes condiciones de la superficie de rodamiento.
Se utilizara modelos matematicos para representar la interaccion entre los elementos principales de la suspencion y analiszar como infruyen parametros como la rigidez del resorte, el coeficiente del amortiguamiento y las irregularidades de la carretea en el movimento vertical del vehiculo.
La simulacion se desarrollara utilizando python como lenguaje principal, complementando con herramientas de calculo numerico y visualizacion grafica.
El proyecto comenzara con un modelo simplificado y evolucionara progresivamente hacia una representacion visual animada que permitira modifccar parametros, ejecutar experimentos y comparar resultados.

### **1.2. PLANTEAMIENTO DEL PROBLEMA**
la suspencion de un automovil desempeña un papel importante en la respuesta del vehiculo ante las irregularidades de la carretera. Su comportamiento depende de diferentes propuedades disicas que influyen en la oscilaciones de la carroceria y en el movimiento de las ruedas.
En analisis de esta variables mediante ecuaciones matematicas permiten estudiar el comportamiento del sistema sin necesidad de realizar inicialmente pruebas fisicas sobre un automovil real.
Por lo tanto, se plante desarrollar una herramienta de simulacion qu epermita representar el comportamiento de una  suspension, modificar sus paramentros y observar los efectos producidos bajo condiciones controladas.

### **1.3. OBJETIVO GENERAL**
Desarrollar un simulador computacional de suspension automotriz mediante modelos matematicos y herramientas de programacion cientifica, capaz de representar visualmente el comportamiento dinamico del sistema y analizar la influencia de sis principales parametros fisicos.

### **1.4. OBJETIVOS ESPECIFICOS**
1. Investigar los pirncipios fisicos relacionados con el funcionamiento de los sistemas de suspension automotriz,
2. 2. Identificar las varibles y los parametros necesarios para contruir un modelo matematico simplificado.
3. Implemetar las ecuaciones del sistema mediante python.
4. Resolver numericamente el modelo y obtener datos del movimiento a lo largo del tiempo.
5. Desarrollar graficas que permitan interpretar y conparar los resultados obtenidos.
6. Construir una animaion que represente el movimiento de la carroceria, la rueda, el resorte y el amortiguafdor.
7. Realizar experimentos mediante la modificacion controlada de los parametros fisicos.
8. Documentar los procedimientos, resultadors, limitacion y posibles mejorar del simulador.

### **1.5. ALCANCE INCIAL**
la primera version del proyecto se centrara en el desarrollo del modelo de suspencion simpificado.
Se contmepla:
- Representacion matematica del sistema.
- Definicion de parametros fisicos iniciales.
- Implemetarcion del modelo en python.
- calculo numerico del movimiento,
- visualizacion del resultads mediante graficas.
- animacion bidimencional del sistema.
- comparación entre distintas configuración de rigidez y amortiguamiento.
- registros del experimentos y resultados
En esta etapa no se pretende reproducir todas las caracteristicas deun suspecion comercial ni validar el comportamiento de un vehículo real. los resultados corresponderán al modelo matemático utilizado y a los supuestos definidos.

### **1.6. HERRAMIENTAS Y TEGNOLOGIAS PREVISTAS**

| Herramientas       | Aplicacion                                            |
| ------------------ | ----------------------------------------------------- |
| python             | Implemetacion de la simulacion                        |
| Visual studio code | Entorno de desarrollo                                 |
| Numoy              | Operaciones matematicas y manero de datos numericos   |
| Scipy              | reolucion numerica de ecuaciones diferenciales.       |
| Matplotlib         | Generacion de graficas y animaciones.                 |
| Obsidian           | Bitacora tecnica y documentacion del proyecto         |
| Git                | Control de versiones del codigo                       |
| Github             | Publicacion del repositorio y del avance del proyecto |
Las Herramientas se incorporaran conforme sean encesarios durante el desarrollo.

### **1.7. METODOLOGIA  DEL TRABAJO**
El proyecto se desarrolllara mediante etapas progresivas:

**Etapa1. Investigación:** recopilación de información sobre los componentes de la suspencion y sus principios físicos.
**Etapa2. Modelado matematico:** defjiicion de las variables, parametros, acueciones y supuestos del sistemas.
**Etapa3. Implemetacion numerica:** desarrollo del programa encargado de resolver las ecuaciones del modelo.
**Etapa 4. Visualización:** construcción de gráficas y animaciones basadas en los resultados calculados.
**Etapa 5. Experimentación:** ejecución de pruebas con diferentes parámetros y condiciones de entrada.
**Etapa 6. Evaluación:** análisis de los resultados, identificación de limitaciones y documentación de conclusiones.
**Etapa 7. Presentación:** organización del código, documentación técnica y publicación del proyecto.

## 1.8. Criterios de éxito

Se considerará completada la primera versión cuando:
- El modelo matemático esté implementado y documentado.
    
- El programa ejecute la simulación sin errores.
    
- Los resultados numéricos sean coherentes con el comportamiento esperado del modelo.
    
- Las gráficas permitan observar la evolución temporal del movimiento.
    
- La animación represente el comportamiento calculado.
    
- Se hayan realizado y documentado pruebas con diferentes parámetros.
    
- El proyecto cuente con instrucciones para ejecutarlo y reproducir los experimentos.
    

## 1.9. Registro inicial

**Fecha:** 9 de octubre de 2026.
**Actividad:** Definición inicial del proyecto.
**Descripción:** Se estableció como objetivo desarrollar un simulador computacional de suspensión automotriz, orientado al estudio del comportamiento dinámico mediante modelos matemáticos, programación científica y visualización gráfica.
**Resultado:** Se definieron el propósito general, los objetivos específicos, el alcance inicial, las herramientas previstas y las etapas principales de desarrollo.

**Estado:** Planificación inicial completada. Pendiente de comenzar la investigación técnica y la preparación del entorno de desarrollo.

---

# PARTE II. INVESTIGACIÓN Y FUNDAMENTOS FÍSICOS

**Estado:** Pendiente.

### Actividades previstas

- Investigar el funcionamiento de los resortes y amortiguadores.
    
- Identificar los componentes básicos de una suspensión.
    
- Estudiar el modelo de cuarto de vehículo.
    
- Comprender las variables físicas involucradas.
    
- Investigar cómo se representa matemáticamente el movimiento vertical.
    
- Registrar las fuentes técnicas consultadas.
    

### Entregable

Documento técnico con los fundamentos físicos y matemáticos necesarios para implementar el modelo.

---

# PARTE III. FORMULACIÓN DEL MODELO MATEMÁTICO

**Estado:** Pendiente.

### Actividades previstas

- Definir las masas y los parámetros del sistema.
    
- Establecer las ecuaciones diferenciales.
    
- Definir las condiciones iniciales.
    
- Seleccionar las condiciones de entrada que representarán las irregularidades de la carretera.
    
- Establecer los parámetros iniciales de la simulación.
    

### Entregable

Modelo matemático documentado, con variables, unidades, ecuaciones y supuestos claramente identificados.

---

# PARTE IV. DESARROLLO COMPUTACIONAL

**Estado:** Pendiente.

### Actividades previstas

- Preparar el entorno de Python.
    
- Organizar la estructura del código.
    
- Implementar las ecuaciones matemáticas.
    
- Ejecutar la primera simulación numérica.
    
- Revisar los resultados obtenidos.
    
- Corregir posibles errores.
    

### Entregable

Primera versión funcional del motor de cálculo de la simulación.

---

# PARTE V. VISUALIZACIÓN Y ANIMACIÓN

**Estado:** Pendiente.

### Actividades previstas

- Crear la representación bidimensional de la suspensión.
    
- Dibujar la carrocería, la rueda, el resorte y el amortiguador.
    
- Representar el perfil de la carretera.
    
- Vincular la animación con los resultados del modelo matemático.
    
- Añadir gráficas de desplazamiento vertical.
    

### Entregable

Prototipo visual animado del sistema de suspensión.

---

# PARTE VI. EXPERIMENTACIÓN Y ANÁLISIS

**Estado:** Pendiente.

### Actividades previstas

- Ejecutar pruebas con diferentes rigideces del resorte.
    
- Modificar el coeficiente de amortiguamiento.
    
- Comparar las oscilaciones obtenidas.
    
- Analizar la respuesta del sistema ante distintos perfiles de carretera.
    
- Registrar los resultados en tablas y gráficas.
    
- Documentar las observaciones y limitaciones.
    

### Entregable

Informe de experimentación con resultados comparativos y conclusiones.

---

# PARTE VII. DOCUMENTACIÓN Y PRESENTACIÓN FINAL

**Estado:** Pendiente.

### Actividades previstas

- Revisar y organizar el código.
    
- Añadir instrucciones de instalación y ejecución.
    
- Completar la documentación técnica.
    
- Seleccionar gráficas y capturas de la simulación.
    
- Registrar las tecnologías utilizadas.
    
- Preparar el repositorio del proyecto.
    

### Entregable

Proyecto documentado y organizado para su presentación académica y como parte de un portafolio profesional.

---

# CONTROL GENERAL DE AVANCE

|Fase|Estado|
|---|---|
|I. Planificación|Completada|
|II. Investigación física|Pendiente|
|III. Modelo matemático|Pendiente|
|IV. Desarrollo computacional|Pendiente|
|V. Visualización y animación|Pendiente|
|VI. Experimentación|Pendiente|
|VII. Documentación final|Pendiente|
