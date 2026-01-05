* Objetivo
    * Expectativas
    * Criterios de aceptación
* Definiciones elementales
    * Stack requerido
    * Condiciones de uso (ej: open source)
* Instrucciones
    * Desarrollar una aplicación web que permita conectarse y consumir los datos del proyecto Copernicus (CDSE) con el objetivo de generar una "estimación de generación solar". 
    * La estimación de generación solar se basará en la información de copernicus, localización geográfica (seleccionable mediante mapa) y en parámetros estándar como metros cuadrados de cobertura de paneles, generación por día, etc.
    * La app debe tener dos partes fundamentales: 
        * Un mapa interactivo para seleccionar cualquier zona geográfica
        * Un gráfico de estimación de Radiación Global Horizontal y Directa, que en el eje Y indique Radiación [kWh/m2/día] y el eje X indique los meses del año, con la generación estimada de Componente Directa y Componente difusa.
    * La aplicación tiene que servir a un usuario final que está buscando conocer cual es el potencial de instalar paneles solares
        * La estimación se hará por metraje, es decir el mínimo es 1 m2 y se puede incrementar la superficie de paneles a gusto para generar las estimaciones. 
        * Usaremos las medidas estandar, es decir no nos preocuparemos ahora de qué tipo de panel o marca de panel o especificaciones.
            * Potencia y Generación Diaria
En condiciones reales, la producción de energía se calcula en función de las horas de sol pico (HSP) de tu localidad y la potencia nominal del panel. 
Potencia Pico (W/m²): Los paneles solares residenciales actuales tienen eficiencias de entre el 20% y 23%, lo que se traduce en unos 400 W por metro cuadrado bajo condiciones estándar de prueba (irradiación de 1000 W/m²).
Generación Diaria (kWh): Para calcular la energía diaria, se multiplica la potencia por las horas de sol efectivas. Por ejemplo, en una ubicación con 5 horas de sol pico al día:
Cálculo: 0.4 kW (400 W) x 5 horas = 2 kWh por día.
Esta cifra puede variar significativamente. Un panel de 450 W (que ocupa aproximadamente 2 m²) puede producir entre 1.83 kWh en invierno y 4.27 kWh en verano en diferentes ubicaciones. 

* Experiencia digital
    * La experiencia parte en la landing page de la app, donde solo se verá el mapa global interactivo. 
        * El usuario puede seleccionar cualquier punto del mapa
        * El usuario pide "generar"
    * La landing abajo del mapa tendrá un único botón que diga "Generar" y ejecute todo el proceso según el punto seleccionado con la unidad base de 1 m2. 
    * Se genera la estimación y distribución mensual del potencial de generación. 



