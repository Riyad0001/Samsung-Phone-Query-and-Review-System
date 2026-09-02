"""
Multi-Agent System for Samsung Phone Queries.
Agent 1: SpecsAgent - retrieves specs from DB
Agent 2: ReviewAgent - generates reviews from specs
Orchestrator - coordinates both agents
"""
import re
from database import get_session, Phone


class SpecsAgent:
    """Retrieves detailed phone specifications from the database."""

    def retrieve_specs(self, phone_name):
        session = get_session()
        phone = session.query(Phone).filter(Phone.name.ilike(f"%{phone_name}%")).first()
        session.close()
        return phone

    def retrieve_all(self):
        session = get_session()
        phones = session.query(Phone).all()
        session.close()
        return phones

    def compare_specs(self, name1, name2):
        p1 = self.retrieve_specs(name1)
        p2 = self.retrieve_specs(name2)
        return p1, p2


class ReviewAgent:
    """Generates a detailed product review from specifications."""

    def generate_review(self, phone, llm=None):
        if not phone:
            return "No phone data available to generate a review."

        review = self._rule_based_review(phone)

        if llm is not None:
            try:
                prompt = (
                    f"Write a concise, helpful product review for the following Samsung phone.\n\n"
                    f"{review}\n\n"
                    f"Overall Review (2-3 sentences):"
                )
                llm_out = llm(prompt, max_new_tokens=100, do_sample=False)[0]["generated_text"]
                if "Overall Review:" in llm_out:
                    llm_out = llm_out.split("Overall Review:", 1)[1].strip()
                review += f"\n\n📝 AI-Generated Summary: {llm_out}"
            except Exception:
                pass

        return review

    def generate_comparison_review(self, p1, p2, llm=None):
        if not p1 or not p2:
            return "Cannot generate comparison: one or both phones not found."

        lines = [
            f"COMPARISON REVIEW: {p1.name} vs {p2.name}",
            "",
            f"─── {p1.name} ───",
            f"  Display: {p1.display_size} | Processor: {p1.processor} | RAM: {p1.ram}",
            f"  Camera: {p1.main_camera[:100] if p1.main_camera else 'N/A'}...",
            f"  Battery: {p1.battery} | Price: {p1.price}",
            "",
            f"─── {p2.name} ───",
            f"  Display: {p2.display_size} | Processor: {p2.processor} | RAM: {p2.ram}",
            f"  Camera: {p2.main_camera[:100] if p2.main_camera else 'N/A'}...",
            f"  Battery: {p2.battery} | Price: {p2.price}",
            "",
        ]
        p1_pros, p1_cons = self._pros_cons(p1)
        p2_pros, p2_cons = self._pros_cons(p2)
        lines.extend([f"Pros for {p1.name}: {p1_pros}", f"Cons for {p1.name}: {p1_cons}"])
        lines.extend([f"Pros for {p2.name}: {p2_pros}", f"Cons for {p2.name}: {p2_cons}"])
        lines.append("")
        p1_score = self._score(p1)
        p2_score = self._score(p2)
        if p1_score > p2_score:
            lines.append(f"Verdict: {p1.name} scores higher ({p1_score:.0f} vs {p2_score:.0f}).")
        elif p2_score > p1_score:
            lines.append(f"Verdict: {p2.name} scores higher ({p2_score:.0f} vs {p1_score:.0f}).")
        else:
            lines.append("Verdict: Both phones are evenly matched.")

        if llm is not None:
            try:
                cmp_text = "\n".join(lines)
                prompt = f"Based on this comparison:\n{cmp_text}\n\nWrite a 2-sentence summary recommendation:"
                llm_out = llm(prompt, max_new_tokens=80, do_sample=False)[0]["generated_text"]
                if "recommendation:" in llm_out:
                    llm_out = llm_out.split("recommendation:", 1)[1].strip()
                lines.append(f"\nAI Recommendation: {llm_out}")
            except Exception:
                pass

        return "\n".join(lines)

    def _rule_based_review(self, phone):
        pros, cons = self._pros_cons(phone)
        score = self._score(phone)
        rating = "5/5" if score >= 80 else "4/5" if score >= 60 else "3/5"
        review = [
            f"PRODUCT REVIEW: {phone.name}",
            f"Rating: {rating} ({score:.0f}/100)",
            "",
            f"─── Specifications ───",
            f"  Display: {phone.display_size} {phone.display_type}",
            f"  Resolution: {phone.resolution}",
            f"  Processor: {phone.processor}",
            f"  RAM: {phone.ram}",
            f"  Storage: {phone.storage}",
            f"  Main Camera: {phone.main_camera}",
            f"  Selfie Camera: {phone.selfie_camera}",
            f"  Battery: {phone.battery}",
            f"  OS: {phone.os_version}",
            f"  Weight: {phone.weight}",
            f"  Price: {phone.price}",
            "",
            f"Pros: {pros}",
            f"Cons: {cons}",
        ]
        return "\n".join(review)

    def _pros_cons(self, phone):
        pros = []
        cons = []
        if phone.display_size:
            try:
                size_val = float(phone.display_size.split()[0])
            except (ValueError, IndexError):
                size_val = 0
            if size_val >= 6.5:
                pros.append("Large immersive display")
            else:
                pros.append("Compact and portable design")
        if phone.processor:
            if "Snapdragon 8 Gen" in phone.processor:
                pros.append("Flagship-grade processor")
            elif "Exynos" in phone.processor:
                pros.append("Powerful Exynos chipset")
        if phone.battery:
            m = re.search(r"(\d+)", str(phone.battery))
            batt = int(m.group(1)) if m else 0
            if batt >= 5000:
                pros.append("Excellent battery life (5000mAh+)")
            elif batt < 4000:
                cons.append("Below average battery capacity")
            else:
                pros.append("Good battery capacity")
        if phone.main_camera:
            if "200" in phone.main_camera:
                pros.append("Industry-leading 200MP camera")
            elif "108" in phone.main_camera:
                pros.append("High-resolution 108MP camera")
        if phone.price:
            price_str = re.sub(r"[^\d]", "", str(phone.price))
            if price_str:
                price_val = int(price_str)
                if price_val >= 1500:
                    cons.append("Premium pricing")
                elif price_val <= 500:
                    pros.append("Great value for money")
        if not pros:
            pros.append("Solid build quality and Samsung ecosystem")
        if not cons:
            cons.append("No significant drawbacks at this price point")
        return "; ".join(pros), "; ".join(cons)

    def _score(self, phone):
        score = 50
        if phone.display_size:
            try:
                size_val = float(phone.display_size.split()[0])
            except (ValueError, IndexError):
                size_val = 0
            score += min(10, size_val * 1.5)
        if phone.processor:
            if "8 Gen 3" in phone.processor:
                score += 20
            elif "8 Gen 2" in phone.processor:
                score += 17
            elif "8 Gen 1" in phone.processor:
                score += 14
            elif "Snapdragon 888" in phone.processor:
                score += 10
            else:
                score += 5
        if phone.battery:
            m = re.search(r"(\d+)", str(phone.battery))
            batt = int(m.group(1)) if m else 0
            score += min(10, batt / 500)
        if phone.main_camera:
            if "200" in phone.main_camera:
                score += 10
            elif "108" in phone.main_camera:
                score += 8
            else:
                score += 5
        return min(100, score)


