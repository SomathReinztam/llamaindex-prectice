from google import genai
from typing import Optional, List, Dict
import time
import google.genai.types as types

def create_file_search_store(display_name: str, client : genai.Client) -> genai.types.FileSearchStore:
    """
    Crea un nuevo File Search Store.

    Args:
        display_name: Nombre descriptivo para identificar el store

    Returns:
        FileSearchStore object con información del store creado
    """
    store = client.file_search_stores.create(
        config={'display_name': display_name}
    )

    print(f"✅ Store creado exitosamente")
    print(f"   • Nombre: {store.name}")
    print(f"   • Display Name: {display_name}")

    return store





# --------------------




def upload_file_to_store(
    client : genai.Client,
    file_path: str,
    store_name: str,
    display_name: Optional[str] = None,
    custom_metadata: Optional[List[Dict]] = None,
) -> bool:
    """
    Sube e indexa un archivo directamente en un File Search Store.

    Args:
        file_path: Ruta local al archivo
        store_name: Nombre del store (ej: 'fileSearchStores/abc123')
        display_name: Nombre para identificar el archivo (opcional)
        custom_metadata: Lista de metadatos personalizados (opcional)

    Returns:
        bool: True si la indexación fue exitosa
    """
    try:
        config = {}
        if display_name:
            config['display_name'] = display_name
        if custom_metadata:
            config['custom_metadata'] = custom_metadata

        print(f"📤 Subiendo: {file_path}...")

        # Iniciar la operación de upload
        operation = client.file_search_stores.upload_to_file_search_store(
            file=file_path,
            file_search_store_name=store_name,
            config=config if config else None
        )

        # Esperar a que la indexación complete
        print(f"⏳ Indexando (esto puede tomar algunos segundos)...")
        while not operation.done:
            time.sleep(5)
            operation = client.operations.get(operation)

        print(f"✅ Archivo indexado: {display_name or file_path}\n")
        return True

    except Exception as e:
        print(f"❌ Error indexando {file_path}: {str(e)}\n")
        return False
    





def batch_upload_files(
    file_paths: List[str],
    store_name: str,
    metadata_generator: Optional[callable] = None
) -> Dict[str, bool]:
    """
    Sube múltiples archivos de forma secuencial.

    Args:
        file_paths: Lista de rutas a archivos
        store_name: Nombre del store
        metadata_generator: Función que genera metadata para cada archivo

    Returns:
        Dict con el resultado de cada upload (filename: success_bool)
    """
    results = {}

    print(f"📦 Iniciando batch upload de {len(file_paths)} archivos...\n")

    for file_path in file_paths:
        metadata = metadata_generator(file_path) if metadata_generator else None

        success = upload_file_to_store(
            file_path=file_path,
            store_name=store_name,
            display_name=file_path,
            custom_metadata=metadata
        )

        results[file_path] = success

    # Resumen
    successful = sum(1 for v in results.values() if v)
    print(f"\n📊 Resumen: {successful}/{len(file_paths)} archivos indexados exitosamente")

    return results






def search_file_store(
    client : genai.Client,
    query: str,
    store_names: List[str],
    model: str = 'gemini-2.5-flash',
    metadata_filter: Optional[str] = None
) -> genai.types.GenerateContentResponse:
    """
    Realiza una búsqueda en uno o más File Search Stores.

    Args:
        query: Pregunta o consulta en lenguaje natural
        store_names: Lista de stores donde buscar
        model: Modelo de Gemini a usar (2.5-flash o 2.5-pro)
        metadata_filter: Filtro opcional de metadata

    Returns:
        Respuesta del modelo con el contenido generado
    """
    # Configurar la herramienta de File Search
    file_search_config = types.FileSearch(
        file_search_store_names=store_names
    )

    if metadata_filter:
        file_search_config.metadata_filter = metadata_filter

    # Hacer la consulta
    response = client.models.generate_content(
        model=model,
        contents=query,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    file_search=file_search_config
                )
            ]
        )
    )

    return response





