"""
STRATEGIC CERTAINTY ENGINE - COMPLETE SINGLE-FILE SOLUTION
==========================================================
Multi-Agent Marketing AI System with Web UI
- 11 Specialized AI Agents
- Central Strategy Agent (CSA) Orchestrator
- Real-time Strategic Huddles
- WebSocket Support
- Beautiful Modern UI

INSTALLATION:
pip install flask flask-socketio flask-cors groq pandas numpy scikit-learn xgboost

RUN:
python strategic_engine.py
Open: http://localhost:5001
"""

from flask import Flask, jsonify, request, render_template_string
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import random
import re
import sys
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


def configure_console_encoding():
    """Avoid Windows cp1252 crashes from emoji/unicode startup logs."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def load_local_env(env_path: str = ".env"):
    """Lightweight .env loader so local keys work without extra dependencies."""
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


configure_console_encoding()
load_local_env()


def extract_command(verdict_text: str) -> str:
    """Parse a stable command label from variable LLM output."""
    if not verdict_text:
        return "ADJUST"

    upper_text = verdict_text.upper()

    if "COMMAND:" in upper_text:
        command_line = upper_text.split("COMMAND:", 1)[1].splitlines()[0].strip()
        for token in ("GO", "STOP", "ADJUST"):
            if token in command_line:
                return token

    first_lines = upper_text.splitlines()[:8]
    for line in first_lines:
        stripped = line.strip()
        if stripped in {"GO", "STOP", "ADJUST"}:
            return stripped
        for token in ("GO", "STOP", "ADJUST"):
            if stripped.startswith(token):
                return token

    positive_signals = ("SCALE", "LAUNCH", "PROCEED", "INCREASE", "MOVE FORWARD", "EXPAND")
    caution_signals = ("OPTIMIZE", "ADJUST", "PHASED", "TEST", "PILOT", "REFINE")
    negative_signals = ("PAUSE", "STOP", "HOLD", "DELAY", "DO NOT", "AVOID")

    if any(signal in upper_text for signal in negative_signals):
        return "STOP"
    if any(signal in upper_text for signal in caution_signals):
        return "ADJUST"
    if any(signal in upper_text for signal in positive_signals):
        return "GO"

    return "ADJUST"


def ensure_command_prefix(verdict_text: str) -> str:
    """Guarantee the UI receives a verdict with a command header."""
    command = extract_command(verdict_text)
    if verdict_text and "COMMAND:" in verdict_text.upper():
        return verdict_text
    return f"COMMAND: {command}\n\n{verdict_text.strip()}" if verdict_text else f"COMMAND: {command}"


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def normalize_score(value: float, scale: float = 100.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        return 0.0
    if scale <= 0:
        return 0.0
    return clamp(numeric / scale, 0.0, 1.0)


def parse_query_signals(query: str) -> Dict[str, Any]:
    """Extract business intent and request intensity from the query."""
    query_lower = (query or "").lower()

    action = 'evaluate'
    if any(token in query_lower for token in ['pause', 'stop', 'hold', 'delay', 'cancel']):
        action = 'pause'
    elif any(token in query_lower for token in ['cut', 'reduce', 'decrease']):
        action = 'reduce'
    elif any(token in query_lower for token in ['shift', 'reallocate', 'move budget']):
        action = 'reallocate'
    elif any(token in query_lower for token in ['launch', 'roll out', 'start']):
        action = 'launch'
    elif any(token in query_lower for token in ['increase', 'scale', 'expand', 'boost', 'grow']):
        action = 'increase'
    elif any(token in query_lower for token in ['defend', 'respond', 'match competitor']):
        action = 'defend'

    channel = 'mixed'
    for candidate in ['linkedin', 'facebook', 'instagram', 'google', 'search', 'youtube', 'tiktok', 'email', 'webinar']:
        if candidate in query_lower:
            channel = candidate
            break

    objective = 'growth'
    if any(token in query_lower for token in ['cac', 'efficiency', 'roas', 'roi', 'profit']):
        objective = 'efficiency'
    elif any(token in query_lower for token in ['risk', 'brand', 'sentiment', 'competitor', 'defend']):
        objective = 'risk'
    elif any(token in query_lower for token in ['lead quality', 'enterprise leads', 'pipeline', 'conversion']):
        objective = 'quality'

    amount_match = re.search(r'(\d{1,3})\s*%', query_lower)
    change_pct = int(amount_match.group(1)) if amount_match else 0
    if change_pct == 0:
        if 'aggressive' in query_lower:
            change_pct = 40
        elif 'phased' in query_lower or 'pilot' in query_lower or 'test' in query_lower:
            change_pct = 15
        elif action in {'increase', 'reduce', 'reallocate'}:
            change_pct = 25

    urgency = 'medium'
    if any(token in query_lower for token in ['immediately', 'now', 'urgent', 'this week']):
        urgency = 'high'
    elif any(token in query_lower for token in ['next quarter', 'later', 'eventually']):
        urgency = 'low'

    return {
        'action': action,
        'channel': channel,
        'objective': objective,
        'change_pct': change_pct,
        'urgency': urgency
    }


def build_scenario_data(query: str, req_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Create structured scenario data from explicit inputs plus query signals."""
    signals = parse_query_signals(query)

    lead_score = float(req_data.get('lead_score', 72))
    conversion_probability = float(req_data.get('conversion_probability', clamp(lead_score / 160.0, 0.15, 0.75)))
    company_size = req_data.get('company_size', '201-1000')
    industry = req_data.get('industry', 'Technology')
    requested_demo = 1 if lead_score >= 75 else 0
    viewed_pricing = 1 if lead_score >= 60 else 0

    roas = float(req_data.get('current_roas', 3.8))
    target_roas = float(req_data.get('target_roas', 3.5))
    brand_health = float(req_data.get('brand_health', 7.0))
    threat_level = int(req_data.get('competitor_threat', 6))

    if signals['action'] == 'increase':
        threat_level += 1 if signals['change_pct'] >= 40 else 0
    elif signals['action'] == 'pause':
        roas -= 0.3
    elif signals['action'] == 'reduce':
        roas -= 0.1
    elif signals['action'] == 'defend':
        threat_level += 1
        brand_health -= 0.2

    if signals['objective'] == 'efficiency':
        target_roas = max(target_roas, 4.0)
    elif signals['objective'] == 'risk':
        brand_health = min(brand_health, 6.8)
        threat_level = max(threat_level, 7)
    elif signals['objective'] == 'quality':
        conversion_probability = max(conversion_probability, 0.35)
        lead_score = max(lead_score, 68)

    if context.get('risk_tolerance', 'Medium').lower() == 'low':
        target_roas += 0.3
        threat_level = max(threat_level, 6)
    elif context.get('risk_tolerance', 'Medium').lower() == 'high':
        target_roas -= 0.2

    if signals['urgency'] == 'high':
        threat_level = min(10, threat_level + 1)

    if 'existing_data' in req_data and isinstance(req_data['existing_data'], dict):
        existing_data = req_data['existing_data']
    else:
        existing_data = req_data.get('data', {})

    scenario_data = {
        'lead_info': {
            'Engagement_Score': round(lead_score / 100.0, 2),
            'Conversion_Probability': round(clamp(conversion_probability, 0.05, 0.95), 2),
            'Company_Size': company_size,
            'Industry': industry,
            'Requested_Demo': requested_demo,
            'Viewed_Pricing_Page': viewed_pricing
        },
        'performance_data': {
            'roas': round(clamp(roas, 0.5, 8.0), 2),
            'target': round(clamp(target_roas, 1.0, 8.0), 2)
        },
        'sentiment_data': {
            'health_score': round(clamp(brand_health, 1.0, 10.0), 1)
        },
        'competitor_data': {
            'threat_level': int(clamp(threat_level, 1, 10))
        },
        'campaign_info': {
            'segment': req_data.get('audience_segment', 'Enterprise Buyers'),
            'product': req_data.get('product_name', 'Growth Program')
        },
        'macro_data': {
            'market_phase': req_data.get('market_phase', '')
        },
        'query_signals': signals
    }

    for section, values in existing_data.items():
        if isinstance(values, dict):
            scenario_data.setdefault(section, {}).update(values)

    return scenario_data

# ML Libraries
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score
    from xgboost import XGBClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("[WARN]  ML libraries not available. Using rule-based scoring.")

# LLM Integration
try:
    from groq import Groq
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("[WARN]  Groq not available. Using template-based generation.")

# =========================================================================
# CONFIGURATION
# =========================================================================

class Config:
    # LLM Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = "llama-3.1-70b-versatile"
    TEMPERATURE = 0.7
    MAX_TOKENS = 1500
    
    # Agent Settings
    MAX_HUDDLE_ROUNDS = 5

# =========================================================================
# LLM INTERFACE
# =========================================================================

