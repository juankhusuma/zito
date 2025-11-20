from __future__ import annotations

import dataclasses
import re
from typing import Dict, List


CITATION_PATTERN = re.compile(
    r"(?:\[{1,2}(?P<number>\d+)\]{1,2}\((?:https://chat\.lexin\.cs\.ui\.ac\.id/details/)?(?P<doc_id>[^)]+)\))|(?:\((?P<doc_id_simple>[^)]+)\))"
)


@dataclasses.dataclass
class Citation:
    number: int
    doc_id: str
    url: str
    start: int
    end: int


class CitationProcessor:
    """Utility for parsing LLM-generated citation markdown.

    Tahap 1: hanya fokus ke ekstraksi citation dari text.
    """

    def __init__(self) -> None:
        self.pattern = CITATION_PATTERN

    def extract_citations(self, text: str) -> List[Citation]:
        """Extract all citations of form [[N]](https://chat.lexin.cs.ui.ac.id/details/{doc_id}) or (doc_id).

        Returns a list of Citation objects with number, doc_id, full url, and
        position (start/end index in the original text).
        """

        citations: List[Citation] = []
        for match in self.pattern.finditer(text):
            # Check which group matched
            doc_id = match.group("doc_id")
            number_str = match.group("number")

            if doc_id:
                # Standard format: [[N]](url)
                try:
                    number = int(number_str)
                except ValueError:
                    continue
            else:
                # Simple format: (doc_id)
                doc_id = match.group("doc_id_simple")
                # Assign dummy number 0, will be renumbered anyway
                number = 0

            if not doc_id:
                continue

            # Clean up doc_id if it contains URL parts (just in case)
            if "/details/" in doc_id:
                doc_id = doc_id.split("/details/")[-1]

            url = f"https://chat.lexin.cs.ui.ac.id/details/{doc_id}"
            
            citations.append(
                Citation(
                    number=number,
                    doc_id=doc_id,
                    url=url,
                    start=match.start(),
                    end=match.end(),
                )
            )

        return citations

    def build_citation_map(self, citations: List[Citation]) -> Dict[str, int]:
        """Build mapping doc_id -> canonical citation number.

        Rules:
        - Dokumen pertama yang muncul mendapatkan nomor 1, berikutnya 2, dst.
        - Jika LLM memberi beberapa nomor berbeda untuk doc_id yang sama,
          kita abaikan dan pakai nomor pertama yang kita tetapkan.
        """

        citation_map: Dict[str, int] = {}
        current_number = 1

        for citation in citations:
            doc_id = citation.doc_id
            if doc_id not in citation_map:
                citation_map[doc_id] = current_number
                current_number += 1

        return citation_map

    def renumber_citations(self, text: str, citation_map: Dict[str, int]) -> str:
        """Return new text where all citation numbers are normalized.

        Nomor di dalam [[N]](...) akan diganti dengan nomor dari citation_map
        berdasarkan doc_id yang muncul di URL.
        """

        if not citation_map:
            return text

        def _replace(match: re.Match) -> str:
            doc_id = match.group("doc_id") or match.group("doc_id_simple")
            
            if not doc_id:
                return match.group(0)

            if "/details/" in doc_id:
                doc_id = doc_id.split("/details/")[-1]

            # Jika doc_id tidak ada di map (edge case), biarkan apa adanya.
            new_number = citation_map.get(doc_id)
            if new_number is None:
                return match.group(0)
            return f"[[{new_number}]](https://chat.lexin.cs.ui.ac.id/details/{doc_id})"

        return self.pattern.sub(_replace, text)

    def validate_citations(
        self,
        citations: List[Citation],
        retrieved_docs: List[dict],
    ) -> List[Citation]:
        """Filter out citations whose doc_id is not in retrieved_docs.

        This enforces the "no hallucinations" rule: we only allow citations
        to documents that actually appear in the retrieval results.
        """

        if not citations or not retrieved_docs:
            return []

        valid_ids = {str(doc.get("_id")) for doc in retrieved_docs if doc.get("_id") is not None}
        return [c for c in citations if c.doc_id in valid_ids]

    def build_reference_list(
        self,
        citation_map: Dict[str, int],
        retrieved_docs: List[dict],
    ) -> List[dict]:
        """Build a clean reference list from citation_map and retrieved_docs.

        Only includes documents that are actually cited (present in citation_map),
        sorted by citation number. Each entry is a simple dict containing the
        number, doc_id, url, and basic metadata fields if available.
        """

        if not citation_map or not retrieved_docs:
            return []

        # Index retrieved docs by their _id as string for easy lookup.
        docs_by_id: Dict[str, dict] = {}
        for doc in retrieved_docs:
            doc_id = str(doc.get("_id")) if doc.get("_id") is not None else None
            if doc_id is not None:
                docs_by_id[doc_id] = doc

        references: List[dict] = []
        for doc_id, number in sorted(citation_map.items(), key=lambda item: item[1]):
            doc = docs_by_id.get(doc_id)
            if doc is None:
                # Edge case: citation_map berisi doc_id yang tidak ada di retrieved_docs.
                # Untuk menjaga invariant "no phantom references", kita skip.
                continue

            metadata = (
                doc.get("_source", {}).get("metadata")
                or doc.get("metadata")
                or doc.get("source", {}).get("metadata")
                or {}
            )
            title = metadata.get("Judul") or metadata.get("title") or ""

            references.append(
                {
                    "number": number,
                    "doc_id": doc_id,
                    "title": title,
                    "url": f"https://chat.lexin.cs.ui.ac.id/details/{doc_id}",
                }
            )

        return references

    def process(self, llm_output: str, retrieved_docs: List[dict]) -> dict:
        """High-level helper: clean LLM output and build references.

        This wires together extraction, validation, numbering, renumbering,
        and reference list building into a single call.
        """

        # 1. Extract citations from raw text
        citations = self.extract_citations(llm_output)

        # 2. Validate citations against retrieval results
        valid_citations = self.validate_citations(citations, retrieved_docs)

        # 3. Build citation map (doc_id -> number)
        citation_map = self.build_citation_map(valid_citations)

        # 4. Renumber citations in text
        cleaned_content = self.renumber_citations(llm_output, citation_map)

        # 5. Build reference list
        references = self.build_reference_list(citation_map, retrieved_docs)

        return {
            "content": cleaned_content,
            "references": references,
        }
