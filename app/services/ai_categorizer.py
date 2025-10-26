"""
AI Transaction Categorizer Agent
Uses machine learning to auto-categorize transactions based on payee patterns
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
import os
from pathlib import Path
from datetime import datetime
from app.models import Transaction, Category, CategorizationRule
from app import db
import re

class AICategorizerAgent:
    def __init__(self):
        self.model_path = Path(__file__).parent.parent.parent / 'data' / 'ml_models'
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.classifier_file = self.model_path / 'categorizer.pkl'
        self.vectorizer_file = self.model_path / 'vectorizer.pkl'
        self.pipeline = None
        self.label_map = {}

    def normalize_payee(self, payee):
        """Normalize payee name for better matching"""
        # Remove numbers, special characters, extra spaces
        payee = re.sub(r'[0-9#*-]', '', payee)
        payee = re.sub(r'\s+', ' ', payee)
        return payee.strip().lower()

    def learn_from_existing_transactions(self):
        """Train model from all categorized transactions"""
        # Get all transactions with categories
        transactions = Transaction.query.filter(Transaction.category_id.isnot(None)).all()

        if len(transactions) < 10:
            return False, "Need at least 10 categorized transactions to train model"

        # Prepare training data
        X = []
        y = []
        category_counts = {}

        for trans in transactions:
            normalized_payee = self.normalize_payee(trans.payee)
            X.append(normalized_payee)
            y.append(trans.category_id)
            category_counts[trans.category_id] = category_counts.get(trans.category_id, 0) + 1

        # Build label map for category IDs to names
        categories = Category.query.all()
        self.label_map = {cat.id: cat.name for cat in categories}

        # Create and train pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
            ('clf', MultinomialNB())
        ])

        self.pipeline.fit(X, y)

        # Save model
        with open(self.classifier_file, 'wb') as f:
            pickle.dump(self.pipeline, f)

        with open(self.model_path / 'label_map.pkl', 'wb') as f:
            pickle.dump(self.label_map, f)

        return True, f"Model trained on {len(transactions)} transactions across {len(category_counts)} categories"

    def load_model(self):
        """Load pre-trained model"""
        if not self.classifier_file.exists():
            return False

        with open(self.classifier_file, 'rb') as f:
            self.pipeline = pickle.load(f)

        with open(self.model_path / 'label_map.pkl', 'rb') as f:
            self.label_map = pickle.load(f)

        return True

    def predict_category(self, payee, transaction_type='withdrawal'):
        """Predict category for a payee"""
        # Try loading model if not loaded
        if self.pipeline is None:
            if not self.load_model():
                # No model trained yet, try to train
                success, message = self.learn_from_existing_transactions()
                if not success:
                    return None, 0.0, message

        # Check for exact rule match first
        rule = self.find_matching_rule(payee)
        if rule:
            rule.usage_count += 1
            rule.last_used_at = datetime.utcnow()
            db.session.commit()
            return rule.category_id, rule.confidence_score, f"Matched rule: {rule.payee_pattern}"

        # Use ML model
        normalized = self.normalize_payee(payee)

        try:
            # Get prediction with probability
            category_id = self.pipeline.predict([normalized])[0]
            probabilities = self.pipeline.predict_proba([normalized])[0]
            confidence = max(probabilities)

            return int(category_id), float(confidence), "ML prediction"
        except Exception as e:
            return None, 0.0, f"Prediction error: {str(e)}"

    def find_matching_rule(self, payee):
        """Find existing categorization rule for payee"""
        normalized = self.normalize_payee(payee)

        # Check for exact matches
        rules = CategorizationRule.query.all()
        for rule in rules:
            rule_pattern = self.normalize_payee(rule.payee_pattern)
            if rule_pattern in normalized or normalized in rule_pattern:
                return rule

        return None

    def create_rule(self, payee, category_id, confidence=1.0, auto_learned=False):
        """Create new categorization rule"""
        normalized = self.normalize_payee(payee)

        # Check if rule already exists
        existing = self.find_matching_rule(payee)
        if existing:
            # Update existing rule
            existing.category_id = category_id
            existing.confidence_score = confidence
            existing.usage_count += 1
            existing.last_used_at = datetime.utcnow()
        else:
            # Create new rule
            rule = CategorizationRule(
                payee_pattern=normalized,
                category_id=category_id,
                confidence_score=confidence,
                is_auto_learned=auto_learned,
                usage_count=1,
                last_used_at=datetime.utcnow()
            )
            db.session.add(rule)

        db.session.commit()

        # Retrain model with new data
        self.learn_from_existing_transactions()

    def auto_categorize_transactions(self, min_confidence=0.6):
        """Auto-categorize all uncategorized transactions"""
        uncategorized = Transaction.query.filter(Transaction.category_id.is_(None)).all()

        categorized_count = 0
        low_confidence_count = 0

        for trans in uncategorized:
            category_id, confidence, source = self.predict_category(trans.payee, trans.transaction_type)

            if category_id and confidence >= min_confidence:
                trans.category_id = category_id
                categorized_count += 1
            elif category_id:
                low_confidence_count += 1

        if categorized_count > 0:
            db.session.commit()

        return {
            'categorized': categorized_count,
            'low_confidence': low_confidence_count,
            'total_uncategorized': len(uncategorized)
        }

    def get_suggestions(self, payee, top_n=3):
        """Get top N category suggestions for a payee"""
        if self.pipeline is None:
            if not self.load_model():
                return []

        normalized = self.normalize_payee(payee)

        try:
            # Get probabilities for all categories
            probabilities = self.pipeline.predict_proba([normalized])[0]
            category_ids = self.pipeline.classes_

            # Sort by probability
            suggestions = []
            for cat_id, prob in zip(category_ids, probabilities):
                category = Category.query.get(int(cat_id))
                if category:
                    suggestions.append({
                        'category_id': int(cat_id),
                        'category_name': category.name,
                        'confidence': float(prob),
                        'confidence_pct': f"{prob * 100:.1f}%"
                    })

            # Sort by confidence and return top N
            suggestions.sort(key=lambda x: x['confidence'], reverse=True)
            return suggestions[:top_n]

        except Exception as e:
            return []
