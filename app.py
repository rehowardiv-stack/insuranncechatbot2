/* Base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Buttons */
.btn-primary, .btn-secondary, .btn-large {
    display: inline-block;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
    font-size: 16px;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.2);
}

.btn-secondary {
    background: white;
    color: #667eea;
    border: 2px solid #667eea;
}

.btn-large {
    padding: 16px 32px;
    font-size: 18px;
}

.btn-small {
    padding: 6px 12px;
    font-size: 14px;
    border-radius: 4px;
}

/* Navbar */
.navbar {
    background: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    position: fixed;
    width: 100%;
    top: 0;
    z-index: 1000;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
}

.logo {
    display: flex;
    align-items: center;
    text-decoration: none;
    color: #333;
    font-size: 24px;
    font-weight: 700;
}

.logo i {
    margin-right: 10px;
    color: #667eea;
}

.nav-links {
    display: flex;
    gap: 30px;
    align-items: center;
}

.nav-links a {
    text-decoration: none;
    color: #666;
    font-weight: 500;
}

.nav-links a:hover {
    color: #667eea;
}

/* Hero Section */
.hero {
    padding: 140px 0 80px;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.hero .container {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.hero-content {
    flex: 1;
    max-width: 600px;
}

.hero h1 {
    font-size: 3.5rem;
    margin-bottom: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 30px;
}

.hero-buttons {
    display: flex;
    gap: 20px;
    margin-bottom: 40px;
}

.stats {
    display: flex;
    gap: 40px;
    margin-top: 40px;
}

.stat {
    text-align: center;
}

.number {
    display: block;
    font-size: 2.5rem;
    font-weight: 700;
    color: #667eea;
}

.label {
    font-size: 0.9rem;
    color: #666;
}

.hero-image {
    flex: 1;
    text-align: center;
}

.hero-image img {
    max-width: 100%;
    height: auto;
}

/* Quick Quote */
.quick-quote {
    padding: 80px 0;
    background: white;
}

.quick-quote h2 {
    text-align: center;
    margin-bottom: 40px;
    font-size: 2.5rem;
}

.quote-form {
    max-width: 600px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.form-group {
    margin-bottom: 20px;
}

.form-group input, .form-group select {
    width: 100%;
    padding: 12px;
    border: 2px solid #e1e5e9;
    border-radius: 8px;
    font-size: 16px;
}

/* Footer */
footer {
    background: #1a202c;
    color: white;
    padding: 60px 0 20px;
}

.footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 40px;
    margin-bottom: 40px;
}

.footer-section h3, .footer-section h4 {
    margin-bottom: 20px;
}

.footer-section h3 i {
    color: #667eea;
    margin-right: 10px;
}

.footer-bottom {
    text-align: center;
    padding-top: 20px;
    border-top: 1px solid #2d3748;
}

.disclaimer {
    font-size: 0.9rem;
    color: #a0aec0;
    margin-top: 10px;
}

/* Responsive */
@media (max-width: 768px) {
    .hero .container {
        flex-direction: column;
        text-align: center;
    }
    
    .hero h1 {
        font-size: 2.5rem;
    }
    
    .hero-buttons {
        flex-direction: column;
    }
    
    .stats {
        justify-content: center;
    }
    
    .quote-form {
        grid-template-columns: 1fr;
    }
}
