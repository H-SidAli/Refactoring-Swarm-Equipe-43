"""
Generator Agent - Code Generation Specialist.
Creates new code artifacts: tests, documentation, utilities.
"""

from src.agents.base import BaseAgent
from src.utils.logger import ActionType


class GeneratorAgent(BaseAgent):
    """
    Agent responsible for generating new code.
    Creates tests, documentation, and utility functions.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        super().__init__(name="Generator", model_name=model_name)

    def get_system_prompt(self) -> str:
        return """Tu es un expert en génération de code Python. Tu crées du code de haute qualité:

STANDARDS DE GÉNÉRATION:
1. Code conforme PEP 8 et PEP 257 (docstrings)
2. Type hints sur toutes les fonctions et méthodes
3. Gestion d'erreurs appropriée
4. Tests unitaires avec pytest
5. Documentation claire et complète

FORMAT DE RÉPONSE pour la génération de code:
```
## 📝 CODE GÉNÉRÉ

### Description
Brève explication de ce qui a été créé

### Code
```python
# Code généré
```

### Utilisation
```python
# Exemple d'utilisation
```
```

FORMAT DE RÉPONSE pour les tests:
```
## 🧪 TESTS GÉNÉRÉS

### Couverture
- Fonction/Méthode testée
- Cas de test couverts

### Code des Tests
```python
# Tests pytest
```

### Exécution
`pytest <fichier_test.py> -v`
```

Génère du code production-ready, pas des prototypes."""

    def get_action_type(self) -> ActionType:
        return ActionType.GENERATION

    def generate_tests(self, file_path: str, code_content: str) -> str:
        """
        Generate unit tests for the given code.

        Args:
            file_path (str): Path to the source file.
            code_content (str): Source code to test.

        Returns:
            str: Generated pytest test file content.
        """
        prompt = f"""Génère des tests unitaires pytest pour le fichier suivant:

**Fichier source**: `{file_path}`

```python
{code_content}
```

Crée des tests complets couvrant:
1. Cas nominaux (happy path)
2. Cas limites (edge cases)
3. Gestion d'erreurs (exceptions attendues)
4. Cas de données invalides

Utilise des fixtures pytest si approprié."""

        return self.invoke(prompt)

    def generate_docstrings(self, file_path: str, code_content: str) -> str:
        """
        Add or improve docstrings in the code.

        Args:
            file_path (str): Path to the file.
            code_content (str): Source code.

        Returns:
            str: Code with improved docstrings.
        """
        prompt = f"""Ajoute ou améliore les docstrings dans le fichier suivant:

**Fichier**: `{file_path}`

```python
{code_content}
```

Utilise le format Google-style docstrings:
- Description courte
- Args avec types et descriptions
- Returns avec type et description
- Raises si applicable
- Examples si utile

Retourne le fichier complet avec les docstrings ajoutées."""

        return self.invoke(prompt)

    def generate_utility(self, description: str, context: str = "") -> str:
        """
        Generate a utility function or class.

        Args:
            description (str): What the utility should do.
            context (str): Optional context about the project.

        Returns:
            str: Generated utility code.
        """
        prompt = f"""Génère une fonction/classe utilitaire Python:

**Description**: {description}

**Contexte du projet**: {context if context else "Projet de refactoring de code Python"}

Génère du code complet avec:
- Type hints
- Docstrings
- Gestion d'erreurs
- Exemple d'utilisation"""

        return self.invoke(prompt)
