#!/usr/bin/env python3
"""Test the new logging system."""

import sys
sys.path.insert(0, '/Users/wahyuhidayat/Documents/Computer Science/Kuliah/semester-7/lexin/zito/hermes')

from src.utils.logger import setup_logging, HermesLogger

setup_logging(level="INFO")

citation_logger = HermesLogger("citation")
search_logger = HermesLogger("perpres_search")
consumer_logger = HermesLogger("consumer")

print("\n=== Testing New Logging Format ===\n")

citation_logger.info(
    "Citation processing complete",
    total_citations=20,
    valid_references=1,
    doc_ids="UU_24_2011"
)

search_logger.info("Search complete", hits=27, duration_ms=1523)

consumer_logger.info("Message processed successfully", session_uid="abc-123")

search_logger.debug("Elasticsearch query successful", total_hits=8)

search_logger.error("Search failed", error="Connection timeout")

print("\n=== Test Complete ===\n")
