
import os, re, sqlite3, math, secrets, qrcode
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from io import BytesIO
import json

# Load environment variables from .env file if it exists
load_dotenv()

# Import configuration
import config

# Import from new modules
from models.database import get_db, init_db
from services.matching import match_score, generate_match_explanation
from services.search import semantic_search, parse_search_query
from services.image_analyzer import ImageAnalyzer

# Import AI services
from services.ai import VisionAnalyzer, EmbeddingService, MultimodalMatcher, OCRService, SemanticSearch, AIAssistant, AnomalyDetector, RecommendationEngine, ConfidenceEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "campusfind.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campusfind-dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED = {"png", "jpg", "jpeg", "webp"}

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize AI services
vision_analyzer = VisionAnalyzer()
embedding_service = EmbeddingService()
multimodal_matcher = MultimodalMatcher()
ocr_service = OCRService()
semantic_search_engine = SemanticSearch()
ai_assistant = AIAssistant()
anomaly_detector = AnomalyDetector()
recommendation_engine = RecommendationEngine()
confidence_engine = ConfidenceEngine()

# Set up recommendation engine dependencies
recommendation_engine.set_services(multimodal_matcher, embedding_service)

# Backward compatibility alias
def db():
    return get_db()

# Seed demo accounts after database initialization
def seed_demo_accounts():
    con = db()
    existing = con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    if existing == 0:
        now = datetime.now().isoformat(timespec="seconds")
        con.execute("INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
                    ("Campus Admin","admin@campusfind.local",generate_password_hash("admin123"),"admin",now))
        con.execute("INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
                    ("Demo Student","student@campusfind.local",generate_password_hash("student123"),"student",now))
        con.commit()
    con.close()

def current_user():
    if "user_id" not in session:
        return None
    con = db()
    u = con.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    con.close()
    return u

@app.context_processor
def inject():
    u = current_user()
    unread = 0
    if u:
        con = db()
        unread = con.execute("SELECT COUNT(*) c FROM notifications WHERE user_id=? AND is_read=0",(u["id"],)).fetchone()["c"]
        con.close()
    return {"current_user": u, "unread_notifications": unread}

def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*a, **kw)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        u = current_user()
        if not u or u["role"] != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return fn(*a, **kw)
    return wrapper

def notify(user_id, message, link=None, notification_type="info"):
    con = db()
    con.execute("INSERT INTO notifications(user_id,message,link,created_at,notification_type) VALUES(?,?,?,?,?)",
                (user_id,message,link,datetime.now().isoformat(timespec="seconds"),notification_type))
    con.commit(); con.close()

@app.route("/")
def index():
    con = db()
    stats = {
        "lost": con.execute("SELECT COUNT(*) c FROM items WHERE type='lost'").fetchone()["c"],
        "found": con.execute("SELECT COUNT(*) c FROM items WHERE type='found'").fetchone()["c"],
        "recovered": con.execute("SELECT COUNT(*) c FROM items WHERE status='recovered'").fetchone()["c"],
        "users": con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    }
    latest = con.execute("""SELECT items.*, users.name FROM items JOIN users ON users.id=items.user_id
                            WHERE items.status='open' ORDER BY items.id DESC LIMIT 6""").fetchall()
    con.close()
    return render_template("index.html", stats=stats, latest=latest)

@app.route("/register", methods=["GET","POST"])
@limiter.limit("5 per hour")
def register():
    if request.method == "POST":
        name,email,password = request.form["name"].strip(), request.form["email"].strip().lower(), request.form["password"]
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")
        con=db()
        try:
            con.execute("INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
                        (name,email,generate_password_hash(password),"student",datetime.now().isoformat(timespec="seconds")))
            con.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "danger")
        finally: con.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
