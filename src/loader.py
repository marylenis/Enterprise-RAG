from llama_index.core import SimpleDirectoryReader
import os

def get_directory_reader(directory_path: str):
    """
    Configures SimpleDirectoryReader to read PDF, Markdown, and Office files.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        
    return SimpleDirectoryReader(
        input_dir=directory_path,
        recursive=True,
        required_exts=[".pdf", ".md", ".docx", ".xlsx", ".txt", ".json"],
    )

if __name__ == "__main__":
    # Test loader with the data folder
    data_path = os.path.join(os.getcwd(), "data")
    reader = get_directory_reader(data_path)
    print(f"Lector configurado para la carpeta: {data_path}")
    print(f"Formatos soportados: {reader.required_exts}")
