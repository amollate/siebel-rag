import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SiebelDocParser:
    def __init__(self):
        self.section_headers = [
            "about", "architecture", "configuration", "installation",
            "tutorial", "guide", "fundamentals", "components", "modules",
            "security", "integration", "deployment", "performance",
            "best practices", "workflow", "business service", "object",
            "data model", "user interface", "open ui", "siebel tools",
            "business object", "business component", "applet", "view",
            "screen", "responsibility", "position", "profile",
        ]

    def detect_sections(self, text):
        lines = text.split("\n")
        sections = []
        current_section = {"title": "Introduction", "lines": []}

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            is_header = False
            for header in self.section_headers:
                if stripped.lower().startswith(header) and len(stripped) < 120:
                    is_header = True
                    break

            if is_header and len(current_section["lines"]) > 0:
                sections.append(current_section)
                current_section = {"title": stripped, "lines": []}
            else:
                current_section["lines"].append(stripped)

        if current_section["lines"]:
            sections.append(current_section)

        return sections

    def parse_metadata(self, url, content):
        parsed = urlparse(url)
        domain = parsed.netloc

        source_map = {
            "docs.oracle.com": "Oracle Official Documentation",
            "www.cleverence.com": "Cleverence Siebel Guide",
            "www.acte.in": "ACTE Siebel Tutorial",
            "www.aired.in": "Aired Siebel Tutorials",
            "www.slideshare.net": "SlideShare Siebel Training",
            "www.a10networks.com": "A10 Networks Deployment Guide",
            "www.scribd.com": "Scribd Document",
            "www.gologica.com": "GoLogica Training",
            "thegreatcrm.com": "The Great CRM",
            "crmcog.com": "CRMCog Architecture",
        }

        source_name = source_map.get(domain, "Unknown Source")

        return {
            "url": url,
            "source": source_name,
            "domain": domain,
            "content_length": len(content),
        }

    def parse(self, documents):
        parsed = []
        for doc in documents:
            url = doc["url"]
            content = doc["content"]
            metadata = self.parse_metadata(url, content)
            sections = self.detect_sections(content)

            for section in sections:
                section_text = "\n".join(section["lines"])
                parsed.append({
                    "url": url,
                    "source": metadata["source"],
                    "section_title": section["title"],
                    "content": section_text,
                    "content_length": len(section_text),
                })

        logger.info("Parsed %d documents into %d sections.", len(documents), len(parsed))
        return parsed