@limiter.limit("10 per hour")
def login():
    if request.method=="POST":
        email=request.form["email"].strip().lower(); password=request.form["password"]
        con=db(); u=con.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); con.close()
        if u and check_password_hash(u["password"],password):
            session["user_id"]=u["id"]
            flash(f"Welcome back, {u['name'].split()[0]}!", "success")
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    u=current_user(); con=db()
    items=con.execute("SELECT * FROM items WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall()
    claims=con.execute("""SELECT claims.*, items.title, items.type FROM claims
                          JOIN items ON items.id=claims.item_id WHERE claims.claimant_id=?
                          ORDER BY claims.id DESC""",(u["id"],)).fetchall()
    stats = {
        "lost_count": con.execute("SELECT COUNT(*) c FROM items WHERE user_id=? AND type='lost'",(u["id"],)).fetchone()["c"],
        "found_count": con.execute("SELECT COUNT(*) c FROM items WHERE user_id=? AND type='found'",(u["id"],)).fetchone()["c"],
        "recovered_count": con.execute("SELECT COUNT(*) c FROM items WHERE user_id=? AND status='recovered'",(u["id"],)).fetchone()["c"],
        "claims_count": con.execute("SELECT COUNT(*) c FROM claims WHERE claimant_id=?",(u["id"],)).fetchone()["c"]
    }
    con.close()
    return render_template("dashboard.html",items=items,claims=claims,stats=stats)

@app.route("/profile")
@login_required
def profile():
    u=current_user(); con=db()
    stats = {
        "lost_count": con.execute("SELECT COUNT(*) c FROM items WHERE user_id=? AND type='lost'",(u["id"],)).fetchone()["c"],
        "found_count": con.execute("SELECT COUNT(*) c FROM items WHERE user_id=? AND type='found'",(u["id"],)).fetchone()["c"],
        "recovered_count": con.execute("SELECT COUNT(*) c FROM items WHERE user_id=? AND status='recovered'",(u["id"],)).fetchone()["c"],
        "claims_count": con.execute("SELECT COUNT(*) c FROM claims WHERE claimant_id=?",(u["id"],)).fetchone()["c"]
    }
    con.close()
    return render_template("profile.html", stats=stats)

@app.route("/my-reports")
@login_required
def my_reports():
    u=current_user(); con=db()
    reports=con.execute("SELECT * FROM items WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall()
    con.close()
    return render_template("my_reports.html", reports=reports)

@app.route("/matches")
@login_required
def matches():
    u=current_user(); con=db()
    # Get user's lost items and their potential matches
    user_items = con.execute("SELECT * FROM items WHERE user_id=? AND type='lost' AND status='open'",(u["id"],)).fetchall()
    match_list = []
    for item in user_items:
        others = con.execute("SELECT * FROM items WHERE type='found' AND status='open' AND id!=?",(item["id"],)).fetchall()
        for other in others:
            score, breakdown = match_score(item, other)
            if score >= 35:
                match_list.append({
                    "item_id": other["id"],
                    "item_title": other["title"],
                    "item_type": other["type"],
                    "item_location": other["location"],
                    "item_date": other["date_time"],
                    "score": score,
                    "reasons": generate_match_explanation(breakdown)
                })
    con.close()
    return render_template("matches.html", matches=match_list)

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

@app.route("/map")
def map():
    con=db()
    items=con.execute("SELECT * FROM items WHERE status='open'").fetchall()
    categories=[r["category"] for r in con.execute("SELECT DISTINCT category FROM items ORDER BY category").fetchall()]
    con.close()
    
    # Convert items to JSON with coordinates
    campus_locations = {
        "Library": [12.9716, 77.5946],
        "Main Block": [12.9726, 77.5956],
        "Cafeteria": [12.9706, 77.5936],
        "Hostel": [12.9696, 77.5966],
        "Parking": [12.9736, 77.5926],
        "Sports Ground": [12.9686, 77.5976],
        "CSE Block": [12.9746, 77.5986],
        "Labs": [12.9756, 77.5996],
        "Auditorium": [12.9766, 77.6006]
    }
    
    items_json = json.dumps([
        {
            "id": item["id"],
            "title": item["title"],
            "type": item["type"],
            "category": item["category"],
            "location": item["location"],
            "date_time": item["date_time"],
            "lat": campus_locations.get(item["location"], [12.9716, 77.5946])[0],
            "lng": campus_locations.get(item["location"], [12.9716, 77.5946])[1]
        }
        for item in items
    ])
    
    return render_template("map.html", items=items, categories=categories, items_json=items_json)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

@app.route("/report/<itype>", methods=["GET","POST"])
@login_required
@limiter.limit("10 per hour")
def report(itype):
    if itype not in ("lost","found"): return redirect(url_for("dashboard"))
    if request.method=="POST":
        title=request.form["title"].strip(); category=request.form["category"].strip()
        desc=request.form["description"].strip(); location=request.form["location"].strip()
        date_time=request.form["date_time"]
        brand=request.form.get("brand","").strip()
        model=request.form.get("model","").strip()
        color=request.form.get("color","").strip()
        features=request.form.get("features","").strip()
        building=request.form.get("building","").strip()
        floor=request.form.get("floor","").strip()
        contact_preference=request.form.get("contact_preference","email")
        
        if not all([title,category,desc,location,date_time]):
            flash("Please fill all required fields.", "danger")
            return render_template("report.html",itype=itype)
        image=None
        f=request.files.get("image")
        if f and f.filename:
            ext=f.filename.rsplit(".",1)[-1].lower()
            if ext not in ALLOWED:
                flash("Allowed images: PNG, JPG, JPEG, WEBP.", "danger")
                return render_template("report.html",itype=itype)
            safe=secure_filename(f.filename)
            image=f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe}"
            f.save(os.path.join(UPLOAD_DIR,image))
        con=db()
        cur=con.execute("""INSERT INTO items(user_id,type,title,category,description,location,date_time,image,status,created_at,brand,color,visual_features,building)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (session["user_id"],itype,title,category,desc,location,date_time,image,"open",datetime.now().isoformat(timespec="seconds"),brand,color,features,building))
        item_id=cur.lastrowid; con.commit()
        item=con.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
        others=con.execute("SELECT * FROM items WHERE type!=? AND status='open'",(itype,)).fetchall()
        con.close()
        for other in others:
            score, _ = match_score(item,other)
            if score >= 55:
                notify(item["user_id"],f"Potential match found for '{item['title']}' — {score}% confidence.",url_for("item_detail",item_id=other["id"]))
                notify(other["user_id"],f"Potential match found for '{other['title']}' — {score}% confidence.",url_for("item_detail",item_id=item_id))
        flash(f"{itype.title()} item reported successfully.", "success")
        return redirect(url_for("item_detail",item_id=item_id))
    return render_template("report.html",itype=itype)

@app.route("/items")
def items():
    q=request.args.get("q","").strip(); category=request.args.get("category","").strip()
    itype=request.args.get("type","").strip(); sort=request.args.get("sort","newest")
    con=db()
    sql="SELECT items.*, users.name FROM items JOIN users ON users.id=items.user_id WHERE items.status='open'"
    params=[]
    if q:
        sql += " AND (items.title LIKE ? OR items.description LIKE ? OR items.location LIKE ?)"
        params += [f"%{q}%"]*3
    if category:
        sql += " AND items.category=?"; params.append(category)
    if itype in ("lost","found"):
        sql += " AND items.type=?"; params.append(itype)
    
    # Sorting
    if sort == "oldest":
        sql += " ORDER BY items.id ASC"
    elif sort == "relevance" and q:
        sql += " ORDER BY CASE WHEN items.title LIKE ? THEN 1 WHEN items.description LIKE ? THEN 2 ELSE 3 END, items.id DESC"
        params += [f"%{q}%", f"%{q}%"]
    else:
        sql += " ORDER BY items.id DESC"
    
    rows=con.execute(sql,params).fetchall()
    cats=[r["category"] for r in con.execute("SELECT DISTINCT category FROM items ORDER BY category").fetchall()]
    con.close()
    return render_template("items.html",items=rows,categories=cats)

@app.route("/item/<int:item_id>")
def item_detail(item_id):
    con=db()
    item=con.execute("""SELECT items.*, users.name owner_name, users.email owner_email
                        FROM items JOIN users ON users.id=items.user_id WHERE items.id=?""",(item_id,)).fetchone()
    if not item:
        con.close(); return "Not found",404
    others=con.execute("SELECT * FROM items WHERE type!=? AND status='open' AND id!=?",(item["type"],item_id)).fetchall()
    matches=[]
    for o in others:
        s,d=match_score(item,o)
        if s>=35: matches.append((s,d,o))
    matches.sort(key=lambda x:x[0], reverse=True)
    con.close()
    return render_template("item_detail.html",item=item,matches=matches[:5])

@app.route("/claim/<int:item_id>", methods=["POST"])
@login_required
def claim(item_id):
    answer=request.form["answer"].strip()
    if len(answer)<5:
        flash("Please provide a meaningful ownership verification answer.", "danger")
        return redirect(url_for("item_detail",item_id=item_id))
    con=db(); item=con.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    if not item or item["status"]!="open":
        con.close(); flash("This item is no longer available for claiming.","warning"); return redirect(url_for("items"))
    con.execute("INSERT INTO claims(item_id,claimant_id,answer,status,created_at) VALUES(?,?,?,?,?)",
                (item_id,session["user_id"],answer,"pending",datetime.now().isoformat(timespec="seconds")))
    con.commit(); owner=item["user_id"]; con.close()
    notify(owner,f"New claim request received for '{item['title']}'.",url_for("admin"),notification_type="claim")
    flash("Claim submitted. The item owner/admin will review your verification.", "success")
    return redirect(url_for("item_detail",item_id=item_id))

@app.route("/notifications")
@login_required
def notifications():
    con=db()
    rows=con.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
    con.execute("UPDATE notifications SET is_read=1 WHERE user_id=?",(session["user_id"],)); con.commit(); con.close()
    return render_template("notifications.html",notifications=rows)

@app.route("/admin")
@admin_required
def admin():
    con=db()
    users=con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    open_items=con.execute("SELECT COUNT(*) c FROM items WHERE status='open'").fetchone()["c"]
    recovered=con.execute("SELECT COUNT(*) c FROM items WHERE status='recovered'").fetchone()["c"]
    lost_count=con.execute("SELECT COUNT(*) c FROM items WHERE type='lost'").fetchone()["c"]
    found_count=con.execute("SELECT COUNT(*) c FROM items WHERE type='found'").fetchone()["c"]
    pending_claims=con.execute("SELECT COUNT(*) c FROM claims WHERE status='pending'").fetchone()["c"]
    
    # Category breakdown
    categories=con.execute("SELECT category, COUNT(*) as count FROM items GROUP BY category ORDER BY count DESC").fetchall()
    
    # Location breakdown
    locations=con.execute("SELECT location, COUNT(*) as count FROM items GROUP BY location ORDER BY count DESC LIMIT 10").fetchall()
    
    # Recovery trend (last 7 days)
    recovery_trend=con.execute("""SELECT DATE(created_at) as date, COUNT(*) as count 
                                  FROM items WHERE status='recovered' 
                                  GROUP BY DATE(created_at) 
                                  ORDER BY date DESC LIMIT 7""").fetchall()
    
    claims=con.execute("""SELECT claims.*, items.title, users.name claimant_name, users.email claimant_email
                         FROM claims JOIN items ON items.id=claims.item_id JOIN users ON users.id=claims.claimant_id
                         ORDER BY claims.id DESC""").fetchall()
    recent=con.execute("""SELECT items.*, users.name FROM items JOIN users ON users.id=items.user_id
                          ORDER BY items.id DESC LIMIT 15""").fetchall()
    con.close()
    
    return render_template("admin.html",users=users,open_items=open_items,recovered=recovered,
                          lost_count=lost_count,found_count=found_count,pending_claims=pending_claims,
                          categories=categories,locations=locations,recovery_trend=recovery_trend,
                          claims=claims,recent=recent)

@app.route("/admin/claim/<int:claim_id>/<action>", methods=["POST"])
@admin_required
def admin_claim(claim_id,action):
    if action not in ("approve","reject"): return redirect(url_for("admin"))
    con=db()
    claim=con.execute("SELECT * FROM claims WHERE id=?",(claim_id,)).fetchone()
    if claim:
        status="approved" if action=="approve" else "rejected"
        con.execute("UPDATE claims SET status=? WHERE id=?",(status,claim_id))
        if action=="approve":
            con.execute("UPDATE items SET status='recovered' WHERE id=?",(claim["item_id"],))
            # Generate handover record
            handover_id = f"CF-{datetime.now().strftime('%Y')}-{str(claim_id).zfill(6)}"
            handover_token = secrets.token_urlsafe(32)
            con.execute("""INSERT INTO handover_records(item_id,claim_id,handover_id,handover_token,created_at)
                          VALUES(?,?,?,?,?)""",
                      (claim["item_id"],claim_id,handover_id,handover_token,datetime.now().isoformat(timespec="seconds")))
            con.commit()
        con.commit()
        item=con.execute("SELECT title,user_id FROM items WHERE id=?",(claim["item_id"],)).fetchone()
        con.close()
        notify(claim["claimant_id"],f"Your claim for '{item['title']}' was {status}.",url_for("item_detail",item_id=claim["item_id"]),notification_type="claim")
        if action=="approve": 
            notify(item["user_id"],f"The claim for '{item['title']}' was approved.",url_for("item_detail",item_id=claim["item_id"]),notification_type="claim")
            notify(claim["claimant_id"],f"Your claim was approved! Handover ID: {handover_id if action=='approve' else ''}",url_for("handover",handover_id=handover_id if action=='approve' else ''),notification_type="claim")
    else: con.close()
    return redirect(url_for("admin"))

@app.route("/admin/item/<int:item_id>/remove", methods=["POST"])
@admin_required
def remove_item(item_id):
    con=db(); con.execute("UPDATE items SET status='removed' WHERE id=?",(item_id,)); con.commit(); con.close()
    flash("Item removed from public listings.","success"); return redirect(url_for("admin"))

@app.route("/api/analyze-image", methods=["POST"])
@login_required
def api_analyze_image():
    """API endpoint to analyze uploaded image and return AI suggestions."""
    f = request.files.get("image")
    if not f or f.filename == "":
        return jsonify({"error": "No image provided"}), 400
    
    ext = f.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED:
        return jsonify({"error": "Invalid image format"}), 400
    
    # Save temporary image
    temp_filename = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(f.filename)}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename)
    f.save(temp_path)
    
    try:
        # Analyze image
        analyzer = ImageAnalyzer()
        analysis = analyzer.analyze_image(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            "success": True,
            "suggestions": analysis
        })
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500

@app.route("/api/match/<int:item_id>")
def api_match(item_id):
    con=db(); item=con.execute("SELECT * FROM items WHERE id=?",(item_id,)).fetchone()
    others=con.execute("SELECT * FROM items WHERE type!=? AND status='open'",(item["type"],)).fetchall() if item else []
    con.close()
    if not item: return jsonify({"error":"not found"}),404
    return jsonify([{"item_id":o["id"],"title":o["title"],"score":match_score(item,o)[0]} for o in others])

@app.route("/handover/<handover_id>")
@login_required
def handover(handover_id):
    con=db()
    record=con.execute("""SELECT handover_records.*, items.title, items.user_id as item_user_id, claims.claimant_id
                       FROM handover_records 
                       JOIN items ON items.id=handover_records.item_id
                       JOIN claims ON claims.id=handover_records.claim_id
                       WHERE handover_records.handover_id=?""",(handover_id,)).fetchone()
    con.close()
    if not record:
        flash("Handover record not found.","danger")
        return redirect(url_for("dashboard"))
    
    # Check authorization
    u=current_user()
    if u["id"] not in [record["item_user_id"], record["claimant_id"]] and u["role"] != "admin":
        flash("You are not authorized to view this handover.","danger")
        return redirect(url_for("dashboard"))
    
    return render_template("handover.html",record=record,current_user_id=u["id"])

@app.route("/handover/<handover_id>/confirm/<role>", methods=["POST"])
@login_required
def confirm_handover(handover_id,role):
    if role not in ["finder","claimant"]:
        return redirect(url_for("dashboard"))
    
    con=db()
    record=con.execute("""SELECT handover_records.*, items.user_id as item_user_id, claims.claimant_id
                       FROM handover_records 
                       JOIN items ON items.id=handover_records.item_id
                       JOIN claims ON claims.id=handover_records.claim_id
                       WHERE handover_records.handover_id=?""",(handover_id,)).fetchone()
    
    if not record:
        con.close()
        flash("Handover record not found.","danger")
        return redirect(url_for("dashboard"))
    
    u=current_user()
    if role == "finder" and u["id"] != record["item_user_id"]:
        con.close()
        flash("You are not authorized to confirm as finder.","danger")
        return redirect(url_for("dashboard"))
    
    if role == "claimant" and u["id"] != record["claimant_id"]:
        con.close()
        flash("You are not authorized to confirm as claimant.","danger")
        return redirect(url_for("dashboard"))
    
    # Update confirmation
    if role == "finder":
        con.execute("UPDATE handover_records SET finder_confirmed=1, finder_confirmed_at=? WHERE handover_id=?",
                   (datetime.now().isoformat(timespec="seconds"),handover_id))
    else:
        con.execute("UPDATE handover_records SET claimant_confirmed=1, claimant_confirmed_at=? WHERE handover_id=?",
                   (datetime.now().isoformat(timespec="seconds"),handover_id))
    
    # Check if both confirmed
    updated=con.execute("SELECT * FROM handover_records WHERE handover_id=?",(handover_id,)).fetchone()
    if updated["finder_confirmed"] and updated["claimant_confirmed"] and not updated["completed_at"]:
        con.execute("UPDATE handover_records SET completed_at=? WHERE handover_id=?",
                   (datetime.now().isoformat(timespec="seconds"),handover_id))
    
    con.commit()
    con.close()
    flash(f"Confirmed as {role}.", "success")
    return redirect(url_for("handover",handover_id=handover_id))

@app.route("/handover/<handover_id>/qr")
@login_required
def handover_qr(handover_id):
    con=db()
    record=con.execute("SELECT * FROM handover_records WHERE handover_id=?",(handover_id,)).fetchone()
    con.close()
    
    if not record:
        flash("Handover record not found.","danger")
        return redirect(url_for("dashboard"))
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{request.host_url}handover/{handover_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

# ========== AI API Endpoints ==========

@app.route("/api/ai/analyze-image", methods=["POST"])
def ai_analyze_image():
    """AI image analysis endpoint."""
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_DIR, filename)
        file.save(filepath)
        
        try:
            # Analyze with vision service
            item_context = {
                "type": request.form.get("type", ""),
                "location": request.form.get("location", "")
            }
            analysis = vision_analyzer.analyze_image(filepath, item_context)
            fingerprint = vision_analyzer.generate_item_fingerprint(analysis)
            
            return jsonify({
                "analysis": analysis,
                "fingerprint": fingerprint,
                "success": True
            })
        except Exception as e:
            return jsonify({"error": str(e), "success": False}), 500
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/ai/semantic-search", methods=["POST"])
def ai_semantic_search():
    """AI semantic search endpoint."""
    data = request.get_json()
    query = data.get("query", "")
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        con = db()
        items = con.execute("SELECT * FROM items WHERE status='open'").fetchall()
        con.close()
        
        # Convert to dicts
        item_dicts = [dict(item) for item in items]
        
        # Perform semantic search
        results = semantic_search_engine.search_items(query, item_dicts, embedding_service)
        
        return jsonify({
            "results": [
                {
                    "item_id": r[0]["id"],
                    "title": r[0]["title"],
                    "type": r[0]["type"],
                    "relevance": r[1],
                    "explanation": r[2]
                }
                for r in results
            ],
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/api/ai/assistant", methods=["POST"])
def ai_assistant():
    """AI conversational assistant endpoint."""
    data = request.get_json()
    message = data.get("message", "")
    user_id = data.get("user_id", session.get("user_id"))
    current_state = data.get("state", {})
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        response = ai_assistant.process_message(message, user_id, current_state)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/api/ai/detect-duplicate", methods=["POST"])
def ai_detect_duplicate():
    """AI duplicate detection endpoint."""
    data = request.get_json()
    new_report = data.get("report", {})
    
    if not new_report:
        return jsonify({"error": "No report data provided"}), 400
    
    try:
        con = db()
        existing_reports = con.execute("SELECT * FROM items WHERE status='open'").fetchall()
        con.close()
        
        existing_dicts = [dict(r) for r in existing_reports]
        
        duplicates = anomaly_detector.detect_duplicate_report(
            new_report, existing_dicts, embedding_service
        )
        
        return jsonify({
            "duplicates": duplicates,
            "is_duplicate": len(duplicates) > 0,
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/api/ai/match-feedback", methods=["POST"])
@login_required
def ai_match_feedback():
    """Human feedback loop for AI matches."""
    data = request.get_json()
    match_id = data.get("match_id")
    feedback = data.get("feedback")  # "confirmed" or "rejected"
    
    if not match_id or feedback not in ["confirmed", "rejected"]:
        return jsonify({"error": "Invalid feedback data"}), 400
    
    try:
        con = db()
        con.execute("""
            UPDATE item_matches 
            SET human_feedback=?, human_feedback_at=?
            WHERE id=?
        """, (feedback, datetime.now().isoformat(timespec="seconds"), match_id))
        con.commit()
        con.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/api/ai/claim-risk", methods=["POST"])
def ai_claim_risk():
    """AI claim risk analysis endpoint."""
    data = request.get_json()
    claim = data.get("claim", {})
    item = data.get("item", {})
    user_history = data.get("user_history", [])
    
    if not claim or not item:
        return jsonify({"error": "Missing claim or item data"}), 400
    
    try:
        risk_analysis = anomaly_detector.analyze_claim_risk(claim, item, user_history)
        return jsonify({"risk_analysis": risk_analysis, "success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/ai-lab")
@login_required
def ai_lab():
    """AI demo page for project demonstration."""
    return render_template("ai_lab.html")

@app.route("/ai-explanation")
def ai_explanation():
    """AI explanation page for viva/demo."""
    return render_template("ai_explanation.html")

@app.route("/admin/ai")
@admin_required
def admin_ai():
    """AI analytics dashboard."""
    con = db()
    
    # AI analysis stats
    total_analyses = con.execute("SELECT COUNT(*) c FROM ai_analysis").fetchone()["c"]
    api_analyses = con.execute("SELECT COUNT(*) c FROM ai_analysis WHERE analysis_method='api'").fetchone()["c"]
    local_analyses = con.execute("SELECT COUNT(*) c FROM ai_analysis WHERE analysis_method='local'").fetchone()["c"]
    
    # Match stats
    total_matches = con.execute("SELECT COUNT(*) c FROM item_matches").fetchone()["c"]
    confirmed_matches = con.execute("SELECT COUNT(*) c FROM item_matches WHERE human_feedback='confirmed'").fetchone()["c"]
    rejected_matches = con.execute("SELECT COUNT(*) c FROM item_matches WHERE human_feedback='rejected'").fetchone()["c"]
    pending_feedback = con.execute("SELECT COUNT(*) c FROM item_matches WHERE human_feedback='pending'").fetchone()["c"]
    
    # Average confidence
    avg_confidence = con.execute("SELECT AVG(confidence_score) as avg FROM item_matches WHERE confidence_score IS NOT NULL").fetchone()["avg"] or 0
    
    # Recent matches
    recent_matches = con.execute("""
        SELECT item_matches.*, 
               lost.title as lost_title, found.title as found_title
        FROM item_matches
        JOIN items lost ON lost.id=item_matches.lost_item_id
        JOIN items found ON found.id=item_matches.found_item_id
        ORDER BY item_matches.id DESC LIMIT 10
    """).fetchall()
    
    con.close()
    
    return render_template("admin_ai.html",
                         total_analyses=total_analyses,
                         api_analyses=api_analyses,
                         local_analyses=local_analyses,
                         total_matches=total_matches,
                         confirmed_matches=confirmed_matches,
                         rejected_matches=rejected_matches,
                         pending_feedback=pending_feedback,
                         avg_confidence=round(avg_confidence * 100, 1),
                         recent_matches=recent_matches)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED

if __name__=="__main__":
    init_db()
    seed_demo_accounts()
    app.run(debug=True, host="127.0.0.1", port=5000)
