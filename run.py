from app import create_app, db
from app.models import Account, Transaction, Category

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Account': Account, 'Transaction': Transaction, 'Category': Category}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('FLASK_PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
