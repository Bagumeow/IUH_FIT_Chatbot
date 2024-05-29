from typing import Any, Union, List, Literal
from langchain_community.document_loaders import PyMuPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import dotenv

dotenv.load_dotenv()


class TextSplitter:
    def __init__(
        self,
        separators: Union[str, List[str]] = ["\n\n", "\n", " ", ""],
        chunk_size: int = 2000,
        chunk_overlap: int = 50,
    ):
        self.split_docs = RecursiveCharacterTextSplitter(
            separators=separators, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def __call__(self, documents):
        return self.split_docs.split_documents(documents)


class Loader:
    def __init__(
        self,
        file_type: str = Literal["pdf"],
        loader_cls: Any = PyMuPDFLoader,
        use_multithreading: bool = True,
        split_kwargs: dict = {
            "separators": ["\n\n", "\n", " ", ""],
            "chunk_size": 2000,
            "chunk_overlap": 50,
        },
    ):
        assert file_type in ["pdf"], f"File type must be pdf"
        self.file_type = file_type
        self.loader_cls = loader_cls
        self.use_multithreading = use_multithreading
        self.doc_splitter = TextSplitter(**split_kwargs)

    def load_pdf(
        self,
        pdf_files: Union[str],
    ):
        documents = PyMuPDFLoader.load_pdf(pdf_files)
        return documents

    def load_dir(self, dir_path: str):
        documents = DirectoryLoader(
            dir_path,
            glob=f"*.{self.file_type}",
            loader_cls=self.loader_cls,
            use_multithreading=self.use_multithreading,
        )
        return documents.load_and_split()


# if __name__ == "__main__":
#     loader = Loader(file_type = "pdf")
#     documents = loader.load_dir("./data/")
#     print(documents)
