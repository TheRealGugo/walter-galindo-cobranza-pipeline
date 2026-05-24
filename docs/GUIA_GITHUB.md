# Guía rápida: Subir este proyecto a GitHub

## Prerrequisitos

1. Tener cuenta en https://github.com (si no, créala — es gratis)
2. Tener Git instalado: descarga en https://git-scm.com/download/win
3. Verificar instalación:
   ```bash
   git --version
   ```

## Configurar Git por primera vez (solo una vez en tu PC)

```bash
git config --global user.name "Walter Galindo"
git config --global user.email "walter.galindo.p@uni.pe"
```

---

## Paso 1: Crear el repo en GitHub

1. Entra a https://github.com/new
2. **Repository name**: `walter-galindo-cobranza-pipeline`
3. **Description**: `Pipeline ETL en Python para automatización de reportes de cobranza. Portafolio Analista Jr. Automatización de Procesos.`
4. **Public** (importante: el reclutador debe poder verlo sin login)
5. **NO marques** "Add README" ni ".gitignore" ni "license" (ya los tenemos locales)
6. Click en **Create repository**

GitHub te mostrará un comando que se ve así (CÓPIALO):
```
https://github.com/<TU_USUARIO>/walter-galindo-cobranza-pipeline.git
```

---

## Paso 2: Inicializar el repo local y subir

Desde la carpeta del proyecto, abre la terminal y ejecuta:

```bash
# 1. Inicializar Git en la carpeta
git init

# 2. Cambiar a rama main (estándar moderno)
git branch -M main

# 3. Agregar todos los archivos
git add .

# 4. Verificar qué se subirá (debe excluir data/input/*.xlsx)
git status

# 5. Primer commit
git commit -m "feat: pipeline ETL inicial de consolidacion de cobranza"

# 6. Conectar con GitHub (REEMPLAZA <TU_USUARIO>)
git remote add origin https://github.com/<TU_USUARIO>/walter-galindo-cobranza-pipeline.git

# 7. Subir
git push -u origin main
```

GitHub te pedirá usuario y contraseña. Para la contraseña usa un **Personal Access Token**:

### Crear Personal Access Token

1. https://github.com/settings/tokens
2. **Generate new token (classic)**
3. Nombre: `Mi laptop`
4. Expiration: `90 days`
5. Scopes: marca **repo** (todo el bloque)
6. **Generate** y copia el token
7. Cuando Git te pida password, pega ese token

---

## Paso 3: Activar GitHub Pages (opcional pero impactante)

Para que tu README se vea como una página web:

1. En tu repo, ve a **Settings** → **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `main` / `/ (root)`
4. **Save**

En 1 minuto tendrás una URL tipo:
```
https://<tu-usuario>.github.io/walter-galindo-cobranza-pipeline/
```

---

## Paso 4: Pulir el repo

### Agregar tópicos (importante para descubribilidad)

En tu repo, junto al nombre, click en el ⚙️ al lado de "About" y agrega:
- `python`
- `automation`
- `etl`
- `pandas`
- `rpa`
- `data-engineering`
- `process-automation`
- `peru`

### Pin del repo en tu perfil

1. Ve a tu perfil en https://github.com/<tu-usuario>
2. **Customize your pins**
3. Selecciona este proyecto
4. **Save pins**

Ahora aparece destacado en tu perfil.

---

## Paso 5: Link en LinkedIn

Agrega en tu CV de LinkedIn una sección **Featured / Destacado** con:
- Título: "Pipeline de Automatización de Cobranza — Python ETL"
- Descripción: 2-3 líneas
- Link al repo

---

## Comandos para actualizar el repo después

Cuando hagas cambios:

```bash
git add .
git commit -m "describe lo que cambiaste"
git push
```

---

## Tip de entrevista

Lleva el link impreso o en un QR. Cuando el reclutador pregunte "¿tienes algo que mostrar?" — abres el repo en pantalla y caminas por:

1. README (storytelling del problema)
2. PDD en docs/ (madurez metodológica)
3. Estructura del código en src/ (organización)
4. Tests pasando con `pytest -v` (calidad)
5. Reporte Excel final (output de negocio)

**Total: 5 minutos. Es la mejor demo posible para este puesto.**