class AgentOrchestrator:
    """Coordinates SpecsAgent and ReviewAgent."""

    def __init__(self, llm=None):
        self.specs_agent = SpecsAgent()
        self.review_agent = ReviewAgent()
        self.llm = llm

    def handle_query(self, user_query):
        """Route query to appropriate agent workflow."""
        q = user_query.lower().strip()

        if "compare" in q or "vs" in q:
            match = re.search(r"(?:compare|vs)\s+(.+?)\s+(?:and|vs|with|to)\s+(.+)", q, re.IGNORECASE)
            if not match:
                match = re.search(r"(.+?)\s+vs\s+(.+)", q, re.IGNORECASE)
            if match:
                n1, n2 = match.group(1).strip(), match.group(2).strip()
                p1, p2 = self.specs_agent.compare_specs(n1, n2)
                return self.review_agent.generate_comparison_review(p1, p2, llm=self.llm)
            return "Could not parse comparison query."

        if "review" in q:
            phone_name = q.replace("review", "").replace("of", "").replace("for", "").strip()
            phone = self.specs_agent.retrieve_specs(phone_name)
            return self.review_agent.generate_review(phone, llm=self.llm)

        phone = self.specs_agent.retrieve_specs(q)
        if phone:
            return self.review_agent.generate_review(phone, llm=self.llm)
        return f"No phone found for '{user_query}'."