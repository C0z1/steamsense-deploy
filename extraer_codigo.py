import os

# ============================================================
# CONFIGURACION - Ajusta estas variables a tu proyecto
# ============================================================

RUTA_PROYECTO = "."

EXTENSIONES = [".py", ".tsx", ".ts", ".js", ".json", ".css"]

CARPETAS_IGNORAR = {
    "node_modules", "__pycache__", ".next", ".git",
    "dist", "build", ".venv", "venv", "env", "migrations"
}

ARCHIVOS_IGNORAR = {
    "package-lock.json", "yarn.lock", ".env", ".env.example",
    "diagnose_db.py",
}

ARCHIVO_SALIDA = "codigo_proyecto.txt"
MAX_LINEAS_POR_ARCHIVO = 1000  # Aumentado de 500

# ============================================================

def extraer_codigo():
    resultado = []
    archivos_procesados = 0
    archivos_omitidos = 0

    for raiz, carpetas, archivos in os.walk(RUTA_PROYECTO):
        carpetas[:] = [c for c in carpetas if c not in CARPETAS_IGNORAR and not c.startswith(".")]

        for archivo in sorted(archivos):
            if archivo in ARCHIVOS_IGNORAR:
                continue

            _, extension = os.path.splitext(archivo)
            if extension not in EXTENSIONES:
                continue

            ruta_completa = os.path.join(raiz, archivo)
            ruta_relativa = os.path.relpath(ruta_completa, RUTA_PROYECTO)

            try:
                with open(ruta_completa, "r", encoding="utf-8", errors="ignore") as f:
                    lineas = f.readlines()

                total_lineas = len(lineas)
                truncado = False

                if total_lineas > MAX_LINEAS_POR_ARCHIVO:
                    lineas = lineas[:MAX_LINEAS_POR_ARCHIVO]
                    truncado = True

                contenido = "".join(lineas)

                resultado.append(f"\n{'='*60}")
                resultado.append(f"ARCHIVO: {ruta_relativa}")
                resultado.append(f"LINEAS: {total_lineas}" + (" (TRUNCADO)" if truncado else ""))
                resultado.append(f"{'='*60}\n")
                resultado.append(contenido)

                if truncado:
                    resultado.append(f"\n... [Archivo truncado, {total_lineas - MAX_LINEAS_POR_ARCHIVO} lineas omitidas]")

                archivos_procesados += 1

            except Exception as e:
                archivos_omitidos += 1
                print(f"No se pudo leer: {ruta_relativa} -> {e}")

    encabezado = [
        "EXTRACCION DE CODIGO DEL PROYECTO",
        f"Archivos procesados: {archivos_procesados}",
        f"Archivos omitidos: {archivos_omitidos}",
        f"Extensiones incluidas: {', '.join(EXTENSIONES)}",
        "=" * 60 + "\n"
    ]

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(encabezado))
        f.write("\n".join(resultado))

    print(f"\n Listo! Archivo generado: {ARCHIVO_SALIDA}")
    print(f"   Archivos procesados: {archivos_procesados}")
    print(f"   Tamano: {os.path.getsize(ARCHIVO_SALIDA) / 1024:.1f} KB")

if __name__ == "__main__":
    extraer_codigo()