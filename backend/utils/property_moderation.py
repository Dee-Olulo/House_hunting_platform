# ============================================================================
# FILE 1: backend/utils/property_moderation.py
# ============================================================================
"""
Property Auto-Moderation System
Automatically reviews and scores property listings based on quality criteria
"""

from datetime import datetime
from typing import Dict, List, Tuple
import re

class PropertyModerator:
    """
    Auto-moderation system for property listings
    Uses rule-based scoring to approve, flag, or reject properties
    """
    
    def __init__(self):
        # Spam/scam keywords to detect
        self.spam_keywords = [
            'guaranteed', 'limited time', 'act now', 'free money',
            'click here', 'winner', 'congratulations', 'urgent',
            'make money fast', 'work from home', 'mlm', 'pyramid',
            'get rich', 'earn cash', 'no risk', '100% free'
        ]
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'\$\$\$+',  # Multiple dollar signs
            r'!!!+',     # Multiple exclamation marks
            r'www\.',    # Website URLs
            r'http',     # URLs
            r'\.com',    # Website domains
            r'\d{10,}',  # Long phone numbers in description
        ]
    
    def moderate_property(self, property_data: Dict) -> Tuple[str, int, List[str]]:
        """
        Main moderation function
        
        Returns:
            (status, score, issues)
            - status: 'approved', 'pending_review', 'rejected'
            - score: Quality score out of 100
            - issues: List of identified issues
        """
        score = 100  # Start with perfect score
        issues = []
        
        # Run all checks
        score, issues = self._check_images(property_data, score, issues)
        score, issues = self._check_videos(property_data, score, issues)
        score, issues = self._check_description(property_data, score, issues)
        score, issues = self._check_price(property_data, score, issues)
        score, issues = self._check_required_fields(property_data, score, issues)
        score, issues = self._check_spam(property_data, score, issues)
        score, issues = self._check_coordinates(property_data, score, issues)
        
        # Determine status based on score
        if score >= 80:
            status = 'approved'
        elif score >= 50:
            status = 'pending_review'
        else:
            status = 'rejected'
        
        return status, score, issues
    
    def _check_images(self, data: Dict, score: int, issues: List[str]) -> Tuple[int, List[str]]:
        """Check image quality and quantity"""
        images = data.get('images', [])
        
        if not images or len(images) == 0:
            score -= 40
            issues.append("No images provided (critical)")
        elif len(images) < 3:
            score -= 20
            issues.append(f"Only {len(images)} images (minimum 3 recommended)")
        elif len(images) >= 5:
            score += 5  # Bonus for good coverage
        
        if len(images) > 20:
            score -= 10
            issues.append("Too many images (max 20)")
        
        return score, issues
    
    def _check_videos(self, data: Dict, score: int, issues: List[str]) -> Tuple[int, List[str]]:
        """Check video presence (optional but bonus)"""
        videos = data.get('videos', [])
        
        if videos and len(videos) > 0:
            score += 10  # Bonus for having videos
            if len(videos) > 5:
                score -= 5
                issues.append("Too many videos (max 5)")
        
        return score, issues
    
    def _check_description(self, data: Dict, score: int, issues: List[str]) -> Tuple[int, List[str]]:
        """Check description quality"""
        description = data.get('description', '')
        
        if not description:
            score -= 30
            issues.append("No description provided")
            return score, issues
        
        desc_len = len(description)
        
        if desc_len < 50:
            score -= 25
            issues.append(f"Description too short ({desc_len} chars, min 50)")
        elif desc_len < 100:
            score -= 10
            issues.append("Description is brief (100+ chars recommended)")
        elif desc_len >= 200:
            score += 5  # Bonus for detailed description
        
        # Check for meaningful content (not just repeated characters)
        if len(set(description.lower())) < 20:
            score -= 20
            issues.append("Description lacks variety (possible spam)")
        
        return score, issues
    
    def _check_price(self, data: Dict, score: int, issues: List[str]) -> Tuple[int, List[str]]:
        """Check price reasonableness"""
        price = data.get('price')
        
        if not price or price <= 0:
            score -= 30
            issues.append("Invalid price")
            return score, issues
        
        # Price anomaly detection (basic)
        if price < 1000:
            score -= 25
            issues.append(f"Suspiciously low price: KES {price}")
        elif price > 1000000:
            score -= 15
            issues.append(f"Very high price: KES {price} (requires verification)")
        elif price < 5000:
            score -= 10
            issues.append("Price below typical range")
        
        return score, issues
    
    def _check_required_fields(self, data: Dict, score: int, issues: List[str]) -> Tuple[int, List[str]]:
        """Check if all required fields are present"""
        required_fields = {
            'title': 'Title',
            'address': 'Address',
            'city': 'City',
            'bedrooms': 'Bedrooms',
            'bathrooms': 'Bathrooms'
        }
        
        missing_count = 0
        for field, label in required_fields.items():
            if not data.get(field):
                score -= 8
                issues.append(f"Missing {label}")
                missing_count += 1
        
        if missing_count >= 3:
            score -= 10
            issues.append("Multiple required fields missing")
        
        return score, issues
    
    def _check_spam(self, data: Dict, score: int, issues: List[str]) -> Tuple[int, List[str]]:
        """Detect spam/scam indicators"""
        title = data.get('title', '').lower()
        description = data.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Check for spam keywords
        found_keywords = []
        for keyword in self.spam_keywords:
            if keyword in combined_text:
                found_keywords.append(keyword)
        
        if found_keywords:
            penalty = min(len(found_keywords) * 15, 50)  # Max 50 point penalty
            score -= penalty
            issues.append(f"Suspicious keywords detected: {', '.join(found_keywords[:3])}")
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, combined_text):
                score -= 10
                issues.append(f"Suspicious pattern detected in text")
                break
        
        # Check for excessive capitalization
        if title and sum(1 for c in title if c.isupper()) > len(title) * 0.5:
            score -= 15
            issues.append("Excessive capitalization in title")
        
        return score, issues
    
    def _check_coordinates(self, data: Dict, score: int, issues: List[str]) -> Tuple[int, List[str]]:
        """Check location coordinates"""
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            score -= 5
            issues.append("No location coordinates provided")
        else:
            # Bonus for having coordinates
            score += 5
        
        return score, issues
    
    def get_moderation_summary(self, status: str, score: int, issues: List[str]) -> Dict:
        """Generate human-readable moderation summary"""
        if status == 'approved':
            message = "Property approved automatically"
            action_required = False
        elif status == 'pending_review':
            message = "Property flagged for manual review"
            action_required = True
        else:  # rejected
            message = "Property rejected - please fix issues and resubmit"
            action_required = True
        
        return {
            'status': status,
            'score': score,
            'message': message,
            'action_required': action_required,
            'issues': issues,
            'moderated_at': datetime.utcnow().isoformat()
        }



