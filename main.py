# app.py - AI-Powered Content Generation Agent with FREE Groq API

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
import time

app = Flask(__name__)
CORS(app)

# Email Configuration
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@example.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SIMULATED_USER_EMAIL = os.getenv("SIMULATED_USER_EMAIL", "user@example.com")

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def generate_content_with_ai(domain, user_email):
    """
    Uses Groq's FREE and FAST API to generate personalized financial content.
    Returns a dictionary with title, short_description, and full_content_html.
    """
    
    prompt = f"""You are writing a personalized, helpful email about {domain} to someone who's interested. Make it feel like a 1-on-1 message from a helpful team, not a marketing blast.

Generate content with this structure:

1. SUBJECT LINE:
   - Personal and relevant
   - Example: "3 ways to get started with {domain} 💡" or "here's what you need for {domain}"

2. GREETING (1-2 sentences - warm & personal):
   - Address them personally
   - Acknowledge their interest
   - Example: "Hey there! 👋 We noticed you're interested in {domain} - that's awesome. Here's some stuff that'll actually help you get started."

3. VALUE STATEMENT (1-2 sentences):
   - Explain why you're sending this
   - What benefit they'll get
   - Example: "Getting started with {domain} can feel overwhelming, but it doesn't have to be. We've put together some resources and tools that make it way easier."

4. MAIN CONTENT - 3 RECOMMENDATIONS:
   Format as a bulleted list:

   • **[Platform/Tool Name]** - [what it does in simple terms]
   
     why it helps: [specific benefit]
     best for: [who should use it]
     → [Learn more] or [Get started]

   • **[Platform/Tool Name]** - [what it does in simple terms]
   
     why it helps: [specific benefit]  
     best for: [who should use it]
     → [Learn more] or [Get started]

   • **[Platform/Tool Name]** - [what it does in simple terms]
   
     why it helps: [specific benefit]
     best for: [who should use it]
     → [Learn more] or [Get started]

5. CLEAR CALL-TO-ACTION (1 sentence + button text):
   - One simple action to take
   - Example: "Ready to start? Pick one that fits you best and give it a try."
   - Button: "Explore {domain} tools →" or "Get started today →"

6. FRIENDLY SIGN-OFF (2-3 sentences):
   - Personal closing
   - Offer help
   - Encouraging tone
   - Example: "We're here if you need any help getting started. Just reply to this email - we actually read them! You've got this 💪"

7. SIGNATURE:
   - Name + Team name
   - Example: "Sarah and the [Your Brand] Team" or "The {domain} Team"

8. P.S. (Optional - 1 sentence):
   - Add extra value or tip
   - Example: "P.S. Most people start with [specific tool] - it's the easiest one to set up!"

EMAIL STYLE:
✅ Write like a 1-on-1 conversation
✅ Use "you" and "your" throughout
✅ Friendly, not corporate
✅ Helpful, not pushy
✅ Use emojis sparingly (2-3 max in whole email)
✅ Short paragraphs (2-3 sentences max)
✅ Clear formatting with bullets
✅ Actionable recommendations
✅ Personal tone like Buffer's example


GO!"""
    try:
        print(f"[AGENT] Generating AI content for: {domain}")
        print(f"? Using Groq's ultra-fast AI model...")
        
        # Make API request to Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert financial content writer who creates comprehensive, educational, and actionable financial guides. Your content is always well-structured, professional, and easy to understand."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",  # Fast and high-quality model
            temperature=0.7,
            max_tokens=2500,
            top_p=0.9
        )
        
        generated_text = chat_completion.choices[0].message.content
        
        print(f"[OK] Content generated successfully!")
        
        # Parse the response
        title = f"Expert Guide to {domain}"
        description = f"Comprehensive insights and strategies for mastering {domain.lower()}."
        content_body = generated_text
        
        # Extract title, description, and content
        lines = generated_text.split('\n')
        title_found = False
        desc_found = False
        content_start_idx = 0
        
        for i, line in enumerate(lines):
            clean_line = line.strip()
            if clean_line.upper().startswith('TITLE:'):
                title = clean_line.split(':', 1)[1].strip()
                title_found = True
            elif clean_line.upper().startswith('DESCRIPTION:'):
                description = clean_line.split(':', 1)[1].strip()
                desc_found = True
            elif clean_line.upper().startswith('CONTENT:'):
                content_start_idx = i + 1
                break
        
        # Extract the main content
        if content_start_idx > 0:
            content_body = '\n'.join(lines[content_start_idx:]).strip()
        
        # Process content into HTML paragraphs
        paragraphs = []
        current_para = []
        
        for line in content_body.split('\n'):
            line = line.strip()
            if line:
                # Check if it's a heading (starts with ##, #, or is all caps with few words)
                if line.startswith('##'):
                    if current_para:
                        paragraphs.append(('p', ' '.join(current_para)))
                        current_para = []
                    paragraphs.append(('h2', line.replace('##', '').strip()))
                elif line.startswith('#'):
                    if current_para:
                        paragraphs.append(('p', ' '.join(current_para)))
                        current_para = []
                    paragraphs.append(('h2', line.replace('#', '').strip()))
                elif line.isupper() and len(line.split()) <= 8:
                    if current_para:
                        paragraphs.append(('p', ' '.join(current_para)))
                        current_para = []
                    paragraphs.append(('h2', line))
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    if current_para:
                        paragraphs.append(('p', ' '.join(current_para)))
                        current_para = []
                    paragraphs.append(('li', line.lstrip('-•* ').strip()))
                else:
                    current_para.append(line)
            else:
                if current_para:
                    paragraphs.append(('p', ' '.join(current_para)))
                    current_para = []
        
        if current_para:
            paragraphs.append(('p', ' '.join(current_para)))
        
        # Build HTML content
        html_content_body = ""
        in_list = False
        
        for tag, text in paragraphs:
            if tag == 'h2':
                if in_list:
                    html_content_body += "</ul>"
                    in_list = False
                html_content_body += f"<h2>{text}</h2>"
            elif tag == 'li':
                if not in_list:
                    html_content_body += "<ul>"
                    in_list = True
                html_content_body += f"<li>{text}</li>"
            elif tag == 'p':
                if in_list:
                    html_content_body += "</ul>"
                    in_list = False
                html_content_body += f"<p>{text}</p>"
        
        if in_list:
            html_content_body += "</ul>"
        
        # Create beautiful HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.8;
                    color: #333;
                    background-color: #f5f7fa;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    max-width: 700px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2em;
                    font-weight: 700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .header .subtitle {{
                    margin-top: 10px;
                    font-size: 0.95em;
                    opacity: 0.95;
                }}
                .content {{
                    padding: 40px 35px;
                }}
                .description-box {{
                    background-color: #f0f4ff;
                    border-left: 5px solid #667eea;
                    padding: 20px 25px;
                    margin-bottom: 30px;
                    border-radius: 8px;
                }}
                .description-box p {{
                    margin: 0;
                    font-size: 1.1em;
                    color: #444;
                    font-weight: 500;
                }}
                h2 {{
                    color: #667eea;
                    font-size: 1.6em;
                    margin-top: 35px;
                    margin-bottom: 15px;
                    font-weight: 600;
                    border-bottom: 2px solid #e8ecf3;
                    padding-bottom: 10px;
                }}
                h2:first-of-type {{
                    margin-top: 0;
                }}
                p {{
                    margin-bottom: 1.3em;
                    font-size: 1.05em;
                    color: #555;
                    line-height: 1.8;
                }}
                ul {{
                    margin: 20px 0;
                    padding-left: 0;
                    list-style: none;
                }}
                li {{
                    margin-bottom: 12px;
                    padding-left: 30px;
                    position: relative;
                    font-size: 1.05em;
                    color: #555;
                    line-height: 1.7;
                }}
                li:before {{
                    content: "✓";
                    position: absolute;
                    left: 0;
                    color: #667eea;
                    font-weight: bold;
                    font-size: 1.3em;
                }}
                strong {{
                    color: #2c3e50;
                    font-weight: 600;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    border-top: 3px solid #667eea;
                }}
                .footer p {{
                    margin: 5px 0;
                    color: #666;
                    font-size: 0.9em;
                }}
                .footer .ai-badge {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 8px 20px;
                    border-radius: 20px;
                    font-weight: 600;
                    font-size: 0.85em;
                    margin-top: 10px;
                }}
                .timestamp {{
                    color: #999;
                    font-size: 0.85em;
                    font-style: italic;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>{title}</h1>
                    <div class="subtitle">🤖 AI-Generated Financial Insights</div>
                </div>
                <div class="content">
                    <div class="description-box">
                        <p><strong>Overview:</strong> {description}</p>
                    </div>
                    {html_content_body}
                </div>
                <div class="footer">
                    <div class="ai-badge">⚡ Powered by Groq AI</div>
                    <p><strong>AI Financial Assistant</strong></p>
                    <p>Personalized content generated exclusively for you</p>
                    <p class="timestamp">Generated on {time.strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p style="font-size: 0.8em; margin-top: 15px;">© 2024 AI Financial Assistant. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {
            "title": title,
            "short_description": description,
            "full_content_html": html_content
        }
            
    except Exception as e:
        print(f"[FAIL] AI generation error: {e}")
        # Fallback content
        return generate_fallback_content(domain)

def generate_fallback_content(domain):
    """
    Generates basic fallback content if AI fails.
    """
    domain_info = {
        "Investing": {
            "desc": "Learn about stocks, bonds, mutual funds, and building a diversified investment portfolio for long-term wealth creation.",
            "tips": [
                "Start with low-cost index funds for diversification",
                "Invest consistently through dollar-cost averaging",
                "Maintain a long-term perspective (5+ years)",
                "Diversify across asset classes and sectors",
                "Reinvest dividends to compound your returns",
                "Keep investment costs and fees low",
                "Rebalance your portfolio annually"
            ]
        },
        "Crypto": {
            "desc": "Understand blockchain technology, cryptocurrencies, and digital asset investment strategies in this evolving market.",
            "tips": [
                "Research thoroughly before investing in any cryptocurrency",
                "Use secure hardware wallets for storage",
                "Understand the high volatility and risk involved",
                "Never invest more than you can afford to lose",
                "Diversify across multiple cryptocurrencies",
                "Keep private keys secure and backed up",
                "Stay updated on regulatory changes"
            ]
        },
        "Budgeting": {
            "desc": "Master the art of budgeting, expense tracking, and smart money management techniques to take control of your finances.",
            "tips": [
                "Track every expense for at least one month",
                "Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings",
                "Build an emergency fund of 3-6 months expenses",
                "Automate your savings and bill payments",
                "Review and adjust your budget monthly",
                "Cut unnecessary subscriptions and expenses",
                "Use budgeting apps for easy tracking"
            ]
        },
        "Retirement": {
            "desc": "Plan for your future with retirement accounts, compound interest strategies, and long-term wealth building for financial independence.",
            "tips": [
                "Start saving for retirement as early as possible",
                "Maximize employer 401(k) matching contributions",
                "Contribute to both traditional and Roth IRAs",
                "Increase contributions by 1% annually",
                "Diversify retirement account investments",
                "Understand your Social Security benefits",
                "Consider working with a financial advisor"
            ]
        },
        "DebtManagement": {
            "desc": "Proven strategies for paying off debt, improving credit scores, and achieving financial freedom from high-interest obligations.",
            "tips": [
                "List all debts with balances and interest rates",
                "Use debt snowball or avalanche method",
                "Pay more than the minimum payment",
                "Negotiate with creditors for lower rates",
                "Avoid taking on new debt while paying off existing debt",
                "Consider debt consolidation if beneficial",
                "Create a realistic debt payoff timeline"
            ]
        }
    }
    
    info = domain_info.get(domain, {
        "desc": f"Comprehensive financial guidance and strategies for {domain}.",
        "tips": ["Research thoroughly", "Consult financial experts", "Start with small steps", "Stay consistent and disciplined"]
    })
    
    tips_html = ''.join([f'<li>{tip}</li>' for tip in info['tips']])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.8;
                color: #333;
                background-color: #f5f7fa;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 700px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2em;
            }}
            .content {{
                padding: 40px 35px;
            }}
            .description-box {{
                background-color: #f0f4ff;
                border-left: 5px solid #667eea;
                padding: 20px 25px;
                margin-bottom: 30px;
                border-radius: 8px;
            }}
            h2 {{
                color: #667eea;
                margin-top: 30px;
            }}
            ul {{
                list-style: none;
                padding-left: 0;
            }}
            li {{
                margin-bottom: 12px;
                padding-left: 30px;
                position: relative;
            }}
            li:before {{
                content: "✓";
                position: absolute;
                left: 0;
                color: #667eea;
                font-weight: bold;
                font-size: 1.3em;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Your Guide to {domain}</h1>
            </div>
            <div class="content">
                <div class="description-box">
                    <p><strong>Overview:</strong> {info['desc']}</p>
                </div>
                <h2>Key Strategies & Tips:</h2>
                <ul>{tips_html}</ul>
                <p>This is your starting point for mastering {domain.lower()}. Stay informed, be patient, and make smart decisions for your financial future.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "title": f"Your Guide to {domain}",
        "short_description": info['desc'],
        "full_content_html": html
    }

def send_email(recipient_email, subject, body_html):
    """
    Sends an HTML formatted email to the specified recipient using SMTP.
    Returns True if the email was sent successfully, False otherwise.
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient_email
        msg["Subject"] = subject

        part = MIMEText(body_html, "html")
        msg.attach(part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        print(f"[OK] Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to send email to {recipient_email}. Error: {e}")
        return False

@app.route("/")
def index():
    """Serves the main HTML page"""
    return render_template("mail.html")
@app.route('/get-engagement-data', methods=['GET'])
def get_engagement_data():
    # In a real app, fetch this from a database based on user ID
    # For now, let's return some dummy data
    labels = ['Investing', 'Budgeting', 'Crypto', 'Retirement', 'Debt Management']
    counts = [300, 250, 180, 120, 70]
    return jsonify({"labels": labels, "counts": counts})

@app.route("/get-personalized-content", methods=["POST"])
def get_personalized_content():
    """
    API endpoint to generate AI-powered personalized content and send it via email.
    """
    data = request.json
    domain = data.get("domain")
    user_email = data.get("user_email", SIMULATED_USER_EMAIL)

    if not domain:
        return jsonify({"success": False, "error": "Content domain is required."}), 400
    if not user_email:
        return jsonify({"success": False, "error": "Recipient email is required."}), 400

    print(f"\n{'='*60}")
    print(f"? REQUEST: Generating content for '{domain}'")
    print(f"[EMAIL] Recipient: {user_email}")
    print(f"{'='*60}\n")
    
    # Generate content using Groq AI
    content_data = generate_content_with_ai(domain, user_email)

    if content_data:
        email_subject = f"🎯 {content_data['title']}"
        email_sent_status = send_email(user_email, email_subject, content_data['full_content_html'])

        print(f"\n{'='*60}")
        print(f"[OK] SUCCESS: Content generated and email {'sent' if email_sent_status else 'failed'}")
        print(f"{'='*60}\n")


        return jsonify({
            "success": True,
            "personalized_content": {
                "title": content_data["title"],
                "short_description": content_data["short_description"],
                "domain": domain,
                "match_score": "⚡ AI-Generated (Groq Ultra-Fast)",
                "email_status": "sent" if email_sent_status else "failed"
            }
        })
    else:
        return jsonify({"success": False, "error": "Failed to generate content."}), 500

if __name__ == "__main__":
    print("\n" + "="*60)
    print("[START] AI FINANCIAL ASSISTANT SERVER")
    print("="*60)
    print(f"[EMAIL] Email: {EMAIL_ADDRESS}")
    print(f"[AGENT] AI Engine: Groq (Ultra-Fast & FREE)")
    print(f"? Status: Ready to generate content!")
    print("="*60 + "\n")
    app.run(debug=True, port=5004)