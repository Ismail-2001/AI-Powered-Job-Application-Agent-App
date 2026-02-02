"""
Flask Web Application for AI-Powered Job Application Agent
Run on localhost for web interface
"""

import os
import sys
import json
import re
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from models import init_db, Profile, User
from utils.resume_parser import ResumeParser

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Import our modular components
from utils.deepseek_client import DeepSeekClient
from utils.document_builder import DocumentBuilder
from utils.match_calculator import MatchCalculator
from agents.job_analyzer import JobAnalyzer
from agents.cv_customizer import CVCustomizer
from agents.cover_letter_generator import CoverLetterGenerator

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database (SQLite by default, configurable via DATABASE_URL)
init_db(app)

# Configure login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Configure OAuth
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


# Global variables for initialized components
client = None
builder = None
match_calculator = None
job_analyzer = None
cv_customizer = None
cover_letter_generator = None

# For SaaS-style background tasks without Redis
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)

def initialize_components():
    """Initialize all AI components."""
    global client, builder, match_calculator, job_analyzer, cv_customizer, cover_letter_generator
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
    
    client = DeepSeekClient(api_key=api_key)
    builder = DocumentBuilder()
    match_calculator = MatchCalculator()
    job_analyzer = JobAnalyzer(client)
    cv_customizer = CVCustomizer(client)
    cover_letter_generator = CoverLetterGenerator(client)

def load_profile(path: str = "data/master_profile.json") -> dict:
    """
    Load the master profile.

    Migration note:
    - Primary source is DB (Profile singleton).
    - If DB profile is empty but JSON file exists, import it once.
    """
    # 1. Try DB first
    if current_user.is_authenticated:
        profile_row = Profile.get_or_create_for_user(current_user.id)
    else:
        profile_row = Profile.get_singleton_profile()
    data = profile_row.to_dict()
    if data:
        return data

    # 2. Fallback: import from existing JSON file (one-time migration)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
            profile_row.update_from_dict(file_data)
            return file_data
    except FileNotFoundError:
        # If no file and no DB data, return empty profile structure
        return {}
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {path}")

def sanitize_filename(name: str) -> str:
    """Sanitize filename for Windows."""
    return re.sub(r'[<>:"/\\|?*]', '', name).strip().replace(' ', '_')

@app.route('/')
@login_required
def index():
    """Main page / Dashboard."""
    try:
        profile = load_profile()
        
        # Load recent history
        from models import JobApplication
        history = JobApplication.query.filter_by(user_id=current_user.id).order_by(JobApplication.created_at.desc()).limit(10).all()
        
        # Use redesigned template if available, fallback to original
        try:
            return render_template('index_redesigned.html', profile=profile, history=history)
        except:
            return render_template('index.html', profile=profile, history=history)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        try:
            return render_template('index_redesigned.html', profile=None, history=[])
        except:
            return render_template('index.html', profile=None, history=[])

