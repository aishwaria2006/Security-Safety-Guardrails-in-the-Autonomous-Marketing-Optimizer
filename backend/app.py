from flask import Flask, request, jsonify
from flask_cors import CORS # To handle CORS issues between frontend and backend
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Configuration ---
EMAIL_ADDRESS = "preethavjjagan@gmail.com" # Your sender email
EMAIL_PASSWORD = "717823i140@kce.ac.in"   # Your email password or app-specific password
SMTP_SERVER = "smtp.gmail.com"           # e.g., "smtp.gmail.com" for Gmail
SMTP_PORT = 587                          # e.g., 587 for TLS

# --- Content Generation (Placeholder) ---
def generate_content(domain):
    if domain == "Investing":
        return {
            "title": "Unlocking Investment Growth: A Comprehensive Guide",
            "short_description": "Explore strategies for stocks, bonds, mutual funds, and more to grow your wealth.",
            "full_content": """
            <h1>Unlocking Investment Growth: A Comprehensive Guide</h1>
            <p>Investing is a powerful tool for building wealth over time. Understanding the different avenues and strategies is crucial for making informed decisions.</p>
            <h2>Stocks: Equity Ownership</h2>
            <p>When you buy a stock, you're purchasing a small piece of ownership in a company. The value of your stock can increase or decrease based on the company's performance, market trends, and investor sentiment.</p>
            <ul>
                <li><b>Growth Stocks:</b> Companies expected to grow faster than the overall market.</li>
                <li><b>Value Stocks:</b> Companies that appear to be undervalued by the market.</li>
            </ul>
            <h2>Bonds: Lending to Governments or Corporations</h2>
            <p>Bonds are essentially loans made by investors to a borrower (typically corporate or governmental entities). In return, the borrower promises to pay interest over a specified period and return the principal amount at maturity.</p>
            <h2>Mutual Funds & ETFs: Diversification Made Easy</h2>
            <p><b>Mutual Funds:</b> A professionally managed investment fund that pools money from many investors to purchase securities. Diversification is a key benefit.</p>
            <p><b>Exchange-Traded Funds (ETFs):</b> Similar to mutual funds, but they trade like stocks on exchanges throughout the day. They often track an index, commodity, or sector.</p>
            <h2>Real Estate: Tangible Assets</h2>
            <p>Investing in real estate can provide rental income and potential appreciation in property value. Options include direct property ownership, Real Estate Investment Trusts (REITs), or crowdfunding.</p>
            <h2>Key Investing Principles:</h2>
            <ol>
                <li><b>Diversification:</b> Don't put all your eggs in one basket. Spread your investments across different asset classes and industries.</li>
                <li><b>Long-Term Perspective:</b> Markets can be volatile in the short term, but historically, they tend to grow over the long run.</li>
                <li><b>Risk Tolerance:</b> Understand how much risk you're comfortable taking. This will influence your investment choices.</li>
                <li><b>Regular Contributions:</b> Invest consistently over time (dollar-cost averaging) to smooth out market fluctuations.</li>
                <li><b>Stay Informed:</b> Keep up-to-date with economic news and market trends, but avoid emotional reactions.</li>
            </ol>
            <p>Remember, always consult with a financial advisor to tailor an investment strategy that aligns with your personal financial goals and risk profile.</p>
            """
        }
    elif domain == "Crypto":
        return {
            "title": "Understanding Cryptocurrencies: A Beginner's Guide",
            "short_description": "Dive into the world of digital assets, blockchain, and decentralized finance.",
            "full_content": """
            <h1>Understanding Cryptocurrencies: A Beginner's Guide</h1>
            <p>Cryptocurrencies are digital or virtual currencies secured by cryptography, making them nearly impossible to counterfeit or double-spend. Many cryptocurrencies are decentralized networks based on blockchain technology—a distributed ledger enforced by a disparate network of computers.</p>
            <h2>What is Blockchain?</h2>
            <p>Blockchain is the underlying technology behind most cryptocurrencies. It's a decentralized and distributed ledger that records transactions across many computers. This makes it highly secure and transparent.</p>
            <h2>Key Cryptocurrencies:</h2>
            <ul>
                <li><b>Bitcoin (BTC):</b> The first and most well-known cryptocurrency, often referred to as digital gold.</li>
                <li><b>Ethereum (ETH):</b> The second-largest cryptocurrency, known for its smart contract functionality and powering decentralized applications (dApps).</li>
                <li><b>Altcoins:</b> A collective term for all cryptocurrencies other than Bitcoin.</li>
            </ul>
            <h2>How to Acquire Cryptocurrencies:</h2>
            <ol>
                <li><b>Exchanges:</b> Platforms like Coinbase, Binance, Kraken, etc., allow you to buy and sell crypto using fiat currency.</li>
                <li><b>Mining:</b> The process of verifying and adding new transactions to the blockchain.</li>
            </ol>
            <h2>Risks and Considerations:</h2>
            <ul>
                <li><b>Volatility:</b> Cryptocurrency prices can be highly volatile, leading to significant gains or losses.</li>
                <li><b>Regulation:</b> The regulatory landscape for cryptocurrencies is still evolving.</li>
                <li><b>Security:</b> Proper security practices (e.g., using hardware wallets, strong passwords) are essential to protect your assets.</li>
            </ul>
            <p>The world of cryptocurrencies is rapidly evolving, offering both opportunities and risks. Thorough research and a clear understanding of the technology are paramount before investing.</p>
            """
        }
    # Add more domains as needed (Retirement, Budgeting, General)
    else:
        return {
            "title": f"Discover {domain} Insights",
            "short_description": f"Expert guidance and strategies for {domain.lower()}.",
            "full_content": f"""
            <h1>Discover {domain} Insights</h1>
            <p>This is placeholder content for the {domain} domain. Here you would find detailed articles, tips, and strategies related to {domain.lower()}.</p>
            <p>Our AI has curated this information to help you achieve your goals in {domain.lower()} management.</p>
            <ul>
                <li>Key strategies for {domain.lower()} success.</li>
                <li>Latest trends and updates in the {domain.lower()} sector.</li>
                <li>Practical advice for everyday {domain.lower()} challenges.</li>
            </ul>
            <p>Stay tuned for more personalized content!</p>
            """
        }

# --- Email Sending Function ---
def send_email(recipient_email, subject, body_html):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Attach the HTML content
        part1 = MIMEText(body_html, "html")
        msg.attach(part1)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        print(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# --- API Endpoint ---
@app.route("/get-personalized-content", methods=["POST"])
def get_personalized_content():
    data = request.json
    domain = data.get("domain")
    user_email = data.get("user_email")

    if not domain or not user_email:
        return jsonify({"error": "Domain and user email are required."}), 400

    content_data = generate_content(domain)

    if content_data:
        # Send email with full content
        email_subject = f"Your Personalized Content: {content_data['title']}"
        email_body = f"""
        <html>
        <head></head>
        <body>
            {content_data['full_content']}
            <p>---</p>
            <p>This email was sent to {user_email} based on your interest in {domain}.</p>
        </body>
        </html>
        """
        email_sent = send_email(user_email, email_subject, email_body)

        # Return data for the frontend stream
        return jsonify({
            "success": True,
            "personalized_content": {
                "title": content_data["title"],
                "short_description": content_data["short_description"],
                "domain": domain,
                "match_score": "AI-Generated", # Or a calculated score
                "email_status": "sent" if email_sent else "failed"
            }
        })
    else:
        return jsonify({"error": "Content not found for the specified domain."}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000) # Run on port 5000
