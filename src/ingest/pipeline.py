import json
from pathlib import Path
from .pdf_parser import PDFParser
from .chunker import TextChunker

class IngestionPipeline:
    """Process all PDFs in manifest"""
    
    def __init__(self, manifest_path: str = "data/data_manifest.json"):
        with open(manifest_path, 'r') as f:
            self.manifest = json.load(f)
        self.chunker = TextChunker(chunk_size=512, overlap=128)
        
    def run(self):
        """Process all sources and save outputs"""
        all_chunks = []
        stats = {'total_sources': 0, 'total_chunks': 0, 'errors': []}
        
        for item in self.manifest:
            source_id = item['id']
            raw_path = f"data/raw/{source_id}.pdf"
            print(f"Processing {source_id}...")
            
            try:
                # Parse PDF
                parser = PDFParser(raw_path)
                text = parser.extract_text()
                
                # Save processed text
                processed_path = f"data/processed/{source_id}.txt"
                Path(processed_path).parent.mkdir(parents=True, exist_ok=True)
                with open(processed_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                # Chunk text
                chunks = self.chunker.chunk_text(text, source_id)
                all_chunks.extend(chunks)
                
                stats['total_sources'] += 1
                print(f"  → {len(chunks)} chunks created")
                
            except Exception as e:
                error_msg = f"Error processing {source_id}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
        
        # Save all chunks to JSONL
        chunks_path = "data/processed/chunks.jsonl"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk) + '\n')
        
        stats['total_chunks'] = len(all_chunks)
        
        # Generate report
        self._save_report(stats)
        
        print(f"\n✓ Ingestion complete")
        print(f"  Sources: {stats['total_sources']}")
        print(f"  Chunks: {stats['total_chunks']}")
        print(f"  Avg chunks/source: {stats['total_chunks'] / stats['total_sources']:.1f}")
        
    def _save_report(self, stats: dict):
        """Save ingestion statistics"""
        report_path = "data/processed/ingestion_report.txt"
        with open(report_path, 'w') as f:
            f.write(f"INGESTION REPORT\n")
            f.write(f"================\n\n")
            f.write(f"Total sources processed: {stats['total_sources']}\n")
            f.write(f"Total chunks created: {stats['total_chunks']}\n")
            f.write(f"Average chunks per source: {stats['total_chunks'] / max(stats['total_sources'], 1):.1f}\n\n")
            
            if stats['errors']:
                f.write(f"Errors encountered:\n")
                for err in stats['errors']:
                    f.write(f"  - {err}\n")

if __name__ == "__main__":
    pipeline = IngestionPipeline()
    pipeline.run()