@app.route('/profile')
@login_required
def profile_page():
    """Render profile management page."""
    try:
        profile = load_profile()
        return render_template('profile.html', profile=profile, user=current_user)
    except Exception as e:
        flash(f"Error loading profile: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/api/profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile and API keys."""
    try:
        data = request.json
        profile_data = data.get('profile')
        google_key = data.get('google_api_key')
        deepseek_key = data.get('deepseek_api_key')
        
        from models import Profile, db, User
        profile = Profile.get_or_create_for_user(current_user.id)
        profile.update_from_dict(profile_data)
        
        user = User.query.get(current_user.id)
        if google_key is not None: user.google_api_key = google_key
        if deepseek_key is not None: user.deepseek_api_key = deepseek_key
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resume/upload', methods=['POST'])
@login_required
def upload_resume():
    """Handle resume upload and AI parsing."""
    if 'resume' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
    try:
        # Get AI client for parsing (using user's key if available)
        user = User.query.get(current_user.id)
        api_key = user.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return jsonify({'success': False, 'error': 'Check Profile: DeepSeek API Key required for parsing'}), 400
            
        ai_client = DeepSeekClient(api_key=api_key)
        parser = ResumeParser(ai_client)
        
        file_bytes = file.read()
        structured_data = parser.parse_resume(file_bytes, file.filename)
        
        # Partially update profile with extracted data
        from models import Profile, db
        profile = Profile.get_or_create_for_user(current_user.id)
        current_data = profile.to_dict()
        
        # Merge or overwrite? Let's merge basic info and overwrite lists
        if 'personal_info' in structured_data:
            current_data['personal_info'] = structured_data['personal_info']
        if 'summary' in structured_data:
            current_data['summary'] = structured_data['summary']
        if 'experience' in structured_data:
            current_data['experience'] = structured_data['experience']
        if 'education' in structured_data:
            current_data['education'] = structured_data['education']
        if 'skills' in structured_data:
            current_data['skills'] = structured_data['skills']
            
        profile.update_from_dict(current_data)
        
        return jsonify({
            'success': True, 
            'message': 'Resume parsed successfully! Check your details below.',
            'profile': current_data
        })
        
    except Exception as e:
        print(f"Resume Upload Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# --- OAuth Routes ---

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorize/google')
def authorize_google():
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get('userinfo')
        if not userinfo:
            return redirect(url_for('login'))
            
        email = userinfo.get('email')
        user = User.get_by_email(email)
        
        if not user:
            # Create user if doesn't exist (Social Signup)
            user = User.create(email=email, password_hash=None)
            
        login_user(user)
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Google Login Failed: {str(e)}", "error")
        return redirect(url_for('login'))

@app.route('/api/process', methods=['POST'])
@login_required
def process_job():
    """Process job description asynchronously."""
    try:
        data = request.json
        job_description = data.get('job_description', '').strip()
        
        if not job_description or len(job_description) < 50:
            return jsonify({
                'success': False,
                'error': 'Job description is too short. Please provide at least 50 characters.'
            }), 400
        
        # Initialize components if not already done
        if client is None:
            initialize_components()
        
        # Create a pending application entry
        from models import JobApplication, db
        job_app = JobApplication.create(
            user_id=current_user.id,
            status="processing"
        )
        
        # Start background task
        executor.submit(run_ai_pipeline, job_app.id, job_description, current_user.id)
        
        return jsonify({
            'success': True,
            'app_id': job_app.id,
            'status': 'processing'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Initialization error: {str(e)}'
        }), 500

def run_ai_pipeline(app_id, job_description, user_id):
    """Background task to run the AI agents."""
    from models import JobApplication, db, Profile
    import app as flask_app_module # to get app context
    
    with flask_app.app_context():
        try:
            from models import JobApplication, db, Profile, User
            job_app = JobApplication.query.get(app_id)
            if not job_app: return

            user = User.query.get(user_id)
            
            # Setup local clients with user keys if available
            user_deepseek_key = user.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
            user_google_key = user.google_api_key or os.getenv("GOOGLE_API_KEY")
            
            if not user_deepseek_key:
                raise ValueError("DeepSeek API Key missing. Please set it in Your Profile.")
            
            # Local instances for this thread to avoid global state issues
            from utils.deepseek_client import DeepSeekClient
            from utils.gemini_client import GeminiClient
            from utils.match_calculator import MatchCalculator
            from agents.job_analyzer import JobAnalyzer
            from agents.cv_customizer import CVCustomizer
            from agents.cover_letter_generator import CoverLetterGenerator
            from utils.document_builder import DocumentBuilder

            local_client = DeepSeekClient(api_key=user_deepseek_key)
            local_analyzer = JobAnalyzer(local_client)
            local_customizer = CVCustomizer(local_client)
            local_cl_gen = CoverLetterGenerator(local_client)
            local_match_calc = MatchCalculator()
            local_builder = DocumentBuilder()

            # 1. Load profile
            profile_row = Profile.query.filter_by(user_id=user_id).first()
            if not profile_row:
                profile_row = Profile.get_singleton_profile()
            profile = profile_row.to_dict()

            # 2. Analyze job
            analysis = local_analyzer.analyze(job_description)
            role_title = analysis.get('role_info', {}).get('title', 'Unknown Role')
            company = analysis.get('role_info', {}).get('company', 'Unknown Company')
            
            # 3. Calculate match score
            match_data = local_match_calc.calculate_match_score(profile, analysis)
            
            # 4. Customize CV
            customized_cv = local_customizer.customize(profile, analysis)
            
            # 5. Generate cover letter
            cover_letter_text = local_cl_gen.generate(profile, analysis)
            
            # 6. Generate documents
            os.makedirs("output", exist_ok=True)
            safe_title = sanitize_filename(role_title)
            safe_company = sanitize_filename(company)
            
            cv_filename = f"output/CV_{safe_company}_{safe_title}.docx"
            cl_filename = f"output/CL_{safe_company}_{safe_title}.docx"
            
            local_builder.create_cv(customized_cv, cv_filename)
            local_builder.create_cover_letter(cover_letter_text, profile, cl_filename)
            
            # 7. Update database
            job_app.role_title = role_title
            job_app.company = company
            job_app.match_score = match_data.get('score', 0)
            job_app.cv_path = cv_filename
            job_app.cover_letter_path = cl_filename
            job_app.analysis_data = analysis
            job_app.status = "completed"
            db.session.commit()
            
        except Exception as e:
            print(f"❌ Background Task Error: {e}")
            try:
                job_app = JobApplication.query.get(app_id)
                if job_app:
                    job_app.status = "failed"
                    job_app.error_message = str(e)
                    db.session.commit()
            except:
                pass

@app.route('/api/status/<int:app_id>')
@login_required
def get_job_status(app_id):
    """Check status of a background job."""
    from models import JobApplication
    job_app = JobApplication.query.filter_by(id=app_id, user_id=current_user.id).first()
    
    if not job_app:
        return jsonify({'error': 'Job not found'}), 404
        
    return jsonify({
        'status': job_app.status,
        'role_title': job_app.role_title,
        'company': job_app.company,
        'match_score': job_app.match_score,
        'cv_file': job_app.cv_path,
        'cover_letter_file': job_app.cover_letter_path,
        'analysis': job_app.analysis_data,
        'error': job_app.error_message
    })

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download generated files."""
    try:
        # Security: only allow files from output directory
        if not filename.startswith('output/'):
            return jsonify({'error': 'Invalid file path'}), 403
        
        file_path = filename
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current profile."""
    try:
        profile = load_profile()
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration."""
    if request.method == 'POST':
        data = request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth_signup.html')

        if User.get_by_email(email):
            flash('Email is already registered. Please log in.', 'error')
            return render_template('auth_signup.html')

        password_hash = generate_password_hash(password)
        user = User.create(email=email, password_hash=password_hash)
        login_user(user)
        return redirect(url_for('index'))

    return render_template('auth_signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        data = request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        user = User.get_by_email(email)
        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'error')
            return render_template('auth_login.html')

        login_user(user)
        return redirect(url_for('index'))

    return render_template('auth_login.html')


@app.route('/logout')
@login_required
def logout():
    """Log out current user."""
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Initialize components on startup
    try:
        initialize_components()
        print("✅ All components initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize components: {e}")
        print("💡 Make sure DEEPSEEK_API_KEY is set in .env file")
    
    print("\n🚀 Starting Flask web server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
