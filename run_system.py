#!/usr/bin/env python3
"""
Ameron Complete System Startup Script
Starts all components: RAG Engine, Trading API, and Trading Agent API
"""

import os
import sys
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🚀 Ameron - Complete AI Trading System")
    print("=" * 50)
    
    # Set local store if no Pinecone key
    if not os.getenv("PINECONE_API_KEY"):
        os.environ["USE_LOCAL_STORE"] = "true"
        print("📦 Using local vector store (no Pinecone key found)")
    else:
        print("🌐 Using Pinecone vector store")
    
    print("\n🔧 Starting System Components:")
    print("  • RAG Engine (AI Analysis): http://localhost:8000")
    print("  • Trading API (Secure): http://localhost:8001") 
    print("  • Trading Agent API (Main): http://localhost:8003")
    
    print(f"\n📚 Documentation:")
    print(f"  • RAG Engine: http://localhost:8000/docs")
    print(f"  • Trading API: http://localhost:8001/docs")
    print(f"  • Trading Agent: http://localhost:8003/docs")
    
    print(f"\n🎯 Quick Start:")
    print(f"  • Run demo: python demo_showcase.py")
    print(f"  • Test system: python test_system.py")
    print(f"  • View dashboard: http://localhost:8003/dashboard/investor")
    
    print(f"\n⚡ System Features:")
    print(f"  ✅ AI-powered market analysis (RAG)")
    print(f"  ✅ Autonomous trading agent")
    print(f"  ✅ Real-time portfolio management")
    print(f"  ✅ Multiple trading strategies")
    print(f"  ✅ Comprehensive backtesting")
    print(f"  ✅ Risk management")
    print(f"  ✅ Investor demonstrations")
    
    print(f"\n🚨 Press Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        # Start all services
        processes = []
        
        # RAG Engine
        print("🧠 Starting RAG Engine...")
        p1 = subprocess.Popen(['uvicorn', 'rag_engine.api_service:app', '--port', '8000', '--reload'])
        processes.append(p1)
        time.sleep(2)
        
        # Trading API
        print("💰 Starting Trading API...")
        p2 = subprocess.Popen(['uvicorn', 'trading_api.main:app', '--port', '8001', '--reload'])
        processes.append(p2)
        time.sleep(2)
        
        # Trading Agent API (Main System)
        print("🤖 Starting Trading Agent API...")
        p3 = subprocess.Popen(['uvicorn', 'trading_agent_api:app', '--port', '8003', '--reload'])
        processes.append(p3)
        time.sleep(2)
        
        print(f"\n✅ All services started successfully!")
        print(f"🌐 Main Dashboard: http://localhost:8003")
        print(f"🎯 Ready for demonstrations and trading!")
        
        # Wait for interrupt
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n🛑 Shutting down all services...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except:
                p.kill()
        print("✅ All services stopped")
    
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        print(f"💡 Make sure all dependencies are installed:")
        print(f"   pip install -r requirements.txt")

if __name__ == "__main__":
    main() 