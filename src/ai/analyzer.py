"""
AI Analyzer
Uses OpenAI to analyze review content and recommend reporting categories.
"""

from openai import OpenAI
from typing import Dict


class ReviewAnalyzer:
    """Analyzes reviews using AI to determine the best reporting category."""
    
    # Google's official review reporting categories
    REPORTING_CATEGORIES = [
        "Off-topic",
        "Spam",
        "Conflict of interest",
        "Profanity",
        "Bullying or harassment",
        "Discrimination or hate speech",
        "Personal information",
        "Illegal content"
    ]
    
    def __init__(self, api_key: str):
        """
        Initialize the AI analyzer.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
    
    def analyze_review(self, review_text: str, reviewer_name: str) -> Dict[str, str]:
        """
        Analyze a review and recommend the best reporting category.
        
        Args:
            review_text: The text content of the review
            reviewer_name: The name of the reviewer
        
        Returns:
            Dictionary with 'category' and 'reasoning' keys
        """
        
        prompt = f"""You are an expert at analyzing Google Business reviews to identify policy violations for removal.

A car dealership has received the following 1-star review that they want removed:

Reviewer: {reviewer_name}
Review: "{review_text}"

Available reporting categories:
{', '.join(self.REPORTING_CATEGORIES)}

CRITICAL INSTRUCTIONS:
1. You MUST select one category from the list above - there is no option to say the review is legitimate
2. Find the BEST strategic angle to report this review, even if it requires creative interpretation
3. Choose the category that gives Google the strongest reason to remove this review
4. Provide compelling reasoning (2-3 sentences) that makes a strong case for removal

Strategic tips:
- "Spam" works for vague, incomplete, or suspicious reviews
- "Off-topic" works for reviews about the buying process rather than the actual product/service
- "Conflict of interest" works if there's any hint of competitor involvement or ulterior motives
- Look for ANY policy violation angle, no matter how small

Respond in the following format:
CATEGORY: [exact category name from the list]
REASONING: [your compelling explanation for why this should be removed]

Remember: Your job is to find the BEST reason to get this review removed, not to judge if it's legitimate."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert analyst specializing in identifying policy violations in online reviews."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response
            category = None
            reasoning = None
            
            lines = content.split('\n')
            for line in lines:
                if line.startswith('CATEGORY:'):
                    category = line.replace('CATEGORY:', '').strip()
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
            
            # Validate that we got a valid category
            if category not in self.REPORTING_CATEGORIES:
                # Try to find a close match
                category_lower = category.lower() if category else ""
                for valid_category in self.REPORTING_CATEGORIES:
                    if valid_category.lower() in category_lower or category_lower in valid_category.lower():
                        category = valid_category
                        break
                else:
                    # Default to "Spam" if we can't parse
                    category = "Spam"
                    reasoning = "Unable to parse AI response. Defaulting to Spam as a safe category."
            
            if not reasoning:
                reasoning = "AI analysis completed but reasoning was unclear."
            
            return {
                'category': category,
                'reasoning': reasoning
            }
            
        except Exception as e:
            # Fallback in case of API error
            return {
                'category': 'Spam',
                'reasoning': f'AI analysis failed: {str(e)}. Defaulting to Spam category.'
            }
