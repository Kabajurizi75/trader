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
        """Query LLM with RAG context - Enhanced for clearer responses"""
        try:
            # Format context for the prompt
            context_text = self._format_context(context)
            
            # Create the full prompt with context - Enhanced structure
            full_prompt = f"""Based on the following financial market information, please answer the user's question clearly and comprehensively.

CONTEXT INFORMATION:
{context_text}

USER QUESTION: {prompt}

INSTRUCTIONS:
1. Start with a direct answer to the question
2. Provide detailed explanation using the context provided
3. Cite specific information from the context when relevant
4. If the context doesn't fully answer the question, clearly state what information is missing
5. Structure your response for easy reading
6. Provide actionable insights when appropriate

Please provide a clear, well-structured response."""
            
            # Create messages with conversation history support
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=full_prompt)
            ]
            
            # Get response with increased token limit for comprehensive answers
            response = self.llm.invoke(messages)
            answer = response.content.strip()
            
            # Ensure answer is not empty
            if not answer or len(answer) < 10:
                return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question or provide more context."
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in context query: {e}")
            return f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your question."
    
    def _query_simple(self, prompt: str) -> str:
        """Simple LLM query without context - Enhanced for clearer responses"""
        try:
            # Enhance the prompt for better responses
            enhanced_prompt = f"""Please answer the following question about financial markets, trading, or cryptocurrency clearly and comprehensively:

{prompt}

Please provide:
1. A direct answer
2. Detailed explanation
3. Relevant context or background
4. Any important considerations or risks

Structure your response for easy reading."""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=enhanced_prompt)
            ]
            
            response = self.llm.invoke(messages)
            answer = response.content.strip()
            
            # Ensure answer is not empty
            if not answer or len(answer) < 10:
                return "I apologize, but I couldn't generate a proper response. Could you please provide more details or rephrase your question?"
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in simple query: {e}")
            return f"I encountered an error: {str(e)}. Please try rephrasing your question or providing more context."
    
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