class LLMInterface:
    """Universal LLM interface supporting Groq"""
    
    def __init__(self):
        self.available = LLM_AVAILABLE and Config.GROQ_API_KEY
        
        if self.available:
            try:
                self.client = Groq(api_key=Config.GROQ_API_KEY)
                print("[OK] LLM Interface: Groq connected")
            except Exception as e:
                print(f"[WARN]  LLM initialization failed: {e}")
                self.available = False
        else:
            print("[WARN]  LLM Interface: Using template mode")
    
    def generate(self, prompt: str, system_message: Optional[str] = None, temperature: Optional[float] = None) -> str:
        """Generate completion"""
        
        if not self.available:
            return self._template_fallback(prompt)
        
        try:
            temp = temperature or Config.TEMPERATURE
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=messages,
                temperature=temp,
                max_tokens=Config.MAX_TOKENS
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[WARN]  LLM generation failed: {e}")
            return self._template_fallback(prompt)
    
    def _template_fallback(self, prompt):
        """Fallback template responses"""
        if "segment" in prompt.lower():
            return "Analysis complete. Customers segmented into 5 strategic groups based on engagement and value."
        elif "campaign" in prompt.lower():
            return "Campaign variants generated with A/B testing optimization."
        elif "verdict" in prompt.lower():
            return """COMMAND: GO

═══════════════════════════════════════
THE STRATEGY (What are we doing?)
═══════════════════════════════════════
Scale marketing investment with data-driven targeting and continuous optimization.

═══════════════════════════════════════
THE PREDICTION (Will it work?)
═══════════════════════════════════════
Expected ROI: 4.2x return
Confidence Score: 78%
Timeframe: 60 days
Key Success Metric: Customer Acquisition Cost < $150

═══════════════════════════════════════
THE DEFENSE (What about rivals/risks?)
═══════════════════════════════════════
Competitive positioning maintained through differentiated value proposition and proactive market monitoring.

═══════════════════════════════════════
EXECUTION ORDERS
═══════════════════════════════════════
→ Campaign Generator: Launch optimized campaigns by EOD
→ Performance Monitor: Track ROAS daily, alert at 3.5x threshold
→ Competitor Intelligence: Monitor rival activities weekly

RATIONALE: Strong lead quality indicators and market conditions support aggressive growth strategy."""
        else:
            return "Analysis completed successfully. Recommendations generated based on available data."

# =========================================================================
# BASE AGENT CLASS
# =========================================================================

class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_name: str, agent_role: str):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.llm = LLMInterface()
    
    @abstractmethod
    def analyze(self, data: Dict, context: Dict) -> Dict:
        """Each agent must implement their analysis logic"""
        pass
    
    def present_case(self, query: str, context: Dict, data: Optional[Dict] = None) -> Dict:
        """Present argument in strategic huddle"""
        
        # Run analysis
        analysis_result = self.analyze(data or {}, context)
        
        # Format as huddle argument
        system_message = f"""You are the {self.agent_name}.
Your role: {self.agent_role}

You are participating in a strategic huddle. Present your argument clearly:
- Start with PRO/CON/CAUTION/CONTEXT depending on your stance
- Use data from your analysis
- Be concise but persuasive
- Focus on your specialized domain"""

        prompt = f"""
STRATEGIC QUERY:
{query}

YOUR ANALYSIS RESULTS:
{self._format_analysis(analysis_result)}

BUSINESS CONTEXT:
{self._format_context(context)}

Present your argument to the Central Strategy Agent. Start with PRO/CON/CAUTION/CONTEXT.
"""
        
        argument = self.llm.generate(prompt, system_message, temperature=0.6)
        
        return {
            'agent_name': self.agent_name,
            'argument': argument,
            'raw_analysis': analysis_result,
            'confidence': analysis_result.get('confidence_score', 0.5)
        }
    
    def _format_analysis(self, analysis):
        """Convert analysis dict to readable format"""
        return '\n'.join([f"- {k}: {v}" for k, v in analysis.items()])
    
    def _format_context(self, context):
        """Convert context dict to readable format"""
        return '\n'.join([f"- {k}: {v}" for k, v in context.items()])

# =========================================================================
# CENTRAL STRATEGY AGENT (CSA)
# =========================================================================

class CentralStrategyAgent:
    """The AI CMO - Orchestrates all strategic decisions"""
    
    def __init__(self):
        self.llm = LLMInterface()
        self.conversation_state = []
        self.decision_history = []
    
    def open_huddle(self, query: str, context: Dict) -> Dict:
        """Initiate strategic huddle"""
        
        system_message = """You are the Central Strategy Agent (CSA), an AI Chief Marketing Officer.
You facilitate strategic huddles where specialized agents debate before you make final decisions.

Your role:
1. Analyze the query and business context
2. Identify which specialized agents are needed for this decision
3. Frame the strategic question clearly"""

        prompt = f"""
BUSINESS CONTEXT:
- Goal Mode: {context.get('goal_mode', 'Balanced Growth')}
- Risk Tolerance: {context.get('risk_tolerance', 'Medium')}
- Budget Available: ${context.get('budget', 50000)}
- Time Horizon: {context.get('timeframe', '30 days')}

STRATEGIC QUERY:
{query}

TASK: Open the strategic huddle with:
1. A clear restatement of the decision needed
2. List of 3-5 specialized agents who should present arguments

FORMAT YOUR RESPONSE AS:
DECISION NEEDED: [One sentence]
AGENTS REQUIRED: [Agent1, Agent2, Agent3]
"""
        
        response = self.llm.generate(prompt, system_message)
        
        huddle_opening = {
            'role': 'CSA',
            'phase': 'OPENING',
            'content': response,
            'timestamp': datetime.now().isoformat()
        }
        
        self.conversation_state.append(huddle_opening)
        return huddle_opening
    
    def parse_agent_requirements(self, opening_response: Dict) -> List[str]:
        """Extract which agents need to participate"""
        
        content = opening_response['content']
        
        # Try to extract from structured format
        if 'AGENTS REQUIRED:' in content:
            agents_line = content.split('AGENTS REQUIRED:')[1].split('\n')[0]
            agents = [a.strip() for a in agents_line.split(',')]
            
            # Map to actual agent keys
            agent_mapping = {
                'lead scorer': 'smart_lead_scorer',
                'smart lead': 'smart_lead_scorer',
                'value': 'lead_value_predictor',
                'enrichment': 'lead_enrichment',
                'campaign': 'campaign_generator',
                'content': 'content_recommender',
                'creative': 'creative_optimizer',
                'performance': 'performance_monitor',
                'sentiment': 'sentiment_tracker',
                'competitor': 'competitor_intelligence',
                'macro': 'macro_trend_analyzer',
                'trend': 'macro_trend_analyzer'
            }
            
            mapped_agents = []
            for agent in agents:
                agent_lower = agent.lower()
                for key, value in agent_mapping.items():
                    if key in agent_lower and value not in mapped_agents:
                        mapped_agents.append(value)
                        break
            
            if mapped_agents:
                return mapped_agents
        
        # Fallback: return default agents
        return ['smart_lead_scorer', 'lead_value_predictor', 'competitor_intelligence', 
                'performance_monitor', 'creative_optimizer']
    
    def synthesize_arguments(self, agent_arguments: List[Dict]) -> Dict:
        """Collect all agent arguments"""
        
        synthesis = {
            'role': 'CSA',
            'phase': 'SYNTHESIS',
            'content': '\n\n'.join([
                f"[{arg['agent_name']}]: {arg['argument']}" 
                for arg in agent_arguments
            ]),
            'timestamp': datetime.now().isoformat()
        }
        
        self.conversation_state.append(synthesis)
        return synthesis
    
    def issue_verdict(self, context: Dict, goal_weights: Optional[Dict] = None) -> Dict:
        """Make final strategic decision"""
        
        if goal_weights is None:
            goal_weights = {
                'growth': 0.4,
                'risk_mitigation': 0.3,
                'efficiency': 0.3
            }
        
        system_message = """You are the Central Strategy Agent issuing a FINAL VERDICT.

You must analyze all arguments and make a decisive command: GO, STOP, or ADJUST.

Your verdict MUST include:
1. THE STRATEGY: One clear action plan
2. THE PREDICTION: Expected ROI/outcome with confidence score (%)
3. THE DEFENSE: How this protects against competition/risk
4. EXECUTION ORDERS: Specific tasks for each agent"""

        # Build conversation history
        conversation_text = "\n\n".join([
            f"{'='*60}\n{msg.get('phase', msg['role'])}\n{'='*60}\n{msg['content']}"
            for msg in self.conversation_state
        ])
        
        prompt = f"""
STRATEGIC HUDDLE TRANSCRIPT:
{conversation_text}

DECISION WEIGHTS:
- Growth Priority: {goal_weights['growth']*100}%
- Risk Mitigation: {goal_weights['risk_mitigation']*100}%
- Efficiency: {goal_weights['efficiency']*100}%

ISSUE YOUR FINAL VERDICT IN THIS EXACT FORMAT:

COMMAND: [GO / STOP / ADJUST]

═══════════════════════════════════════
THE STRATEGY (What are we doing?)
═══════════════════════════════════════
[One clear sentence describing the action plan]

═══════════════════════════════════════
THE PREDICTION (Will it work?)
═══════════════════════════════════════
Expected ROI: [X.Xx return]
Confidence Score: [XX%]
Timeframe: [X days/weeks]
Key Success Metric: [specific KPI]

═══════════════════════════════════════
THE DEFENSE (What about rivals/risks?)
═══════════════════════════════════════
[How this decision protects competitive position]

═══════════════════════════════════════
EXECUTION ORDERS
═══════════════════════════════════════
→ [Agent Name]: [Specific task with deadline]
→ [Agent Name]: [Specific task with deadline]

RATIONALE: [2-3 sentences explaining key factors]
"""
        
        verdict_response = self.llm.generate(prompt, system_message, temperature=0.3)
        verdict_response = ensure_command_prefix(verdict_response)
        
        verdict = {
            'role': 'CSA',
            'phase': 'FINAL_VERDICT',
            'content': verdict_response,
            'context': context,
            'weights': goal_weights,
            'timestamp': datetime.now().isoformat()
        }
        
        self.conversation_state.append(verdict)
        self.decision_history.append({
            'query': context.get('original_query'),
            'verdict': verdict_response,
            'timestamp': verdict['timestamp']
        })
        
        return verdict
    
    def get_huddle_transcript(self) -> List[Dict]:
        """Return full conversation for transparency"""
        return self.conversation_state
    
    def reset_huddle(self):
        """Clear state for new decision"""
        self.conversation_state = []

