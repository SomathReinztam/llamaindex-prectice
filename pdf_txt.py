import fitz

def extraer_texto_pdf(pdf_path, paginas_a_extraer=None):
    """
    Extrae texto de un archivo PDF de las páginas especificadas.
    
    Args:
        pdf_path (str): Ruta al archivo PDF
        paginas_a_extraer (list, optional): Lista de números de página a extraer (0-indexed).
                                           Si es None, extrae todas las páginas.
    
    Returns:
        str: Texto extraído de las páginas especificadas
    """
    try:
        # Paso 1: Abre el archivo PDF
        
        doc = fitz.open(pdf_path)
        # Si no se especifican páginas, extraer todas
        if paginas_a_extraer is None:
            paginas_a_extraer = list(range(len(doc)))
        
        # Paso 2: Extrae el texto de las páginas seleccionadas
        texto_total = ""
        for pagina_numero in paginas_a_extraer:
            pagina = doc.load_page(pagina_numero)  # Carga la página
            texto = pagina.get_text("text")  # Extrae el texto
            texto_total += texto + "\n"  # Agrega el texto a la cadena total
        
        # Cierra el documento
        doc.close()
        
        return texto_total
        
    except Exception as e:
        print(f"Error al procesar el PDF: {e}")
        raise e

