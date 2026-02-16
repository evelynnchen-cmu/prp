import re
import json
from typing import Dict, List

class StructuredCitationGenerator:
    """Generate validated citations with reference list"""
    
    def __init__(self, manifest_path: str = "data/data_manifest.json"):
        with open(manifest_path, 'r') as f:
            self.manifest = json.load(f)
        # Create lookup dict by id
        self.manifest_dict = {item['id']: item for item in self.manifest}
        
    def enhance_answer(self, result: Dict) -> Dict:
        """
        Add citation validation and reference list
        
        Returns enhanced result with:
        - citation_validation_passed (bool)
        - invalid_citations (list)
        - reference_list (str)
        """
        answer = result['answer']
        chunks = result['retrieved_chunks']
        
        # Extract citations
        citations = self._extract_citations(answer)
        
        # Validate citations
        chunk_ids = {c['chunk_id'] for c in chunks}
        invalid = []
        
        for cit in citations:
            match = re.search(r'\(([^,]+),\s*([^)]+)\)', cit)
            if match:
                chunk_id = match.group(2).strip()
                if chunk_id not in chunk_ids:
                    invalid.append(cit)
        
        # Generate reference list
        source_ids = set()
        for cit in citations:
            match = re.search(r'\(([^,]+)', cit)
            if match:
                source_ids.add(match.group(1))
        
        reference_list = self._build_references(source_ids)
        
        return {
            **result,
            'enhanced': True,
            'citation_validation_passed': len(invalid) == 0,
            'invalid_citations': invalid,
            'reference_list': reference_list,
            'num_unique_sources': len(source_ids)
        }
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract all citations from text"""
        pattern = r'\(([a-z0-9_]+),\s*([a-z0-9_]+)\)'
        matches = re.findall(pattern, text)
        return [f"({m[0]}, {m[1]})" for m in matches]
    
    def _build_references(self, source_ids: set) -> str:
        """Build formatted reference list"""
        refs = []
        
        for source_id in sorted(source_ids):
            if source_id in self.manifest_dict:
                item = self.manifest_dict[source_id]
                venue = item.get('venue', 'Various')
                refs.append(
                    f"{source_id}: {item['authors']} ({item['year']}). "
                    f"{item['title']}. {venue}. {item['link_or_DOI']}"
                )
        
        return "\n".join(refs)