# =========================================================================
# SPECIALIZED AGENTS
# =========================================================================

class SmartLeadScorer(BaseAgent):
    """Predicts lead conversion probability"""
    
    def __init__(self):
        super().__init__(
            agent_name="Smart Lead Scorer",
            agent_role="Predicts lead conversion probability and priority"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        lead_data = data.get('lead_info', {})
        
        # Simple scoring logic
        score = 0
        engagement = lead_data.get('Engagement_Score', 0.5)
        
        score += engagement * 50
        
        if lead_data.get('Requested_Demo', 0) == 1:
            score += 25
        if lead_data.get('Viewed_Pricing_Page', 0) == 1:
            score += 15
        if lead_data.get('Company_Size', '') in ['201-1000', '1000+']:
            score += 10
        
        score = min(100, score)
        
        if score >= 75:
            priority = "HOT"
        elif score >= 50:
            priority = "WARM"
        else:
            priority = "COLD"
        
        return {
            'priority_score': round(score, 1),
            'conversion_probability': round(score / 100, 2),
            'priority': priority,
            'confidence_score': 0.85,
            'recommendation': f"{priority}_PRIORITY"
        }

class LeadEnrichmentAgent(BaseAgent):
    """Fills missing lead data"""
    
    def __init__(self):
        super().__init__(
            agent_name="Lead Enrichment Agent",
            agent_role="Fills missing lead data with external sources"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        lead_data = data.get('lead_info', {})
        
        # Mock enrichment
        enriched_fields = []
        if not lead_data.get('Company_Size'):
            lead_data['Company_Size'] = '51-200'
            enriched_fields.append('Company_Size')
        
        if not lead_data.get('Industry'):
            lead_data['Industry'] = 'Technology'
            enriched_fields.append('Industry')
        
        enrichment_score = (len(enriched_fields) / 5) * 100
        
        return {
            'enriched_data': lead_data,
            'newly_enriched_fields': enriched_fields,
            'enrichment_score': round(enrichment_score, 1),
            'confidence_score': 0.75
        }

class LeadValuePredictor(BaseAgent):
    """Calculates Expected Lifetime Value"""
    
    def __init__(self):
        super().__init__(
            agent_name="Lead Value Predictor",
            agent_role="Calculates Expected Lifetime Value and revenue potential"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        lead_data = data.get('lead_info', {})
        
        # Base deal size
        company_size = lead_data.get('Company_Size', '51-200')
        size_multipliers = {'1-10': 5000, '11-50': 15000, '51-200': 50000, '201-1000': 150000, '1000+': 500000}
        
        base_value = 50000
        for size, value in size_multipliers.items():
            if size in company_size:
                base_value = value
                break
        
        # Adjust for conversion probability
        conv_prob = lead_data.get('Conversion_Probability', 0.25)
        eltv = base_value * conv_prob * 3.5  # 3.5 year average lifetime
        
        # ROI calculation
        acquisition_cost = context.get('avg_acquisition_cost', 5000)
        roi_multiple = (eltv / acquisition_cost) if acquisition_cost > 0 else 0
        
        # Value tier
        if eltv >= 200000:
            value_tier = 'PLATINUM'
        elif eltv >= 100000:
            value_tier = 'GOLD'
        elif eltv >= 50000:
            value_tier = 'SILVER'
        else:
            value_tier = 'BRONZE'
        
        return {
            'expected_lifetime_value': round(eltv, 2),
            'base_deal_size': base_value,
            'roi_multiple': round(roi_multiple, 2),
            'value_tier': value_tier,
            'confidence_score': 0.82
        }

class PersonalizedCampaignGenerator(BaseAgent):
    """Generates multi-channel campaigns"""
    
    def __init__(self):
        super().__init__(
            agent_name="Campaign Generator",
            agent_role="Creates compelling multi-channel marketing content"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        campaign_data = data.get('campaign_info', {})
        
        segment = campaign_data.get('segment', 'All Customers')
        product = campaign_data.get('product', 'Product')
        
        variant_a_subject = f"Exclusive {product} Offer for {segment}"
        variant_a_content = f"Hi! We have {product} designed for {segment}. Limited time offer with premium benefits."
        
        variant_b_subject = f"🎯 {product} - Perfect for {segment}"
        variant_b_content = f"Hello! Introducing {product} - the solution {segment} need. Trusted by thousands."
        
        return {
            'variant_a': {'subject': variant_a_subject, 'content': variant_a_content},
            'variant_b': {'subject': variant_b_subject, 'content': variant_b_content},
            'quality_score_a': 75,
            'quality_score_b': 78,
            'recommended_variant': 'B',
            'confidence_score': 0.80
        }

class ContentRecommendationEngine(BaseAgent):
    """Recommends next-best content"""
    
    def __init__(self):
        super().__init__(
            agent_name="Content Recommender",
            agent_role="Suggests optimal content for lead progression"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        lead_data = data.get('lead_info', {})
        
        engagement = lead_data.get('Engagement_Score', 0.5)
        
        if engagement > 0.7:
            stage = 'decision'
            recommendations = ['Pricing Guide', 'ROI Calculator', 'Customer Stories']
        elif engagement > 0.4:
            stage = 'consideration'
            recommendations = ['Product Demo', 'Feature Comparison', 'Case Studies']
        else:
            stage = 'awareness'
            recommendations = ['Industry Report', 'Getting Started Guide', 'Webinar']
        
        return {
            'current_stage': stage,
            'top_recommendations': recommendations,
            'confidence_score': 0.78
        }

class CreativeOptimizer(BaseAgent):
    """Optimizes creative elements"""
    
    def __init__(self):
        super().__init__(
            agent_name="Creative Optimizer",
            agent_role="Analyzes and optimizes creative performance"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        creative_data = data.get('creative_info', {})
        
        suggestions = [
            {'priority': 'HIGH', 'element': 'Subject Line', 'suggestion': 'Add personalization token', 'impact': '+26%'},
            {'priority': 'MEDIUM', 'element': 'CTA', 'suggestion': 'Change to action-oriented', 'impact': '+15%'}
        ]
        
        return {
            'optimization_suggestions': suggestions,
            'estimated_performance_lift': '+35%',
            'confidence_score': 0.88
        }

class PerformanceMonitor(BaseAgent):
    """Tracks campaign performance"""
    
    def __init__(self):
        super().__init__(
            agent_name="Performance Monitor",
            agent_role="Tracks real-time ROI and ROAS metrics"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        perf_data = data.get('performance_data', {})
        
        current_roas = perf_data.get('roas', 4.2)
        target_roas = perf_data.get('target', 3.5)
        
        status = 'EXCEEDING' if current_roas > target_roas else 'MEETING' if current_roas >= target_roas * 0.9 else 'BELOW'
        
        return {
            'current_roas': current_roas,
            'target_roas': target_roas,
            'performance_status': status,
            'recommendation': 'SCALE' if status == 'EXCEEDING' else 'MAINTAIN' if status == 'MEETING' else 'OPTIMIZE',
            'confidence_score': 0.92
        }

class SentimentTracker(BaseAgent):
    """Monitors brand sentiment"""
    
    def __init__(self):
        super().__init__(
            agent_name="Sentiment Tracker",
            agent_role="Monitors brand health and reputation risks"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        sentiment_data = data.get('sentiment_data', {})
        
        brand_health = sentiment_data.get('health_score', 7.2)
        
        if brand_health > 7.5:
            risk_level = 'LOW'
            recommendation = 'PROCEED'
        elif brand_health > 5:
            risk_level = 'MEDIUM'
            recommendation = 'CAUTION'
        else:
            risk_level = 'HIGH'
            recommendation = 'DEFENSIVE_ONLY'
        
        return {
            'brand_health_score': round(brand_health, 1),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'confidence_score': 0.75
        }

class CompetitorIntelligence(BaseAgent):
    """Tracks competitor activities"""
    
    def __init__(self):
        super().__init__(
            agent_name="Competitor Intelligence",
            agent_role="Monitors competitor strategies and provides counter-moves"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        competitor_data = data.get('competitor_data', {})
        
        threat_score = competitor_data.get('threat_level', 6)
        
        if threat_score > 7:
            urgency = 'HIGH'
            counter_strategy = 'AGGRESSIVE: Match or exceed competitor spend'
        elif threat_score > 4:
            urgency = 'MEDIUM'
            counter_strategy = 'DEFENSIVE: Maintain position while monitoring'
        else:
            urgency = 'LOW'
            counter_strategy = 'OPPORTUNISTIC: Exploit competitor weaknesses'
        
        return {
            'rival_threat_score': threat_score,
            'urgency_level': urgency,
            'recommended_counter_strategy': counter_strategy,
            'confidence_score': 0.85
        }

class MacroTrendAnalyzer(BaseAgent):
    """Analyzes market trends"""
    
    def __init__(self):
        super().__init__(
            agent_name="Macro Trend Analyzer",
            agent_role="Provides market predictions and economic context"
        )
    
    def analyze(self, data: Dict, context: Dict) -> Dict:
        macro_data = data.get('macro_data', {})
        market_phase = macro_data.get('market_phase')
        if not market_phase:
            roas = data.get('performance_data', {}).get('roas', 4.2)
            sentiment = data.get('sentiment_data', {}).get('health_score', 7.2)
            threat = data.get('competitor_data', {}).get('threat_level', 6)

            if roas >= 4.0 and sentiment >= 7.0 and threat <= 6:
                market_phase = 'GROWTH'
            elif roas >= 3.2 and sentiment >= 6.0:
                market_phase = 'RECOVERY'
            elif threat >= 8 or sentiment < 5.0:
                market_phase = 'CONTRACTION'
            else:
                market_phase = 'PEAK'
        
        if market_phase in ['GROWTH', 'RECOVERY']:
            recommendation = 'EXPAND'
            risk = 'LOW'
        elif market_phase == 'PEAK':
            recommendation = 'MAINTAIN'
            risk = 'MODERATE'
        else:
            recommendation = 'CONSOLIDATE'
            risk = 'HIGH'
        
        return {
            'market_phase': market_phase,
            'recommendation': recommendation,
            'market_risk': risk,
            'confidence_score': 0.80
        }

# =========================================================================
# STRATEGIC CERTAINTY ENGINE
# =========================================================================

class StrategicCertaintyEngine:
    """Main orchestrator for multi-agent strategic decision-making"""
    
    def __init__(self):
        self.csa = CentralStrategyAgent()
        
        # Initialize all 11 agents
        self.agents = {
            # Cluster 1: Lead Intelligence
            'smart_lead_scorer': SmartLeadScorer(),
            'lead_enrichment': LeadEnrichmentAgent(),
            'lead_value_predictor': LeadValuePredictor(),
            
            # Cluster 2: Execution & Optimization
            'campaign_generator': PersonalizedCampaignGenerator(),
            'content_recommender': ContentRecommendationEngine(),
            'creative_optimizer': CreativeOptimizer(),
            
            # Cluster 3: Defense & Performance
            'performance_monitor': PerformanceMonitor(),
            'sentiment_tracker': SentimentTracker(),
            'competitor_intelligence': CompetitorIntelligence(),
            
            # Cluster 4: Strategy
            'macro_trend_analyzer': MacroTrendAnalyzer()
        }
        
        print("[OK] Strategic Certainty Engine initialized with 11 agents")
    
    def _select_agents(self, query: str, suggested_agents: List[str]) -> List[str]:
        """Blend LLM suggestions with deterministic query heuristics."""
        query_lower = (query or "").lower()
        chosen = list(suggested_agents or [])

        keyword_map = {
            'budget': ['performance_monitor', 'lead_value_predictor', 'macro_trend_analyzer'],
            'spend': ['performance_monitor', 'lead_value_predictor'],
            'campaign': ['campaign_generator', 'creative_optimizer', 'performance_monitor'],
            'content': ['content_recommender', 'creative_optimizer'],
            'creative': ['creative_optimizer', 'campaign_generator'],
            'brand': ['sentiment_tracker', 'competitor_intelligence'],
            'sentiment': ['sentiment_tracker', 'competitor_intelligence'],
            'competitor': ['competitor_intelligence', 'performance_monitor'],
            'lead': ['smart_lead_scorer', 'lead_value_predictor', 'lead_enrichment'],
            'pricing': ['smart_lead_scorer', 'lead_value_predictor'],
            'market': ['macro_trend_analyzer', 'competitor_intelligence'],
            'risk': ['sentiment_tracker', 'macro_trend_analyzer', 'competitor_intelligence']
        }

        for keyword, mapped_agents in keyword_map.items():
            if keyword in query_lower:
                for agent in mapped_agents:
                    if agent not in chosen:
                        chosen.append(agent)

        baseline_agents = [
            'smart_lead_scorer',
            'lead_value_predictor',
            'performance_monitor',
            'competitor_intelligence',
            'macro_trend_analyzer'
        ]
        for agent in baseline_agents:
            if agent not in chosen:
                chosen.append(agent)

        return [agent for agent in chosen if agent in self.agents][:6]

    def _compute_decision_payload(self, agent_arguments: List[Dict], context: Dict, query: str) -> Dict:
        """Create a deterministic executive decision from structured agent signals."""
        analyses = {arg['agent_name']: arg.get('raw_analysis', {}) for arg in agent_arguments}
        signals = context.get('query_signals', parse_query_signals(query))

        lead = analyses.get('Smart Lead Scorer', {})
        value = analyses.get('Lead Value Predictor', {})
        perf = analyses.get('Performance Monitor', {})
        sentiment = analyses.get('Sentiment Tracker', {})
        competitor = analyses.get('Competitor Intelligence', {})
        macro = analyses.get('Macro Trend Analyzer', {})
        content = analyses.get('Content Recommender', {})

        growth_score = np.mean([
            normalize_score(lead.get('priority_score', 60)),
            normalize_score(value.get('roi_multiple', 2.0), 5.0),
            normalize_score(perf.get('current_roas', 3.5), 6.0),
            1.0 if macro.get('recommendation') == 'EXPAND' else 0.65 if macro.get('recommendation') == 'MAINTAIN' else 0.35
        ])

        risk_score = np.mean([
            0.2 if sentiment.get('risk_level') == 'LOW' else 0.55 if sentiment.get('risk_level') == 'MEDIUM' else 0.85,
            0.75 if competitor.get('urgency_level') == 'HIGH' else 0.5 if competitor.get('urgency_level') == 'MEDIUM' else 0.25,
            0.8 if macro.get('market_risk') == 'HIGH' else 0.5 if macro.get('market_risk') == 'MODERATE' else 0.25
        ])

        efficiency_score = np.mean([
            normalize_score(value.get('roi_multiple', 2.0), 5.0),
            normalize_score(perf.get('current_roas', 3.5), 5.0),
            0.8 if perf.get('performance_status') == 'EXCEEDING' else 0.6 if perf.get('performance_status') == 'MEETING' else 0.35
        ])

        risk_tolerance = context.get('risk_tolerance', 'Medium').lower()
        risk_adjustment = {'low': -0.08, 'medium': 0.0, 'high': 0.08}.get(risk_tolerance, 0.0)
        action_adjustment = {
            'increase': 0.06 if signals.get('change_pct', 0) <= 25 else -0.02 if signals.get('change_pct', 0) <= 40 else -0.10,
            'launch': 0.02,
            'reallocate': 0.03,
            'reduce': -0.03,
            'pause': -0.12,
            'defend': -0.05,
            'evaluate': 0.0
        }.get(signals.get('action', 'evaluate'), 0.0)
        objective_adjustment = {
            'growth': growth_score * 0.08,
            'efficiency': efficiency_score * 0.08,
            'risk': -risk_score * 0.10,
            'quality': normalize_score(lead.get('priority_score', 60)) * 0.06
        }.get(signals.get('objective', 'growth'), 0.0)
        decision_index = (growth_score * 0.45) + (efficiency_score * 0.35) - (risk_score * 0.30) + risk_adjustment + action_adjustment + objective_adjustment

        if decision_index >= 0.48 and risk_score < 0.68:
            command = 'GO'
        elif decision_index >= 0.10:
            command = 'ADJUST'
        else:
            command = 'STOP'

        roi_multiple = max(value.get('roi_multiple', 0), perf.get('current_roas', 0))
        confidence = int(clamp((0.55 + decision_index + (0.15 * (1 - abs(0.5 - risk_score)))), 0.35, 0.92) * 100)
        timeframe = context.get('timeframe', '30 days')
        success_metric = 'ROAS >= {:.1f} with stable lead quality'.format(max(perf.get('target_roas', 3.5), 3.5))

        channel_text = signals.get('channel', 'mixed').title() if signals.get('channel') and signals.get('channel') != 'mixed' else 'priority channels'
        action = signals.get('action', 'evaluate')
        if command == 'GO':
            if action == 'pause':
                strategy = f"Approve the pause on {channel_text} expansion and protect budget until performance and risk indicators improve."
            elif action == 'reallocate':
                strategy = f"Reallocate budget toward the strongest-performing areas within {channel_text}, using controlled weekly checkpoints to confirm the shift is improving outcomes."
            elif action == 'defend':
                strategy = f"Move forward with a focused defensive plan in {channel_text}, protecting share while keeping spend tied to efficiency guardrails."
            else:
                strategy = f"Move forward with the proposed {action} plan in {channel_text}, concentrating spend on the best-converting segments while enforcing weekly guardrails on ROAS, sentiment, and competitor response."
        elif command == 'ADJUST':
            if action == 'pause':
                strategy = f"Do a partial pause rather than a full stop: freeze the weakest activity in {channel_text}, keep only high-efficiency programs live, and reassess after one review cycle."
            elif action == 'reallocate':
                strategy = f"Reallocate in phases for {channel_text}: shift only part of the budget first, validate retention and defensive performance, then expand the move if KPIs hold."
            elif action == 'defend':
                strategy = f"Proceed with a measured defensive response in {channel_text}: tighten messaging, improve targeting, and monitor competitor reaction before committing more spend."
            else:
                strategy = f"Proceed in a phased rollout for {channel_text}: tighten targeting, creative, and measurement first, then scale only after checkpoint metrics confirm the move is working."
        else:
            if action == 'pause':
                strategy = f"Do not resume expansion yet. Maintain the pause, fix the underlying performance and risk issues, and reopen the decision only after the next review window."
            elif action == 'reallocate':
                strategy = f"Do not make the full reallocation yet. Hold the current mix, resolve the highest-risk issues, and retest the shift with a smaller pilot first."
            elif action == 'defend':
                strategy = f"Do not escalate into a broad defensive spend response yet. Protect the core accounts and messaging first, then decide whether a larger counter-move is justified."
            else:
                strategy = f"Do not fully commit to the current {action} move yet; stabilize performance and risk signals first, then revisit the decision with updated data."

        defense = (
            f"Brand risk is {sentiment.get('risk_level', 'MEDIUM').lower()}, competitor pressure is "
            f"{competitor.get('urgency_level', 'MEDIUM').lower()}, and macro conditions are "
            f"{macro.get('market_phase', 'mixed').lower()}; the plan uses staged monitoring to protect efficiency and positioning."
        )

        execution_orders = []
        if 'Performance Monitor' in analyses:
            execution_orders.append("Performance Monitor: Track ROAS, CAC, and conversion velocity daily; alert if metrics drop below target for two consecutive cycles.")
        if 'Campaign Generator' in analyses:
            execution_orders.append("Campaign Generator: Prepare the primary launch variant and one lower-risk fallback variant for immediate testing.")
        if 'Creative Optimizer' in analyses:
            execution_orders.append("Creative Optimizer: Refresh headline, CTA, and proof elements before the next spend increase.")
        if 'Content Recommender' in analyses:
            stage = content.get('current_stage', 'consideration')
            execution_orders.append(f"Content Recommender: Push {stage}-stage assets to improve lead progression before the next scaling checkpoint.")
        if 'Competitor Intelligence' in analyses:
            execution_orders.append("Competitor Intelligence: Monitor rival offers and message shifts weekly; escalate if threat level rises materially.")
        if 'Smart Lead Scorer' in analyses:
            execution_orders.append("Smart Lead Scorer: Re-prioritize the active pipeline so outreach focuses on the highest-conversion leads first.")
        if not execution_orders:
            execution_orders = [
                "Performance Monitor: Establish daily KPI monitoring.",
                "Campaign Generator: Prepare a phased execution plan."
            ]

        rationale = (
            f"The recommendation is based on growth={growth_score:.2f}, efficiency={efficiency_score:.2f}, and risk={risk_score:.2f}. "
            f"Lead quality and value indicators are {lead.get('priority', 'mixed').lower()} / {value.get('value_tier', 'mixed').lower()}, "
            f"while performance is {perf.get('performance_status', 'mixed').lower()} against the current target. "
            f"The request intent is {signals.get('action', 'evaluate')} with a requested change of {signals.get('change_pct', 0)}% and a {signals.get('objective', 'growth')} objective."
        )

        return {
            'command': command,
            'strategy': strategy,
            'prediction': {
                'expected_roi': f"{roi_multiple:.1f}x return",
                'confidence_score': f"{confidence}%",
                'timeframe': timeframe,
                'success_metric': success_metric
            },
            'defense': defense,
            'execution_orders': execution_orders[:5],
            'rationale': rationale,
            'scores': {
                'growth': round(growth_score, 2),
                'risk': round(risk_score, 2),
                'efficiency': round(efficiency_score, 2),
                'decision_index': round(decision_index, 2)
            },
            'summary': {
                'query': query,
                'agents_used': [arg['agent_name'] for arg in agent_arguments],
                'query_signals': signals
            }
        }

    def _format_decision_payload(self, payload: Dict) -> str:
        lines = [
            f"COMMAND: {payload['command']}",
            "",
            "THE STRATEGY",
            payload['strategy'],
            "",
            "THE PREDICTION",
            f"Expected ROI: {payload['prediction']['expected_roi']}",
            f"Confidence Score: {payload['prediction']['confidence_score']}",
            f"Timeframe: {payload['prediction']['timeframe']}",
            f"Key Success Metric: {payload['prediction']['success_metric']}",
            "",
            "THE DEFENSE",
            payload['defense'],
            "",
            "EXECUTION ORDERS"
        ]

        for order in payload['execution_orders']:
            lines.append(f"- {order}")

        lines.extend([
            "",
            "RATIONALE",
            payload['rationale']
        ])

        return "\n".join(lines)

    def run_strategic_huddle(self, query: str, context: Dict, data: Optional[Dict] = None) -> Dict:
        """Execute full strategic decision-making process"""
        
        # Reset conversation state
        self.csa.reset_huddle()
        
        # Emit progress (if socketio is available)
        try:
            socketio.emit('huddle_status', {'phase': 'opening', 'message': 'CSA opening strategic huddle...'})
        except:
            pass
        
        # Step 1: CSA opens the huddle
        opening = self.csa.open_huddle(query, context)
        
        # Step 2: Identify required agents
        required_agents = self._select_agents(query, self.csa.parse_agent_requirements(opening))
        
        # Fallback to default agents if parsing fails
        if not required_agents or len(required_agents) < 2:
            required_agents = [
                'smart_lead_scorer',
                'lead_value_predictor',
                'competitor_intelligence',
                'performance_monitor',
                'creative_optimizer'
            ]
        
        try:
            socketio.emit('huddle_status', {
                'phase': 'agents_identified',
                'agents': [self.agents[a].agent_name for a in required_agents if a in self.agents],
                'message': f'Consulting {len(required_agents)} expert agents...'
            })
        except:
            pass
        
        # Step 3: Collect arguments from each agent
        agent_arguments = []
        
        for agent_key in required_agents:
            if agent_key in self.agents:
                try:
                    try:
                        socketio.emit('agent_thinking', {
                            'agent': self.agents[agent_key].agent_name,
                            'status': 'analyzing'
                        })
                    except:
                        pass
                    
                    argument = self.agents[agent_key].present_case(query, context, data)
                    agent_arguments.append(argument)
                    
                    try:
                        socketio.emit('agent_complete', {
                            'agent': self.agents[agent_key].agent_name,
                            'confidence': argument.get('confidence', 0.5)
                        })
                    except:
                        pass
                    
                except Exception as e:
                    print(f"[FAIL] Agent {agent_key} failed: {e}")
        
        # Step 4: CSA synthesizes arguments
        try:
            socketio.emit('huddle_status', {'phase': 'synthesis', 'message': 'CSA synthesizing arguments...'})
        except:
            pass
        
        self.csa.synthesize_arguments(agent_arguments)
        
        # Step 5: produce deterministic executive verdict
        try:
            socketio.emit('huddle_status', {'phase': 'verdict', 'message': 'CSA issuing final verdict...'})
        except:
            pass
        
        decision_payload = self._compute_decision_payload(agent_arguments, context, query)
        verdict = {
            'role': 'CSA',
            'phase': 'FINAL_VERDICT',
            'content': self._format_decision_payload(decision_payload),
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'decision_payload': decision_payload
        }
        self.csa.conversation_state.append(verdict)
        self.csa.decision_history.append({
            'query': context.get('original_query'),
            'verdict': verdict['content'],
            'timestamp': verdict['timestamp']
        })
        
        # Guardrail integration: Parse LLM verdict for actions and evaluate risk/budget
        try:
            from guardrails import guardrail_manager
            verdict_text = verdict.get('content', '')
            orders = []
            
            # Identify line-by-line orders
            for line in verdict_text.split('\n'):
                line_stripped = line.strip()
                if line_stripped.startswith('→') or line_stripped.startswith('-') or 'order' in line_stripped.lower():
                    # Attempt to find agent and action keywords
                    target_agent = None
                    target_action = None
                    cost_amount = 0.0
                    
                    # Match agent name
                    for key, ag in self.agents.items():
                        if ag.agent_name.lower() in line_stripped.lower() or key.lower() in line_stripped.lower():
                            target_agent = ag.agent_name
                            break
                    if not target_agent:
                        if 'csa' in line_stripped.lower() or 'cmo' in line_stripped.lower():
                            target_agent = "CentralStrategyAgent"
                        else:
                            target_agent = "MarketingAgent"
                            
                    # Match action risk rules
                    if 'reallocate' in line_stripped.lower() or 'budget' in line_stripped.lower():
                        target_action = "reallocate_budget"
                        # Parse dollar values (e.g. $10K or $10000)
                        matches = re.findall(r'\$?(\d[\d,]*)(?:\s*|K|k)?', line_stripped)
                        for val in matches:
                            val_clean = val.replace(',', '')
                            try:
                                cost_amount = float(val_clean)
                                if 'k' in line_stripped.lower() or 'K' in line_stripped.lower():
                                    cost_amount *= 1000
                                break
                            except:
                                pass
                    elif 'launch' in line_stripped.lower() or 'campaign' in line_stripped.lower():
                        target_action = "launch_new_campaign"
                    elif 'draft' in line_stripped.lower() or 'copy' in line_stripped.lower():
                        target_action = "draft_campaign_copy"
                    elif 'pause' in line_stripped.lower():
                        target_action = "pause_campaign"
                        
                    if target_action:
                        orders.append({
                            "agent": target_agent,
                            "action": target_action,
                            "params": {"amount": cost_amount, "description": line_stripped}
                        })
            
            # Intercept orders
            for ord in orders:
                res = guardrail_manager.request_agent_action(ord["agent"], ord["action"], ord["params"])
                if res.get("status") == "pending_human_approval":
                    socketio.emit('action_pending', res)
                elif res.get("status") == "denied":
                    socketio.emit('security_alert', {
                        'type': 'budget_denied',
                        'message': f"Blocked action '{ord['action']}' for agent '{ord['agent']}': {res['reason']}"
                    })
            
            # Emit latest security stats
            socketio.emit('security_update', guardrail_manager.get_security_status())
        except Exception as e:
            print(f"Error executing guardrails parser: {e}")

        try:
            socketio.emit('huddle_complete', {
                'verdict': verdict['content'],
                'timestamp': verdict['timestamp']
            })
        except:
            pass
        
        return {
            'verdict': verdict,
            'decision_payload': decision_payload,
            'full_transcript': self.csa.get_huddle_transcript(),
            'agent_analyses': agent_arguments,
            'agents_consulted': len(agent_arguments)
        }


# =========================================================================
# FLASK APPLICATION
# =========================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'strategic-certainty-engine-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize the engine globally
try:
    sce = StrategicCertaintyEngine()
except Exception as e:
    print(f"[FAIL] FATAL: Engine initialization failed: {e}")
    sce = None

# =========================================================================
# REST API ENDPOINTS
# =========================================================================

@app.route('/')
def index():
    """Render main UI"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if sce is None:
        return jsonify({'status': 'error', 'message': 'Engine not initialized'}), 500
    
    return jsonify({
        'status': 'healthy',
        'agents': list(sce.agents.keys()),
        'total_agents': len(sce.agents),
        'llm_available': LLM_AVAILABLE,
        'ml_available': ML_AVAILABLE
    })

@app.route('/api/strategic-huddle', methods=['POST'])
def run_strategic_huddle():
    """Main endpoint for strategic huddle execution"""
    
    if sce is None:
        return jsonify({'status': 'error', 'message': 'Engine not initialized'}), 500
    
    try:
        req_data = request.json or {}
        
        query = (req_data.get('query') or 'Should we increase marketing budget?').strip()
        
        # Guardrail: Screen input query for prompt injection
        from guardrails import screen_external_input, guardrail_manager
        screen_res = screen_external_input("user_query", query)
        if screen_res["flagged"]:
            guardrail_manager.record_blocked_injection("user_query", query, screen_res["matched_patterns"])
            try:
                socketio.emit('security_alert', {
                    'type': 'prompt_injection',
                    'message': f"Blocked prompt injection in query: {', '.join(screen_res['matched_patterns'])}",
                    'query': query
                })
                socketio.emit('security_update', guardrail_manager.get_security_status())
            except Exception as e:
                print(f"Socket emit failed: {e}")
            return jsonify({
                'status': 'blocked',
                'reason': 'Prompt injection detected',
                'matched_patterns': screen_res["matched_patterns"]
            }), 400
            
        context = {
            'goal_mode': req_data.get('goal_mode', 'Max Growth'),
            'risk_tolerance': req_data.get('risk_tolerance', 'Medium'),
            'budget': req_data.get('budget', 50000),
            'timeframe': req_data.get('timeframe', '30 days'),
            'original_query': query
        }
        data = build_scenario_data(query, req_data, context)
        context['query_signals'] = data.get('query_signals', {})
        
        # Run the huddle
        result = sce.run_strategic_huddle(query, context, data)
        
        # Parse the verdict
        verdict_content = result['verdict']['content']
        command = extract_command(verdict_content)
        
        return jsonify({
            'status': 'success',
            'command': result.get('decision_payload', {}).get('command', command),
            'verdict_full': verdict_content,
            'decision_payload': result.get('decision_payload', {}),
            'agents_consulted': result['agents_consulted'],
            'timestamp': result['verdict']['timestamp'],
            'transcript_length': len(result['full_transcript'])
        })
        
    except Exception as e:
        print(f"[FAIL] Error in strategic huddle: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/security/status', methods=['GET'])
def get_security_status():
    """Retrieve all guardrail statuses and logs"""
    from guardrails import guardrail_manager
    return jsonify(guardrail_manager.get_security_status())

@app.route('/api/security/approve', methods=['POST'])
def approve_security_action():
    """Approve a pending high-risk action"""
    from guardrails import guardrail_manager
    data = request.json or {}
    action_id = data.get("id")
    if not action_id:
        return jsonify({"status": "error", "message": "Missing action ID"}), 400
    
    result = guardrail_manager.approve_action(action_id)
    if result.get("status") == "executed":
        try:
            socketio.emit('security_update', guardrail_manager.get_security_status())
            socketio.emit('huddle_status', {
                'phase': 'action_executed',
                'message': f"Action {action_id} approved and executed successfully."
            })
        except Exception as e:
            print(f"Socket emit failed: {e}")
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/security/deny', methods=['POST'])
def deny_security_action():
    """Deny a pending high-risk action"""
    from guardrails import guardrail_manager
    data = request.json or {}
    action_id = data.get("id")
    reason = data.get("reason", "Denied by user")
    if not action_id:
        return jsonify({"status": "error", "message": "Missing action ID"}), 400
    
    result = guardrail_manager.deny_action(action_id, reason)
    if result.get("status") == "denied":
        try:
            socketio.emit('security_update', guardrail_manager.get_security_status())
            socketio.emit('huddle_status', {
                'phase': 'action_denied',
                'message': f"Action {action_id} was denied by user."
            })
        except Exception as e:
            print(f"Socket emit failed: {e}")
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get list of all available agents"""
    if sce is None:
        return jsonify({'status': 'error', 'agents': []}), 500
    agents_info = []
    
    for key, agent in sce.agents.items():
        cluster = 'unknown'
        if 'lead' in key or 'enrichment' in key or 'scorer' in key or 'value' in key:
            cluster = 'Lead Intelligence'
        elif 'campaign' in key or 'content' in key or 'creative' in key:
            cluster = 'Execution & Optimization'
        elif 'performance' in key or 'sentiment' in key or 'competitor' in key:
            cluster = 'Defense & Performance'
        elif 'macro' in key or 'trend' in key:
            cluster = 'Strategy & Insights'
        
        agents_info.append({
            'id': key,
            'name': agent.agent_name,
            'role': agent.agent_role,
            'cluster': cluster
        })
    
    return jsonify({
        'status': 'success',
        'total': len(agents_info),
        'agents': agents_info
    })

@app.route('/api/quick-decision', methods=['POST'])
def quick_decision():
    """Quick decision endpoint with minimal input"""
    
    if sce is None:
        return jsonify({'status': 'error', 'message': 'Engine not initialized'}), 500
    
    try:
        req_data = request.json or {}
        query = (req_data.get('query') or 'Should we proceed with this campaign?').strip()
        
        # Use defaults
        context = {
            'goal_mode': 'Balanced',
            'risk_tolerance': 'Medium',
            'budget': 50000,
            'timeframe': '30 days',
            'original_query': query
        }
        
        data = build_scenario_data(query, req_data, context)
        context['query_signals'] = data.get('query_signals', {})
        result = sce.run_strategic_huddle(query, context, data)
        
        verdict_content = result['verdict']['content']
        command = extract_command(verdict_content)
        
        return jsonify({
            'status': 'success',
            'command': command,
            'verdict': verdict_content
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =========================================================================
# WEBSOCKET EVENTS
# =========================================================================

@socketio.on('connect')
def handle_connect():
    print('[OK] Client connected')
    emit('connection_status', {
        'status': 'connected',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('[FAIL] Client disconnected')

@socketio.on('start_huddle')
def handle_start_huddle(data):
    """Handle real-time huddle via WebSocket"""
    
    if sce is None:
        emit('error', {'message': 'Engine not initialized'})
        return
    
    try:
        query = (data.get('query') or 'Should we increase budget?').strip()
        context = {
            'goal_mode': data.get('goal_mode', 'Max Growth'),
            'risk_tolerance': data.get('risk_tolerance', 'Medium'),
            'budget': data.get('budget', 50000),
            'timeframe': data.get('timeframe', '30 days'),
            'original_query': query
        }
        scenario_data = build_scenario_data(query, data, context)
        context['query_signals'] = scenario_data.get('query_signals', {})
        result = sce.run_strategic_huddle(query, context, scenario_data)
        
        emit('huddle_result', {
            'status': 'success',
            'verdict': result['verdict']['content'],
            'agents_consulted': result['agents_consulted']
        })
        
    except Exception as e:
        emit('error', {'message': str(e)})

# =========================================================================
# HTML TEMPLATE (BEAUTIFUL MODERN UI)
# =========================================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Strategic Certainty Engine - AI Marketing Command Center</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #00ff88;
            --secondary: #0066ff;
            --dark: #0a0e1a;
            --card: #151925;
            --text: #e0e6f0;
            --text-dim: #8b95a8;
            --success: #00ff88;
            --warning: #ffd93d;
            --danger: #ff6b6b;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 100%);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 2rem 0;
            border-bottom: 1px solid rgba(0, 255, 136, 0.1);
            margin-bottom: 3rem;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            font-weight: 800;
            box-shadow: 0 8px 32px rgba(0, 255, 136, 0.3);
        }
        
        .logo-text h1 {
            font-size: 2rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            letter-spacing: -1px;
        }
        
        .logo-text p {
            font-size: 0.9rem;
            color: var(--text-dim);
            margin-top: 0.25rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid var(--primary);
            border-radius: 50px;
            font-size: 0.9rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--primary);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        
        /* Main Grid */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        /* Card */
        .card {
            background: var(--card);
            border: 1px solid rgba(0, 255, 136, 0.1);
            border-radius: 24px;
            padding: 2rem;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: var(--primary);
            box-shadow: 0 8px 32px rgba(0, 255, 136, 0.1);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .card-title {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .card-icon {
            font-size: 1.8rem;
        }
        
        /* Form */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-dim);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .form-input,
        .form-select,
        .form-textarea {
            width: 100%;
            padding: 1rem 1.25rem;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-input:focus,
        .form-select:focus,
        .form-textarea:focus {
            outline: none;
            border-color: var(--primary);
            background: rgba(0, 255, 136, 0.05);
        }
        
        .form-textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        /* Button */
        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Inter', sans-serif;
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--dark);
            box-shadow: 0 4px 16px rgba(0, 255, 136, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 255, 136, 0.4);
        }
        
        .btn-primary:active {
            transform: translateY(0);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-full {
            width: 100%;
            justify-content: center;
        }
        
        /* Agent Grid */
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .agent-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .agent-card.active {
            border-color: var(--primary);
            background: rgba(0, 255, 136, 0.1);
        }
        
        .agent-card.thinking {
            border-color: var(--warning);
            animation: thinking 1.5s infinite;
        }
        
        @keyframes thinking {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        .agent-card.complete {
            border-color: var(--success);
            background: rgba(0, 255, 136, 0.05);
        }
        
        .agent-emoji {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .agent-name {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text);
        }
        
        .agent-status {
            font-size: 0.75rem;
            color: var(--text-dim);
            margin-top: 0.25rem;
        }
        
        /* Progress */
        .progress-container {
            margin: 1.5rem 0;
        }
        
        .progress-label {
            font-size: 0.9rem;
            color: var(--text-dim);
            margin-bottom: 0.5rem;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 50px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            border-radius: 50px;
            transition: width 0.5s ease;
        }
        
        /* Verdict Display */
        .verdict-container {
            background: rgba(0, 0, 0, 0.4);
            border: 2px solid var(--primary);
            border-radius: 16px;
            padding: 2rem;
            margin-top: 2rem;
            display: none;
        }
        
        .verdict-container.show {
            display: block;
            animation: slideUp 0.5s ease;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .verdict-command {
            display: inline-block;
            padding: 0.75rem 2rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--dark);
            font-size: 1.5rem;
            font-weight: 800;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }
        
        .verdict-content {
            font-size: 0.95rem;
            line-height: 1.8;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Courier New', monospace;
        }

        .verdict-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 0 0 1.5rem 0;
        }

        .verdict-metric {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 1rem;
        }

        .verdict-metric-label {
            color: var(--text-dim);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.35rem;
        }

        .verdict-metric-value {
            color: var(--text);
            font-size: 1rem;
            font-weight: 700;
        }
        
        /* Loading */
        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(0, 255, 136, 0.2);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Toast */
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--card);
            border: 1px solid var(--primary);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            display: none;
            z-index: 1000;
        }
        
        .toast.show {
            display: block;
            animation: slideInRight 0.3s ease;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        /* Responsive */
        @media (max-width: 1024px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <div class="logo-icon">Ξ</div>
                <div class="logo-text">
                    <h1>Strategic Certainty Engine</h1>
                    <p>AI-Powered Multi-Agent Marketing Command Center</p>
                </div>
            </div>
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span id="statusText">System Ready</span>
            </div>
        </header>
        
        <div class="main-grid">
            <!-- Left Column: Control Panel -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">🎯</span>
                        Strategic Query
                    </h2>
                </div>
                
                <form id="huddleForm">
                    <div class="form-group">
                        <label class="form-label">Your Strategic Question</label>
                        <textarea 
                            class="form-textarea" 
                            id="queryInput" 
                            placeholder="e.g., Should we increase our LinkedIn campaign budget by 50%?"
                            required
                        >Should we increase our LinkedIn campaign budget by 50% to capture more enterprise leads?</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Goal Mode</label>
                        <select class="form-select" id="goalMode">
                            <option value="Max Growth">Max Growth</option>
                            <option value="Balanced">Balanced</option>
                            <option value="Conservative">Conservative</option>
                            <option value="Experimental">Experimental</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Risk Tolerance</label>
                        <select class="form-select" id="riskTolerance">
                            <option value="High">High</option>
                            <option value="Medium" selected>Medium</option>
                            <option value="Low">Low</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Budget ($)</label>
                        <input 
                            type="number" 
                            class="form-input" 
                            id="budgetInput" 
                            value="50000" 
                            min="0" 
                            step="1000"
                        >
                    </div>

                    <div class="form-group">
                        <label class="form-label">Current ROAS</label>
                        <input type="number" class="form-input" id="currentRoasInput" value="3.8" min="0" step="0.1">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Target ROAS</label>
                        <input type="number" class="form-input" id="targetRoasInput" value="3.5" min="0" step="0.1">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Lead Quality Score (0-100)</label>
                        <input type="number" class="form-input" id="leadScoreInput" value="72" min="0" max="100" step="1">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Brand Health (1-10)</label>
                        <input type="number" class="form-input" id="brandHealthInput" value="7.0" min="1" max="10" step="0.1">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Competitor Threat (1-10)</label>
                        <input type="number" class="form-input" id="competitorThreatInput" value="6" min="1" max="10" step="1">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Audience Segment</label>
                        <select class="form-select" id="audienceSegment">
                            <option value="Enterprise Buyers">Enterprise Buyers</option>
                            <option value="Mid-Market Teams">Mid-Market Teams</option>
                            <option value="SMB Owners">SMB Owners</option>
                            <option value="Existing Customers">Existing Customers</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Market Phase</label>
                        <select class="form-select" id="marketPhase">
                            <option value="">Auto-detect</option>
                            <option value="GROWTH">Growth</option>
                            <option value="RECOVERY">Recovery</option>
                            <option value="PEAK">Peak</option>
                            <option value="CONTRACTION">Contraction</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn btn-primary btn-full" id="startHuddleBtn">
                        <span>🚀</span>
                        <span>Start Strategic Huddle</span>
                    </button>
                </form>
                
                <div class="progress-container" id="progressContainer" style="display: none;">
                    <div class="progress-label" id="progressLabel">Initializing huddle...</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                    </div>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p id="loadingText">AI agents are deliberating...</p>
                </div>
                
                <div class="verdict-container" id="verdictContainer">
                    <div class="verdict-command" id="verdictCommand">GO</div>
                    <div class="verdict-grid">
                        <div class="verdict-metric">
                            <div class="verdict-metric-label">Expected ROI</div>
                            <div class="verdict-metric-value" id="verdictRoi">-</div>
                        </div>
                        <div class="verdict-metric">
                            <div class="verdict-metric-label">Confidence</div>
                            <div class="verdict-metric-value" id="verdictConfidence">-</div>
                        </div>
                        <div class="verdict-metric">
                            <div class="verdict-metric-label">Timeframe</div>
                            <div class="verdict-metric-value" id="verdictTimeframe">-</div>
                        </div>
                        <div class="verdict-metric">
                            <div class="verdict-metric-label">Success Metric</div>
                            <div class="verdict-metric-value" id="verdictMetric">-</div>
                        </div>
                    </div>
                    <div class="verdict-content" id="verdictContent"></div>
                </div>
            </div>
            
            <!-- Right Column: Agent Status -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">🤖</span>
                        AI Agent Network
                    </h2>
                </div>
                
                <div class="agents-grid" id="agentsGrid">
                    <div class="agent-card" data-agent="smart_lead_scorer">
                        <div class="agent-emoji">🎯</div>
                        <div class="agent-name">Lead Scorer</div>
                        <div class="agent-status">Ready</div>
                    </div>
                    <div class="agent-card" data-agent="lead_value_predictor">
                        <div class="agent-emoji">💰</div>
                        <div class="agent-name">Value Predictor</div>
                        <div class="agent-status">Ready</div>
                    </div>
                    <div class="agent-card" data-agent="campaign_generator">
                        <div class="agent-emoji">📧</div>
                        <div class="agent-name">Campaign Gen</div>
                        <div class="agent-status">Ready</div>
                    </div>
                    <div class="agent-card" data-agent="creative_optimizer">
                        <div class="agent-emoji">🎨</div>
                        <div class="agent-name">Creative Opt</div>
                        <div class="agent-status">Ready</div>
                    </div>
                    <div class="agent-card" data-agent="performance_monitor">
                        <div class="agent-emoji">📊</div>
                        <div class="agent-name">Performance</div>
                        <div class="agent-status">Ready</div>
                    </div>
                    <div class="agent-card" data-agent="sentiment_tracker">
                        <div class="agent-emoji">😊</div>
                        <div class="agent-name">Sentiment</div>
                        <div class="agent-status">Ready</div>
                    </div>
                    <div class="agent-card" data-agent="competitor_intelligence">
                        <div class="agent-emoji">🔍</div>
                        <div class="agent-name">Competitor</div>
                        <div class="agent-status">Ready</div>
                    </div>
                    <div class="agent-card" data-agent="macro_trend_analyzer">
                        <div class="agent-emoji">📈</div>
                        <div class="agent-name">Macro Trends</div>
                        <div class="agent-status">Ready</div>
                    </div>
                </div>
                
                <div style="margin-top: 2rem; padding-top: 2rem; border-top: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="font-size: 1rem; margin-bottom: 1rem; color: var(--text-dim);">System Info</h3>
                    <div style="font-size: 0.85rem; line-height: 1.8; color: var(--text-dim);">
                        <div><strong>Total Agents:</strong> <span id="totalAgents">10</span></div>
                        <div><strong>LLM Status:</strong> <span id="llmStatus">Connected</span></div>
                        <div><strong>Last Decision:</strong> <span id="lastDecision">None</span></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast">
        <div id="toastMessage"></div>
    </div>
    
    <script>
        const API_BASE = `${window.location.origin}/api`;
        const socket = io(window.location.origin);
        
        // Elements
        const huddleForm = document.getElementById('huddleForm');
        const startHuddleBtn = document.getElementById('startHuddleBtn');
        const loading = document.getElementById('loading');
        const verdictContainer = document.getElementById('verdictContainer');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressLabel = document.getElementById('progressLabel');

        function renderVerdict(result) {
            const payload = result.decision_payload || {};
            const prediction = payload.prediction || {};

            document.getElementById('verdictCommand').textContent = result.command || payload.command || 'ADJUST';
            document.getElementById('verdictContent').textContent = result.verdict_full || '';
            document.getElementById('verdictRoi').textContent = prediction.expected_roi || '-';
            document.getElementById('verdictConfidence').textContent = prediction.confidence_score || '-';
            document.getElementById('verdictTimeframe').textContent = prediction.timeframe || '-';
            document.getElementById('verdictMetric').textContent = prediction.success_metric || '-';
            verdictContainer.classList.add('show');
        }
        
        // Socket.IO event handlers
        socket.on('connect', () => {
            console.log('WebSocket connected');
            showToast('✅ Connected to Strategic Engine');
        });
        
        socket.on('huddle_status', (data) => {
            console.log('Huddle status:', data);
            progressLabel.textContent = data.message;
            
            const phases = ['opening', 'agents_identified', 'synthesis', 'verdict'];
            const currentIndex = phases.indexOf(data.phase);
            const progress = ((currentIndex + 1) / phases.length) * 100;
            progressFill.style.width = progress + '%';
        });
        
        socket.on('agent_thinking', (data) => {
            console.log('Agent thinking:', data);
            const agentCards = document.querySelectorAll('.agent-card');
            agentCards.forEach(card => {
                const agentName = card.querySelector('.agent-name').textContent;
                if (data.agent.includes(agentName.split(' ')[0])) {
                    card.classList.add('thinking');
                    card.querySelector('.agent-status').textContent = 'Analyzing...';
                }
            });
        });
        
        socket.on('agent_complete', (data) => {
            console.log('Agent complete:', data);
            const agentCards = document.querySelectorAll('.agent-card');
            agentCards.forEach(card => {
                const agentName = card.querySelector('.agent-name').textContent;
                if (data.agent.includes(agentName.split(' ')[0])) {
                    card.classList.remove('thinking');
                    card.classList.add('complete');
                    card.querySelector('.agent-status').textContent = 'Complete ✓';
                }
            });
        });
        
        socket.on('huddle_complete', (data) => {
            console.log('Huddle complete:', data);
            showToast('✅ Strategic decision made!');
        });
        
        // Form submission
        huddleForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const query = document.getElementById('queryInput').value;
            const goalMode = document.getElementById('goalMode').value;
            const riskTolerance = document.getElementById('riskTolerance').value;
            const budget = parseInt(document.getElementById('budgetInput').value);
            const currentRoas = parseFloat(document.getElementById('currentRoasInput').value);
            const targetRoas = parseFloat(document.getElementById('targetRoasInput').value);
            const leadScore = parseFloat(document.getElementById('leadScoreInput').value);
            const brandHealth = parseFloat(document.getElementById('brandHealthInput').value);
            const competitorThreat = parseInt(document.getElementById('competitorThreatInput').value);
            const audienceSegment = document.getElementById('audienceSegment').value;
            const marketPhase = document.getElementById('marketPhase').value;
            
            // Reset UI
            verdictContainer.classList.remove('show');
            document.querySelectorAll('.agent-card').forEach(card => {card.classList.remove('active', 'thinking', 'complete');
                card.querySelector('.agent-status').textContent = 'Ready';
            });
            
            // Show loading
            startHuddleBtn.disabled = true;
            startHuddleBtn.innerHTML = '<span>⏳</span><span>Running Huddle...</span>';
            loading.classList.add('show');
            progressContainer.style.display = 'block';
            progressFill.style.width = '0%';
            
            try {
                const response = await fetch(`${API_BASE}/strategic-huddle`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: query,
                        goal_mode: goalMode,
                        risk_tolerance: riskTolerance,
                        budget: budget,
                        current_roas: currentRoas,
                        target_roas: targetRoas,
                        lead_score: leadScore,
                        brand_health: brandHealth,
                        competitor_threat: competitorThreat,
                        audience_segment: audienceSegment,
                        market_phase: marketPhase
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    renderVerdict(result);
                    
                    // Update system info
                    document.getElementById('lastDecision').textContent = new Date().toLocaleTimeString();
                    document.getElementById('statusText').textContent = `Last decision: ${result.command}`;
                    
                    // Complete progress
                    progressFill.style.width = '100%';
                    progressLabel.textContent = 'Strategic decision complete!';
                    
                    showToast(`✅ Decision: ${result.command}`);
                } else {
                    showToast('❌ Error: ' + result.message);
                }
                
            } catch (error) {
                console.error('Error:', error);
                showToast('❌ Failed to run strategic huddle');
            } finally {
                loading.classList.remove('show');
                startHuddleBtn.disabled = false;
                startHuddleBtn.innerHTML = '<span>🚀</span><span>Start Strategic Huddle</span>';
            }
        });
        
        // Toast notification
        function showToast(message) {
            const toast = document.getElementById('toast');
            const toastMessage = document.getElementById('toastMessage');
            
            toastMessage.textContent = message;
            toast.classList.add('show');
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 4000);
        }
        
        // Load system info on page load
        async function loadSystemInfo() {
            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();
                
                if (data.status === 'healthy') {
                    document.getElementById('totalAgents').textContent = data.total_agents;
                    document.getElementById('llmStatus').textContent = data.llm_available ? 'Connected ✓' : 'Template Mode';
                }
            } catch (error) {
                console.error('Failed to load system info:', error);
            }
        }
        
        // Initialize
        loadSystemInfo();
        
        // Example queries for quick testing
        const exampleQueries = [
            "Should we increase our LinkedIn campaign budget by 50% to capture more enterprise leads?",
            "Is now the right time to launch a new product campaign given current market conditions?",
            "Should we shift 30% of our budget from Facebook to TikTok for Gen Z targeting?",
            "Can we scale our email nurture campaigns without hurting deliverability?",
            "Should we pause our competitor comparison ads due to negative sentiment?"
        ];
        
        // Add quick example buttons (optional)
        let exampleIndex = 0;
        document.getElementById('queryInput').addEventListener('dblclick', () => {
            document.getElementById('queryInput').value = exampleQueries[exampleIndex];
            exampleIndex = (exampleIndex + 1) % exampleQueries.length;
            showToast('💡 Example query loaded');
        });
    </script>
</body>
</html>
'''

# =========================================================================
# MAIN EXECUTION
# =========================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("[START] STRATEGIC CERTAINTY ENGINE - LAUNCHING")
    print("="*80)
    print("\n? Features:")
    print("  [OK] 11 Specialized AI Agents")
    print("  [OK] Central Strategy Agent (CSA) Orchestrator")
    print("  [OK] Real-time Strategic Huddles")
    print("  [OK] WebSocket Support")
    print("  [OK] Beautiful Modern UI")
    print(f"\n[CONFIG] Configuration:")
    print(f"  ? LLM: {'Groq (Connected)' if LLM_AVAILABLE else 'Template Mode'}")
    print(f"  ? ML: {'Available' if ML_AVAILABLE else 'Rule-based'}")
    print(f"  ? Port: 5010")
    
    if sce is None:
        print("\n[FAIL] CRITICAL FAILURE: Engine cannot start. Check logs above.")
        exit(1)
    
    print("\n" + "="*80)
    print("? SERVER RUNNING")
    print("="*80)
    print("  [URL] Web UI: http://localhost:5010")
    print("  ? API: http://localhost:5010/api/strategic-huddle")
    print("  [HEALTH]  Health: http://localhost:5010/api/health")
    print("\n[TIP] Tip: Double-click the query box to load example questions")
    print("="*80 + "\n")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5010, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n[BYE] Shutting down Strategic Certainty Engine...")
    except Exception as e:
        print(f"\n[FAIL] Fatal error: {e}")
        import traceback
        traceback.print_exc()
