---

# 📘 Guía de Instalación: Predictor de Fútbol con IA

### 🏗️ Fase 1: Instalar Python (El Motor)

Si ya tienes Python, salta a la Fase 2. Si no, o no estás seguro:

**🪟 Para Windows:**

1. Ve a [python.org/downloads](https://www.python.org/downloads/).
2. Descarga la última versión (ej. 3.11 o 3.12).
3. ⚠️ **MUY IMPORTANTE:** Al iniciar el instalador, marca la casilla que dice **"Add Python.exe to PATH"** (o "Add Python to environment variables"). Si no haces esto, la terminal no reconocerá el comando.
4. Dale a "Install Now".

**🐧 Para Linux (Ubuntu/Debian):**
Abre tu terminal y ejecuta:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip

```

---

### 📂 Fase 2: Preparar el Proyecto

Vamos a crear una carpeta limpia para que no mezcles este proyecto con tus fotos de vacaciones.

1. Crea una carpeta nueva en tu escritorio (o donde quieras) llamada `Futbol_IA`.
2. Dentro de esa carpeta, crea un archivo de texto vacío y llámalo `main.py`.
* *Nota:* Asegúrate de que no se llame `main.py.txt`. En Windows, ve a "Vista" -> "Extensiones de nombre de archivo" para verificarlo.


3. Pega el **último código completo** que generamos dentro de `main.py` y guarda.

---

### 🛡️ Fase 3: El Entorno Virtual (La Caja de Seguridad)

Esto es lo que te dio error antes. Vamos a crear una "burbuja" aislada para instalar las librerías solo para este proyecto.

Abre tu terminal (PowerShell en Windows o Terminal en Linux) y navega hasta tu carpeta:
`cd ruta/a/tu/carpeta/Futbol_IA`

**🪟 En Windows:**

1. Crea el entorno:
```bash
python -m venv venv

```


2. Actívalo:
```bash
venv\Scripts\activate

```



**🐧 En Linux:**

1. Crea el entorno:
```bash
python3 -m venv venv

```


2. Actívalo:
```bash
source venv/bin/activate

```



✅ **Señal de éxito:** Verás que aparece `(venv)` al principio de la línea en tu terminal. Eso significa que estás dentro de la Matrix.

---

### 📦 Fase 4: Instalar Dependencias (Las Herramientas)

Ahora que estás dentro de `(venv)`, instalamos las librerías que usa nuestro código (`pandas` para datos, `requests` para internet, `scipy` para matemáticas, `numpy` para cálculos).

Ejecuta este comando (es igual para Windows y Linux):

```bash
pip install pandas requests scipy numpy

```

Verás muchas barritas de carga. Espera a que termine.

---

### 🚀 Fase 5: ¡A Jugar!

Todo está listo. Para encender el predictor, ejecuta:

**🪟 Windows:**

```bash
python main.py

```

**🐧 Linux:**

```bash
python3 main.py

```

---

### 💡 Trucos y Solución de Problemas

* **¿Cómo salgo del entorno virtual?**
Solo escribe `deactivate` en la terminal.
* **¿Cómo lo abro la próxima vez?**
1. Abres terminal.
2. Entras a la carpeta (`cd ...`).
3. Activas el entorno (Paso 3).
4. Ejecutas `python main.py`.


* **Actualizar datos:**
No tienes que hacer nada técnico. Solo cierra y vuelve a abrir el programa (`main.py`). El script descarga los datos frescos de internet cada vez que inicia.

¡Listo! Ya tienes tu centro de inteligencia deportiva corriendo en local. ⚽📊💎
