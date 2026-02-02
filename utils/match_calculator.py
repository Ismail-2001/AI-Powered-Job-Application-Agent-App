"""
Match Score Calculator Utility
Role: Calculate how well a candidate profile matches a job description.
"""

from typing import Dict, Any, List, Set
import re

class MatchCalculator:
    """
    Calculates match scores between candidate profiles and job requirements.
    """
    
    def __init__(self):
        """Initialize the match calculator."""
        pass
    
    def calculate_match_score(
        self, 
        profile: Dict[str, Any], 
        job_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score between profile and job.
        
        Args:
            profile: Candidate's master profile
            job_analysis: Analyzed job requirements
            
        Returns:
            Dictionary with match scores and detailed breakdown
        """
        # Extract data
        required_skills = set(
            skill.lower() 
            for skill in job_analysis.get('requirements', {}).get('must_have_skills', [])
        )
        nice_to_have_skills = set(
            skill.lower() 
            for skill in job_analysis.get('requirements', {}).get('nice_to_have_skills', [])
        )
        ats_keywords = set(
            keyword.lower() 
            for keyword in job_analysis.get('keywords', {}).get('ats_keywords', [])
        )
        
        # Extract candidate skills
        candidate_skills = self._extract_candidate_skills(profile)
        candidate_keywords = self._extract_keywords_from_profile(profile)
        
        # Calculate matches
        required_matches = self._count_matches(required_skills, candidate_skills)
        nice_to_have_matches = self._count_matches(nice_to_have_skills, candidate_skills)
        keyword_matches = self._count_matches(ats_keywords, candidate_keywords)
        
        # Calculate scores
        required_score = (
            (required_matches / len(required_skills) * 100) 
            if required_skills else 100
        )
        nice_to_have_score = (
            (nice_to_have_matches / len(nice_to_have_skills) * 50) 
            if nice_to_have_skills else 0
        )
        keyword_score = (
            (keyword_matches / len(ats_keywords) * 30) 
            if ats_keywords else 0
        )
        
        # Overall score (weighted)
        overall_score = min(100, required_score + nice_to_have_score + keyword_score)
        
        # Missing skills
        missing_required = required_skills - candidate_skills
        missing_nice_to_have = nice_to_have_skills - candidate_skills
        
        return {
            'overall_score': round(overall_score, 1),
            'required_skills_score': round(required_score, 1),
            'nice_to_have_score': round(nice_to_have_score, 1),
            'keyword_score': round(keyword_score, 1),
            'required_skills_matched': required_matches,
            'required_skills_total': len(required_skills),
            'nice_to_have_matched': nice_to_have_matches,
            'nice_to_have_total': len(nice_to_have_skills),
            'keywords_matched': keyword_matches,
            'keywords_total': len(ats_keywords),
            'missing_required_skills': list(missing_required)[:10],  # Top 10
            'missing_nice_to_have_skills': list(missing_nice_to_have)[:10],
            'recommendations': self._generate_recommendations(
                overall_score, 
                missing_required, 
                missing_nice_to_have
            )
        }
    
    def _extract_candidate_skills(self, profile: Dict[str, Any]) -> Set[str]:
        """Extract all skills from candidate profile."""
        skills_set = set()
        
        # From skills section
        skills_data = profile.get('skills', {})
        if isinstance(skills_data, dict):
            for category, skill_list in skills_data.items():
                if isinstance(skill_list, list):
                    skills_set.update(skill.lower() for skill in skill_list)
        elif isinstance(skills_data, list):
            skills_set.update(skill.lower() for skill in skills_data)
        
        # From experience descriptions
        for exp in profile.get('experience', []):
            responsibilities = exp.get('responsibilities', []) + exp.get('achievements', [])
            for resp in responsibilities:
                # Extract potential skills (simple keyword extraction)
                words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', resp)
                skills_set.update(word.lower() for word in words if len(word) > 3)
        
        return skills_set
    
    def _extract_keywords_from_profile(self, profile: Dict[str, Any]) -> Set[str]:
        """Extract keywords from profile text."""
        keywords = set()
        
        # From summary
        summary = profile.get('summary', '')
        keywords.update(word.lower() for word in summary.split() if len(word) > 4)
        
        # From experience
        for exp in profile.get('experience', []):
            text = ' '.join(exp.get('responsibilities', []) + exp.get('achievements', []))
            keywords.update(word.lower() for word in text.split() if len(word) > 4)
        
        return keywords
    
    def _count_matches(self, required: Set[str], candidate: Set[str]) -> int:
        """Count how many required items match candidate items (fuzzy matching)."""
        matches = 0
        
        for req_item in required:
            # Exact match
            if req_item in candidate:
                matches += 1
                continue
            
            # Partial match (word-level)
            req_words = set(req_item.split())
            for cand_item in candidate:
                cand_words = set(cand_item.split())
                # If significant overlap
                if req_words & cand_words:
                    matches += 1
                    break
        
        return matches
    
    def _generate_recommendations(
        self, 
        score: float, 
        missing_required: Set[str], 
        missing_nice_to_have: Set[str]
    ) -> List[str]:
        """Generate actionable recommendations based on match score."""
        recommendations = []
        
        if score < 50:
            recommendations.append("⚠️  Low match score. Consider applying to roles better aligned with your skills.")
        
        if missing_required:
            recommendations.append(f"📝 Add these required skills to your profile: {', '.join(list(missing_required)[:5])}")
        
        if missing_nice_to_have:
            recommendations.append(f"💡 Consider highlighting these nice-to-have skills: {', '.join(list(missing_nice_to_have)[:5])}")
        
        if score >= 70:
            recommendations.append("✅ Strong match! Your profile aligns well with this role.")
        
        if not recommendations:
            recommendations.append("✅ Excellent match! You have all the key requirements.")
        
        return recommendations
    
    def print_match_report(self, match_data: Dict[str, Any]) -> None:
        """Print a formatted match score report."""
        print("\n" + "=" * 60)
        print("📊 MATCH SCORE ANALYSIS")
        print("=" * 60)
        
        print(f"\n🎯 Overall Match Score: {match_data['overall_score']}/100")
        
        print(f"\n📋 Required Skills:")
        print(f"   Matched: {match_data['required_skills_matched']}/{match_data['required_skills_total']}")
        print(f"   Score: {match_data['required_skills_score']}/100")
        
        print(f"\n⭐ Nice-to-Have Skills:")
        print(f"   Matched: {match_data['nice_to_have_matched']}/{match_data['nice_to_have_total']}")
        print(f"   Score: {match_data['nice_to_have_score']}/50")
        
        print(f"\n🔑 Keywords:")
        print(f"   Matched: {match_data['keywords_matched']}/{match_data['keywords_total']}")
        print(f"   Score: {match_data['keyword_score']}/30")
        
        if match_data['missing_required_skills']:
            print(f"\n❌ Missing Required Skills:")
            for skill in match_data['missing_required_skills']:
                print(f"   • {skill.title()}")
        
        print(f"\n💡 Recommendations:")
        for rec in match_data['recommendations']:
            print(f"   {rec}")
        
        print("\n" + "=" * 60)
