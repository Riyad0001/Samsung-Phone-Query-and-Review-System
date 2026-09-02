"""
Conversational chatbot using RAG + open-source LLM.
"""
import re
from chatbot.query_engine import PhoneQueryEngine


class SamsungChatbot:
    def __init__(self, llm_pipeline=None, embedder=None):
        self.llm = llm_pipeline
        self.engine = PhoneQueryEngine(embedding_model=embedder)

    def initialize(self):
        self.engine.build_index()

    def _extract_phone_name(self, query):
        """Extract likely phone model name from a natural language query."""
        known_models = [
            "Galaxy S24 Ultra", "Galaxy S24 Plus", "Galaxy S24+", "Galaxy S24",
            "Galaxy S23 Ultra", "Galaxy S23 Plus", "Galaxy S23+", "Galaxy S23",
            "Galaxy S22 Ultra", "Galaxy S22 Plus", "Galaxy S22+", "Galaxy S22",
            "Galaxy S21 Ultra", "Galaxy S21 Plus", "Galaxy S21+", "Galaxy S21",
            "Galaxy A54", "Galaxy A34", "Galaxy Z Fold5", "Galaxy Z Fold 5",
        ]
        q_lower = query.lower()
        # Find all matching models
        matches = []
        for model in known_models:
            if model.lower() in q_lower:
                matches.append(model)
        if not matches:
            return query
        # If multiple matches, prefer the longest match (most specific)
        matches.sort(key=len, reverse=True)
        # But if a non-qualified name (e.g. "Galaxy S23") appears WITHOUT the qualifier word (Ultra/Plus/+)
        # in the query, check if the user mentioned the qualifier
        best = matches[0]
        qualifiers = ["ultra", "plus", "fe", "5g"]
        has_qualifier = any(q in q_lower for q in qualifiers)
        # If the best match has a qualifier but the query doesn't mention it, try next match
        for m in matches:
            model_lower = m.lower()
            has_model_qualifier = any(q in model_lower for q in qualifiers)
            if has_model_qualifier and not has_qualifier:
                continue  # skip qualified models if user didn't mention qualifier
            return m
        return matches[0]
        # Fallback: try to match "Galaxy S\d+" or "Galaxy [A-Z]\w+"
        m = re.search(r"(Galaxy\s+\S+(?:\s+\S+)?)", q_lower, re.IGNORECASE)
        if m:
            return m.group(1)
        return query

    def _format_phone_summary(self, phone):
        lines = [
            f"Phone: {phone.name}",
            f"  Display: {phone.display_size} {phone.display_type} ({phone.resolution})",
            f"  Processor: {phone.processor}",
            f"  RAM: {phone.ram} | Storage: {phone.storage}",
            f"  Main Camera: {phone.main_camera}",
            f"  Selfie Camera: {phone.selfie_camera}",
            f"  Battery: {phone.battery}",
            f"  OS: {phone.os_version}",
            f"  Weight: {phone.weight}",
            f"  Price: {phone.price}",
        ]
        return "\n".join(lines)

    def _format_compare(self, p1, p2):
        lines = [
            f"COMPARISON: {p1.name} vs {p2.name}",
            f"{'Feature':<20} | {p1.name:<35} | {p2.name:<35}",
            f"{'-'*20}-+-{'-'*35}-+-{'-'*35}",
            f"{'Display':<20} | {p1.display_size:<35} | {p2.display_size:<35}",
            f"{'Processor':<20} | {p1.processor:<35} | {p2.processor:<35}",
            f"{'RAM':<20} | {p1.ram:<35} | {p2.ram:<35}",
            f"{'Storage':<20} | {p1.storage:<35} | {p2.storage:<35}",
            f"{'Main Camera':<20} | {p1.main_camera:<35} | {p2.main_camera:<35}",
            f"{'Battery':<20} | {p1.battery:<35} | {p2.battery:<35}",
            f"{'OS':<20} | {p1.os_version:<35} | {p2.os_version:<35}",
            f"{'Weight':<20} | {p1.weight:<35} | {p2.weight:<35}",
            f"{'Price':<20} | {p1.price:<35} | {p2.price:<35}",
        ]
        return "\n".join(lines)

    def answer_query(self, user_query):
        """Main entry point: parse query type and respond."""
        q = user_query.lower().strip()

        # Comparison queries
        if "compare" in q or "vs" in q:
            match = re.search(r"(?:compare|vs)\s+(.+?)\s+(?:and|vs|with|to)\s+(.+)", q, re.IGNORECASE)
            if not match:
                match = re.search(r"(.+?)\s+vs\s+(.+)", q, re.IGNORECASE)
            if match:
                n1, n2 = match.group(1).strip(), match.group(2).strip()
                # Extract clean names
                n1 = self._extract_phone_name(n1)
                n2 = self._extract_phone_name(n2)
                p1, p2 = self.engine.compare_phones(n1, n2)
                if p1 and p2:
                    return self._format_compare(p1, p2)
                elif p1:
                    return f"Found '{p1.name}' but couldn't find '{n2}'."
                elif p2:
                    return f"Found '{p2.name}' but couldn't find '{n1}'."
                else:
                    return f"Could not find phones matching '{n1}' or '{n2}'."

        # List all phones
        if "list" in q or "all phones" in q or "show all" in q:
            phones = self.engine.list_all_phones()
            if phones:
                names = "\n".join(f"  {i+1}. {p.name}" for i, p in enumerate(phones))
                return f"Samsung Phones in Database:\n{names}"
            return "No phones found in database."

        # Best battery / best camera / best performance queries
        if "best" in q:
            phones = self.engine.list_all_phones()
            if not phones:
                return "No phones available."
            if "battery" in q:
                best = max(phones, key=lambda p: int(re.search(r"(\d+)\s*mAh", p.battery or "0").group(1)) if re.search(r"(\d+)\s*mAh", p.battery or "0") else 0)
                return f"Best Battery Life: {best.name} ({best.battery})"
            if "camera" in q:
                best = max(phones, key=lambda p: int(re.search(r"(\d+)\s*MP", p.main_camera or "0").group(1)) if re.search(r"(\d+)\s*MP", p.main_camera or "0") else 0)
                return f"Best Camera: {best.name} ({best.main_camera[:80]}...)"
            perf_order = ["Snapdragon 8 Gen 3", "Snapdragon 8 Gen 2", "Snapdragon 8 Gen 1", "Snapdragon 888", "Exynos 1380", "Dimensity 1080"]
            best = max(phones, key=lambda p: next((i for i, chip in enumerate(perf_order) if chip in (p.processor or "")), len(perf_order)))
            return f"Best Performance: {best.name} ({best.processor})"

        # Extract phone name from query for targeted lookup
        phone_name = self._extract_phone_name(user_query)
        phone = self.engine.get_phone_by_name(phone_name)
        if phone:
            specs = self._format_phone_summary(phone)
            # Check if asking about specific attribute
            if "camera" in q:
                return f"Camera specs for {phone.name}:\n  Main Camera: {phone.main_camera}\n  Selfie Camera: {phone.selfie_camera}"
            if "display" in q or "screen" in q:
                return f"Display specs for {phone.name}:\n  Size: {phone.display_size}\n  Type: {phone.display_type}\n  Resolution: {phone.resolution}"
            if "battery" in q:
                return f"Battery specs for {phone.name}: {phone.battery}"
            if "processor" in q or "chip" in q or "performance" in q:
                return f"Processor for {phone.name}: {phone.processor}"
            if "price" in q or "cost" in q:
                return f"Price for {phone.name}: {phone.price}"
            return specs

        # Fallback: try RAG search
        results = self.engine.search(user_query, top_k=2)
        if results:
            return self._format_phone_summary(results[0])

        return "I couldn't find information matching your query. Try asking about specific phone models like 'Galaxy S23' or 'S24 Ultra'."