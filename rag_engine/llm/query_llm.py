from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Optional
import logging

from ..config import RAGConfig

logger = logging.getLogger(__name__)

class LLMQueryEngine:
    def __init__(self, model_name: Optional[str] = None):
        self.config = RAGConfig()
        self.model_name = model_name or self.config.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.1,
            api_key=self.config.OPENAI_API_KEY
        )
        
        # Define system prompt for financial analysis - Enhanced for clearer responses
        self.system_prompt = """You are an expert financial analyst assistant specializing in cryptocurrency and financial markets. 
        Your role is to provide clear, accurate, and actionable insights to traders and investors.
        
        When answering questions, follow these guidelines:
        
        1. CLARITY FIRST: Always provide clear, easy-to-understand explanations. Break down complex concepts.
        2. ACCURACY: Use only the provided context and verified information. Never guess or speculate.
        3. STRUCTURE: Organize your responses with:
           - A brief summary/answer upfront
           - Detailed explanation
           - Actionable insights or recommendations (when appropriate)
           - Sources or context references
        4. CONTEXT AWARENESS: 
           - If context is provided, use it extensively
           - If context is insufficient, clearly state what information is missing
           - Never make up data or statistics
        5. TRADING FOCUS: When discussing trading:
           - Explain market conditions clearly
           - Discuss risk factors
           - Provide balanced perspectives
           - Avoid giving direct trading advice without proper disclaimers
        6. FORMAT: Use bullet points, numbered lists, or clear paragraphs for readability.
        7. TONE: Be professional, helpful, and educational. Avoid jargon unless you explain it.
        
        Always end with a clear conclusion or next steps when appropriate."""
    
    def query_llm(self, prompt: str, context: Optional[List[Dict]] = None) -> str:
        """Query LLM with optional context from RAG"""
        try:
            if context:
                return self._query_with_context(prompt, context)
            else:
                return self._query_simple(prompt)
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return f"Error: Unable to process your request. {str(e)}"
    
    def _query_with_context(self, prompt: str, context: List[Dict]) -> str:
        """Query LLM with RAG context"""
        try:
            # Format context for the prompt
            context_text = self._format_context(context)
            
            # Create the full prompt with context
            full_prompt = f"""Context Information:
{context_text}

User Question: {prompt}

Please answer the user's question based on the provided context. If the context doesn't contain enough information to answer the question, please say so."""
            
            # Create messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=full_prompt)
            ]
            
            # Get response
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in context query: {e}")
            return f"Error processing request with context: {str(e)}"
    
    def _query_simple(self, prompt: str) -> str:
        """Simple LLM query without context"""
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in simple query: {e}")
            return f"Error processing request: {str(e)}"
    
    def _format_context(self, context: List[Dict]) -> str:
        """Format context documents for LLM prompt"""
        formatted_context = []
        
        for i, doc in enumerate(context, 1):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            score = doc.get('score', 0)
            
            # Extract key metadata
            title = metadata.get('title', 'Unknown Title')
            source = metadata.get('source', 'Unknown Source')
            published = metadata.get('published', 'Unknown Date')
            
            formatted_doc = f"""Document {i}:
Title: {title}
Source: {source}
Published: {published}
Relevance Score: {score:.3f}
Content: {content}
---"""
            
            formatted_context.append(formatted_doc)
        
        return "\n".join(formatted_context)
    
    def analyze_market_sentiment(self, context: List[Dict]) -> str:
        """Analyze market sentiment from news context"""
        prompt = """Based on the provided financial news context, analyze the current market sentiment. 
        Consider:
        1. Overall tone of the news (positive, negative, neutral)
        2. Key themes and trends
        3. Potential market impacts
        4. Risk factors mentioned
        
        Provide a concise sentiment analysis with supporting evidence from the news."""
        
        return self._query_with_context(prompt, context)
    
    def summarize_market_news(self, context: List[Dict]) -> str:
        """Summarize market news from context"""
        prompt = """Summarize the key market news and developments from the provided context. 
        Focus on:
        1. Major market-moving events
        2. Significant company announcements
        3. Economic indicators and trends
        4. Regulatory changes
        
        Provide a clear, structured summary."""
        
        return self._query_with_context(prompt, context)
    
    def answer_market_question(self, question: str, context: List[Dict]) -> str:
        """Answer specific market-related questions using context"""
        return self._query_with_context(question, context)

# Backward compatibility function
def query_llm(prompt: str, context: Optional[List[Dict]] = None) -> str:
    """Convenience function for backward compatibility"""
    engine = LLMQueryEngine()
    return engine.query_llm(prompt, context)
