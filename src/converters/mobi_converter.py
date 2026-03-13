import subprocess
from pathlib import Path
from .base_converter import BaseConverter
from .epub_converter import EpubConverter

class MobiConverter(BaseConverter):
    def convert(self, content, title="Generated Novel"):
        """Create a MOBI file from the content using ebook-convert (Calibre)"""
        try:
            # First, create the EPUB to use as a base
            epub_converter = EpubConverter(self.output_dir, self.config, self.cover_path)
            epub_path = epub_converter.convert(content, title)
            
            if not epub_path:
                print("Error: Could not create EPUB base for MOBI conversion.")
                return None
                
            mobi_filename = self.output_dir / f"{title.replace(' ', '_')}.mobi"
            
            print(f"Converting EPUB to MOBI for '{title}'...")
            # Use ebook-convert from Calibre
            try:
                # Include cover in the conversion command explicitly
                cmd = ['ebook-convert', epub_path, str(mobi_filename)]
                if self.cover_path and Path(self.cover_path).exists():
                    cmd.extend(['--cover', self.cover_path])
                
                # available at: https://manual.calibre-ebook.com/generated/en/ebook-convert.html
                cmd.extend(['--mobi-file-type', 'both'])
                cmd.extend(['--share-not-sync']) # Helps some Kindle versions
                
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                # Print conversion log if successful
                if result.stdout:
                    print("\n--- MOBI Conversion Log ---")
                    print(result.stdout)
                    print("--- End of MOBI Log ---\n")
                
                print(f"MOBI file saved at: {mobi_filename}")
                return str(mobi_filename)
            except subprocess.CalledProcessError as e:
                print(f"Error in ebook-convert: {e.stderr}")
                return None
            except FileNotFoundError:
                print("Error: 'ebook-convert' not found. Please install Calibre to support MOBI output.")
                return None
        except Exception as e:
            print(f"Error creating MOBI: {str(e)}")
            return None