def search_with_citations(
    client : genai.Client,
    query: str,
    store_names: List[str],
    show_full_chunks: bool = False
) -> None:
    """
    Realiza una búsqueda y muestra las citaciones de forma legible.

    Args:
        query: Pregunta en lenguaje natural
        store_names: Lista de stores donde buscar
        show_full_chunks: Si True, muestra el texto completo de cada chunk
    """
    print(f"❓ Pregunta: {query}\n")

    # Realizar búsqueda
    response = search_file_store(client, query, store_names)

    # Mostrar respuesta
    print(f"💬 Respuesta:\n{response.text}\n")
    print("=" * 80)

    # Obtener citaciones
    grounding = response.candidates[0].grounding_metadata

    if not grounding or not grounding.grounding_chunks:
        print("ℹ️  No hay citaciones disponibles para esta respuesta")
        return

    print(f"\n📖 CITACIONES ({len(grounding.grounding_chunks)} fuentes):\n")

    for i, chunk in enumerate(grounding.grounding_chunks, 1):
        context = chunk.retrieved_context

        print(f"[{i}] 📄 Fuente: {context.title}")

        if show_full_chunks:
            print(f"    Contenido:\n{context.text}\n")
        else:
            # Mostrar solo un extracto
            preview = context.text[:200] + "..." if len(context.text) > 200 else context.text
            print(f"    Extracto: {preview}\n")





def list_all_stores(client : genai.Client) -> List[genai.types.FileSearchStore]:
    """
    Lista todos los File Search Stores del usuario.

    Returns:
        Lista de FileSearchStore objects
    """
    stores = list(client.file_search_stores.list())

    print(f"📚 Tienes {len(stores)} store(s):\n")

    for i, store in enumerate(stores, 1):
        print(f"{i}. {store.display_name or 'Sin nombre'}")
        print(f"   • ID: {store.name}")
        print(f"   • Creado: {store.create_time}\n")

    return stores





def delete_store(client : genai.Client, store_name: str, confirm: bool = False) -> bool:
    """
    Elimina un File Search Store.

    ⚠️ ADVERTENCIA: Esta acción es IRREVERSIBLE.
    Se perderán todos los documentos indexados.

    Args:
        store_name: Nombre del store a eliminar
        confirm: Debe ser True para confirmar la eliminación

    Returns:
        bool: True si se eliminó exitosamente
    """
    if not confirm:
        print("⚠️  ADVERTENCIA: Debes pasar confirm=True para eliminar el store")
        print("   Esta acción es IRREVERSIBLE y eliminará todos los documentos indexados.")
        return False

    try:
        client.file_search_stores.delete(name=store_name, config={'force': True})
        print(f"✅ Store eliminado: {store_name}")
        return True

    except Exception as e:
        print(f"❌ Error eliminando store: {str(e)}")
        return False






def upload_with_custom_chunking(
    client : genai.Client,
    file_path: str,
    store_name: str,
    max_tokens_per_chunk: int = 500,
    max_overlap_tokens: int = 50
) -> bool:
    """
    Sube un archivo con configuración personalizada de chunking.

    Args:
        file_path: Ruta al archivo
        store_name: Nombre del store
        max_tokens_per_chunk: Máximo de tokens por chunk (default: 500)
        max_overlap_tokens: Tokens de overlap entre chunks (default: 50)

    Returns:
        bool: True si fue exitoso
    """
    try:
        print(f"📤 Subiendo con chunking personalizado:")
        print(f"   • Max tokens por chunk: {max_tokens_per_chunk}")
        print(f"   • Overlap: {max_overlap_tokens} tokens\n")

        operation = client.file_search_stores.upload_to_file_search_store(
            file=file_path,
            file_search_store_name=store_name,
            config={
                'display_name': file_path,
                'chunking_config': {
                    'white_space_config': {
                        'max_tokens_per_chunk': max_tokens_per_chunk,
                        'max_overlap_tokens': max_overlap_tokens
                    }
                }
            }
        )

        # Esperar indexación
        while not operation.done:
            time.sleep(5)
            operation = client.operations.get(operation)

        print(f"✅ Archivo indexado con chunking personalizado\n")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False