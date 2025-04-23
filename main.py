from flask import Flask , jsonify , render_template
from src.routes.otakudesu import otakudesu_print
from src.routes.kuramanime import kuramanime_print

app = Flask(__name__)

app.register_blueprint(otakudesu_print, url_prefix='/api/otkd')
app.register_blueprint(kuramanime_print, url_prefix='/api/krm')


if __name__ == '__main__':
  app.run(debug=True)
  #app.run(host='0.0.0.0', port=5005)