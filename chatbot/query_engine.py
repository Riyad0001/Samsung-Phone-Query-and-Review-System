"""
RAG-based query engine for Samsung phone data.
Uses sentence-transformers for embedding and FAISS for similarity search.
"""
import numpy as np
from database import get_session, Phone


class PhoneQueryEngine:
    def __init__(self, embedding_model=None):
        self.embedder = embedding_model
        self._phone_texts = []
        self._phone_ids = []
        self._index = None

    def build_index(self):
        """Build or rebuild the FAISS index from DB."""
        session = get_session()
        phones = session.query(Phone).all()
        session.close()

        self._phone_ids = []
        self._phone_texts = []

        for phone in phones:
            text = (
                f"Name: {phone.name}. "
                f"Display: {phone.display_size} {phone.display_type}, {phone.resolution}. "
                f"Processor: {phone.processor}. "
                f"RAM: {phone.ram}. Storage: {phone.storage}. "
                f"Main Camera: {phone.main_camera}. Selfie Camera: {phone.selfie_camera}. "
                f"Battery: {phone.battery}. OS: {phone.os_version}. "
                f"Weight: {phone.weight}. Dimensions: {phone.dimensions}. "
                f"Price: {phone.price}."
            )
            self._phone_ids.append(phone.id)
            self._phone_texts.append(text)

        if not self._phone_texts:
            print("[QueryEngine] No phones in DB to index.")
            return

        if self.embedder is not None:
            import faiss
            embeddings = self.embedder.encode(self._phone_texts, show_progress_bar=False)
            dimension = embeddings.shape[1]
            self._index = faiss.IndexFlatL2(dimension)
            self._index.add(np.array(embeddings).astype("float32"))
            print(f"[QueryEngine] Index built with {len(phones)} phones.")

    def search(self, query, top_k=3):
        """Search for phones matching the query."""
        if self._index is None or self.embedder is None:
            return []

        q_vec = self.embedder.encode([query], show_progress_bar=False)
        q_vec = np.array(q_vec).astype("float32")
        distances, indices = self._index.search(q_vec, top_k)

        results = []
        session = get_session()
        for idx in indices[0]:
            if idx < len(self._phone_ids):
                phone = session.query(Phone).filter_by(id=self._phone_ids[idx]).first()
                if phone:
                    results.append(phone)
        session.close()
        return results

    def get_phone_by_name(self, name_query):
        """Find phone by name, preferring exact matches."""
        session = get_session()
        # First try exact match
        phone = session.query(Phone).filter(Phone.name.ilike(name_query)).first()
        if not phone:
            # Then try starts with
            phone = session.query(Phone).filter(Phone.name.ilike(f"{name_query}%")).first()
        if not phone:
            # Then try contains, ordered by closest match
            phones = session.query(Phone).filter(Phone.name.ilike(f"%{name_query}%")).order_by(Phone.name).all()
            # Pick the one with shortest name (closest match)
            if phones:
                phone = min(phones, key=lambda p: len(p.name))
        session.close()
        return phone

    def list_all_phones(self):
        """Return all phones."""
        session = get_session()
        phones = session.query(Phone).all()
        session.close()
        return phones

    def compare_phones(self, name1, name2):
        """Compare two phones by name."""
        p1 = self.get_phone_by_name(name1)
        p2 = self.get_phone_by_name(name2)
        return p1, p2