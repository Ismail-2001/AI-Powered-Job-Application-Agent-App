"""
RAG Engine (Retrieval-Augmented Generation)
Role: Store and retrieve relevant "experience snippets" to improve LLM precision and save tokens.
"""

import json
import re
from typing import List, Dict, Any

class RAGEngine:
    """
    A lightweight Retrieval Engine that breaks down the master profile into 
    searchable snippets and retrieves the most relevant ones.
    """

    def __init__(self, profile_path: str = "data/master_profile.json"):
        self.profile_path = profile_path
        self.snippets = []
        self._initialize_snippets()

    def _initialize_snippets(self):
        """Parse the profile into discrete experience snippets."""
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # 1. Standardize Experience Snippets
            for role in profile.get('experience', []):
                company = role.get('company', 'Unknown')
                title = role.get('title', 'Position')
                
                # Create a snippet for each achievement to allow granular retrieval
                for ach in role.get('achievements', role.get('responsibilities', [])):
                    self.snippets.append({
                        "content": ach,
                        "metadata": {
                            "type": "experience",
                            "company": company,
                            "title": title,
                            "dates": role.get('dates', '')
                        }
                    })
            
            # 2. Project Snippets
            for project in profile.get('projects', []):
                self.snippets.append({
                    "content": f"Project {project.get('name')}: {project.get('description')}",
                    "metadata": {"type": "project", "name": project.get('name')}
                })
                
            print(f"📊 RAG: Initialized with {len(self.snippets)} experience snippets.")
            
        except Exception as e:
            print(f"⚠️ RAG Initialization failed: {e}")

    def retrieve_relevant_experience(self, job_keywords: List[str], top_k: int = 15) -> List[Dict[str, Any]]:
        """
        Retrieve segments that match high-priority job keywords.
        Uses a frequency-based scoring (BM25 variant logic) for precision.
        """
        scored_snippets = []
        
        for snippet in self.snippets:
            score = 0
            content_lower = snippet['content'].lower()
            
            for kw in job_keywords:
                # Weighted score: exact matches in snippets are high value
                if re.search(rf'\b{re.escape(kw.lower())}\b', content_lower):
                    score += 2
                elif kw.lower() in content_lower:
                    score += 1
            
            if score > 0:
                scored_snippets.append((score, snippet))
        
        # Sort by score descending
        scored_snippets.sort(key=lambda x: x[0], reverse=True)
        
        # Return top K
        results = [s[1] for s in scored_snippets[:top_k]]
        print(f"🎯 RAG: Retrieved {len(results)} relevant snippets for customization.")
        return results
