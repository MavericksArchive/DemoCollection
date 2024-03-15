from flask import Flask, render_template, redirect, request, session, jsonify
# The Session instance is not used for direct access, you should always use flask.session
from flask_session import Session
import json
 
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
 
 
@app.route("/")
def index():
    if not session.get("name"):
        return redirect("/login")
    return render_template('index.html')
 
 
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        import pdb; pdb.set_trace()
        session["name"] = request.form.get("name")
        return jsonify({
            "message": json.loads(json.dumps(f'login_name: {session["name"]}'))
        }), 200
 
 
@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8888)