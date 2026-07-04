# backend/app.py

# 1. Imports
from flask import Flask, request, jsonify
from flask_cors import CORS # For handling cross-origin requests from the frontend
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 2. Flask App Initialization & CORS Setup
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# 3. Configuration Variables
# --- IMPORTANT: Configure your email sender details ---
# Replace "your_email@example.com" with your actual sender email address.
EMAIL_ADDRESS = "preethavjjagan@gmail.com"
# Replace "your_email_password" with your actual email password or an App Password (for Gmail with 2FA).
EMAIL_PASSWORD = "ersr jmrp txlj dvmj"
SMTP_SERVER = "smtp.gmail.com"             # e.g., "smtp.gmail.com" for Gmail, "smtp.mail.yahoo.com" for Yahoo
SMTP_PORT = 587                            # Standard port for TLS encryption (common for most providers)

# --- Simulated User Email (for demonstration) ---
# This is the email address that will receive the content.
SIMULATED_USER_EMAIL = "preethavijagan@gmail.com"

# 4. Helper Function: Content Generation
def generate_content(domain):
    """
    Generates content based on the selected domain.
    Returns a dictionary with 'title', 'short_description', and 'full_content_html'.
    """
    if domain == "Investing":
        return {
            "title": "Unlocking Investment Growth: A Comprehensive Guide",
            "short_description": "Explore diverse strategies for stocks, bonds, mutual funds, and real estate to grow your wealth over time.",
            "full_content_html": """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 20px; }
                    h1 { color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
                    h2 { color: #0056b3; margin-top: 25px; }
                    p { margin-bottom: 1em; }
                    ul { list-style-type: disc; margin-left: 20px; }
                    ol { list-style-type: decimal; margin-left: 20px; }
                    .highlight { background-color: #e6f2ff; padding: 10px; border-left: 5px solid #007bff; margin: 15px 0; }
                    .footer { font-size: 0.8em; color: #777; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; text-align: center; }
                </style>
            </head>
            <body>
                <h1>Unlocking Investment Growth: A Comprehensive Guide</h1>
                <p>Investing is a powerful tool for building wealth over time. Understanding the different avenues and strategies is crucial for making informed decisions tailored to your financial goals and risk tolerance.</p>

                <h2>Stocks: Equity Ownership</h2>
                <p>When you buy a stock, you're purchasing a small piece of ownership in a company. The value of your stock can fluctuate based on the company's performance, industry trends, and broader market sentiment.</p>
                <ul>
                    <li><b>Growth Stocks:</b> Companies expected to grow faster than the overall market, often reinvesting profits.</li>
                    <li><b>Value Stocks:</b> Companies that appear to be undervalued by the market, trading at a discount relative to their intrinsic worth.</li>
                </ul>

                <h2>Bonds: Lending to Governments or Corporations</h2>
                <p>Bonds are essentially loans made by investors to a borrower (typically corporate or governmental entities). In return, the borrower promises to pay regular interest payments over a specified period and return the principal amount at maturity.</p>

                <h2>Mutual Funds & ETFs: Diversification Made Easy</h2>
                <p>These instruments allow you to invest in a diversified portfolio of securities with a single purchase, offering convenience and professional management.</p>
                <ul>
                    <li><b>Mutual Funds:</b> Professionally managed portfolios that pool money from many investors to buy stocks, bonds, or other assets.</li>
                    <li><b>Exchange-Traded Funds (ETFs):</b> Similar to mutual funds but trade like individual stocks on exchanges throughout the day. Many ETFs track a specific index (e.g., S&P 500).</li>
                </ul>

                <h2>Real Estate: Tangible Assets</h2>
                <p>Investing in real estate can provide rental income, potential property value appreciation, and a hedge against inflation. Options include direct property ownership, Real Estate Investment Trusts (REITs), or real estate crowdfunding.</p>

                <div class="highlight">
                    <h3>Key Investing Principles:</h3>
                    <ol>
                        <li><b>Diversification:</b> Spread your investments across different asset classes, industries, and geographies to reduce risk.</li>
                        <li><b>Long-Term Perspective:</b> Avoid reacting to short-term market fluctuations; historical data suggests long-term market growth.</li>
                        <li><b>Risk Tolerance:</b> Understand your comfort level with potential losses, which will guide your asset allocation.</li>
                        <li><b>Regular Contributions:</b> Invest consistently over time (dollar-cost averaging) to benefit from market dips and average out your purchase price.</li>
                        <li><b>Stay Informed:</b> Educate yourself on financial markets and economic news, but avoid emotional trading decisions.</li>
                    </ol>
                </div>

                <p>Remember, always consult with a qualified financial advisor to tailor an investment strategy that aligns with your personal financial goals and unique circumstances.</p>

                <div class="footer">
                    <p>This personalized content was brought to you by your AI Financial Assistant.</p>
                    <p>&copy; 2023 AI Financial Assistant. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
        }
    elif domain == "Crypto":
        return {
            "title": "Understanding Cryptocurrencies: A Beginner's Guide",
            "short_description": "Dive into the world of digital assets, blockchain technology, and decentralized finance, exploring both opportunities and risks.",
            "full_content_html": """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 20px; }
                    h1 { color: #ffc107; border-bottom: 2px solid #ffc107; padding-bottom: 10px; }
                    h2 { color: #e0a800; margin-top: 25px; }
                    p { margin-bottom: 1em; }
                    ul { list-style-type: disc; margin-left: 20px; }
                    ol { list-style-type: decimal; margin-left: 20px; }
                    .highlight { background-color: #fff3cd; padding: 10px; border-left: 5px solid #ffc107; margin: 15px 0; }
                    .footer { font-size: 0.8em; color: #777; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; text-align: center; }
                </style>
            </head>
            <body>
                <h1>Understanding Cryptocurrencies: A Beginner's Guide</h1>
                <p>Cryptocurrencies are digital or virtual currencies secured by cryptography, making them nearly impossible to counterfeit or double-spend. Most cryptocurrencies are decentralized networks based on blockchain technology—a distributed ledger enforced by a disparate network of computers.</p>

                <h2>What is Blockchain?</h2>
                <p>Blockchain is the foundational technology behind most cryptocurrencies. It's a decentralized and distributed ledger that records transactions across many computers in a way that is secure, transparent, and immutable.</p>

                <h2>Key Cryptocurrencies:</h2>
                <ul>
                    <li><b>Bitcoin (BTC):</b> The first and most well-known cryptocurrency, often referred to as digital gold due to its scarcity and store-of-value proposition.</li>
                    <li><b>Ethereum (ETH):</b> The second-largest cryptocurrency, renowned for its smart contract functionality that enables the creation of decentralized applications (dApps) and various DeFi protocols.</li>
                    <li><b>Altcoins:</b> A collective term for all cryptocurrencies other than Bitcoin. This broad category includes thousands of digital assets with varying use cases and technologies.</li>
                </ul>

                <h2>How to Acquire Cryptocurrencies:</h2>
                <ol>
                    <li><b>Exchanges:</b> Platforms like Coinbase, Binance, Kraken, and others allow you to buy and sell crypto using traditional fiat currency (e.g., USD, EUR).</li>
                    <li><b>Mining:</b> The process of verifying and adding new transactions to the blockchain, often rewarded with newly minted cryptocurrency. This typically requires specialized hardware.</li>
                </ol>

                <div class="highlight">
                    <h3>Risks and Considerations:</h3>
                    <ul>
                        <li><b>Volatility:</b> Cryptocurrency prices can be highly volatile, leading to significant gains or losses in short periods.</li>
                        <li><b>Regulation:</b> The regulatory landscape for cryptocurrencies is still evolving and varies significantly across different jurisdictions.</li>
                        <li><b>Security:</b> Proper security practices (e.g., using hardware wallets, strong unique passwords, enabling 2FA) are essential to protect your digital assets from theft.</li>
                        <li><b>Scams:</b> The crypto space is unfortunately prone to various scams; always do thorough research before investing.</li>
                    </ul>
                </div>

                <p>The world of cryptocurrencies is rapidly evolving, offering both innovative opportunities and considerable risks. Thorough research, a clear understanding of the technology, and a cautious approach are paramount before engaging in this market.</p>

                <div class="footer">
                    <p>This personalized content was brought to you by your AI Financial Assistant.</p>
                    <p>&copy; 2023 AI Financial Assistant. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
        }
    # Add more domains here as needed (Retirement, Budgeting, General)
    else:
        # Default placeholder content for other domains
        return {
            "title": f"Discover {domain} Insights",
            "short_description": f"Expert guidance and strategies for {domain.lower()} management and planning.",
            "full_content_html": f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 20px; }}
                    h1 {{ color: #6c757d; border-bottom: 2px solid #6c757d; padding-bottom: 10px; }}
                    p {{ margin-bottom: 1em; }}
                    .footer {{ font-size: 0.8em; color: #777; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; text-align: center; }}
                </style>
            </head>
            <body>
                <h1>Discover {domain} Insights</h1>
                <p>This is placeholder content for the <b>{domain}</b> domain. Here you would find detailed articles, tips, and strategies specifically curated for {domain.lower()} management.</p>
                <p>Our AI has analyzed your interests and provided this information to help you navigate and succeed in your {domain.lower()} goals.</p>
                <ul>
                    <li>Key strategies for effective {domain.lower()}.</li>
                    <li>Latest trends and important updates relevant to {domain.lower()}.</li>
                    <li>Practical advice and actionable steps for {domain.lower()} challenges.</li>
                </ul>
                <p>Stay tuned for more in-depth and personalized content as you explore more topics!</p>
                <div class="footer">
                    <p>This personalized content was brought to you by your AI Financial Assistant.</p>
                    <p>&copy; 2023 AI Financial Assistant. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
        }

# 5. Helper Function: Email Sending
def send_email(recipient_email, subject, body_html):
    """
    Sends an HTML formatted email to the specified recipient.
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Attach the HTML content as the email body
        part = MIMEText(body_html, "html")
        msg.attach(part)

        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection with TLS
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        print(f"Email for '{subject}' sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient_email}. Error: {e}")
        return False

# 6. API Endpoint
@app.route("/get-personalized-content", methods=["POST"])
def get_personalized_content():
    """
    API endpoint to generate personalized content and send it via email.
    Expects JSON with 'domain' and 'user_email'.
    """
    data = request.json
    domain = data.get("domain")
    user_email = data.get("user_email", SIMULATED_USER_EMAIL) # Use simulated email if not provided

    # Input validation
    if not domain:
        return jsonify({"success": False, "error": "Domain is required."}), 400
    if not user_email: # Should ideally always be present for a real user
        return jsonify({"success": False, "error": "User email is required for sending content."}), 400

    content_data = generate_content(domain)

    if content_data:
        # Send email with the full HTML content
        email_subject = f"Your Personalized Content: {content_data['title']}"
        email_sent_status = send_email(user_email, email_subject, content_data['full_content_html'])

        # Return data for the frontend stream
        return jsonify({
            "success": True,
            "personalized_content": {
                "title": content_data["title"],
                "short_description": content_data["short_description"],
                "domain": domain,
                "match_score": "AI-Generated", # Could be dynamic in a real system
                "email_status": "sent" if email_sent_status else "failed"
            }
        })
    else:
        return jsonify({"success": False, "error": "Content not found for the specified domain."}), 404

# 7. Main Execution Block
if __name__ == "__main__":
    # Run the Flask app in debug mode on port 5000
    # For production, set debug=False and use a production-ready server like Gunicorn
    app.run(debug=True, port=5000)