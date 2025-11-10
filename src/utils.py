import base64

def limpiar_json_markdown(texto: str) -> str:
    texto = texto.strip()
    if texto.startswith("```"):
        lineas = texto.splitlines()
        lineas = [l for l in lineas if not l.strip().startswith("```")]
        texto = "\n".join(lineas).strip()
    return texto
