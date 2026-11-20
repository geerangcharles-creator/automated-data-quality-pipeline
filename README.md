# Automated Data Quality Pipeline — V1

Application Python de diagnostic de qualité des fichiers **CSV** et **Excel (.xlsx)**. Elle automatise le profilage, les contrôles et les recommandations sans modifier les données d'origine.

## Installation (Windows / PowerShell)

```powershell
cd automated-data-quality-pipeline
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Si PowerShell bloque l'activation : `.venv\Scripts\python.exe -m streamlit run app.py` (après installation avec le Python du venv).

## Installation (Ubuntu)

```bash
cd automated-data-quality-pipeline
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Le terminal affiche l'adresse locale (habituellement `http://localhost:8501`). Importer `data/sample_data.csv` pour la première démonstration.

## Fonctionnement

1. Importer CSV ou Excel (choisir une feuille pour Excel).
2. Pour CSV, corriger si nécessaire séparateur et encodage.
3. Choisir les colonnes de détection des doublons métier.
4. Lire le profil, les anomalies et les recommandations.
5. Télécharger le rapport HTML et le récapitulatif CSV.
6. Dans l'onglet **Investigation**, choisir une colonne numérique atypique, examiner les lignes concernées avec leur contexte et exporter les observations filtrées. Le fichier CSV d'investigation contient les lignes sources et peut inclure des données sensibles.

## Structure

```text
app.py                         Interface Streamlit et graphiques Plotly
src/file_loader.py             Lecture CSV/Excel et erreurs explicites
src/data_profiler.py           Profilage et statistiques
src/quality_checker.py         Manquants, doublons, chaînes vides, types, IQR
src/recommendations.py         Conseils contextualisés sans correction
src/report_generator.py        Exports HTML et CSV
tests/                        Tests automatisés Pytest
data/sample_data.csv           Données fictives de démonstration
```

## Tests

```bash
python -m pytest -q
```

## Interprétation des contrôles

- **Manquant** : valeur `NaN`/vide reconnue par Pandas ; la chaîne contenant seulement des espaces figure séparément dans « chaînes vides ».
- **Doublon supplémentaire** : occurrences répétées après la première, par groupe. « Lignes impliquées » inclut aussi la première occurrence de chaque groupe.
- **Types suspects** : sur une colonne contenant des chaînes, présence d'un mélange de valeurs convertibles en nombres et non convertibles. Ce contrôle est indicatif.
- **Valeurs atypiques** : règle IQR (bornes Q1 − 1,5×IQR et Q3 + 1,5×IQR), appliquée seulement à des colonnes numériques avec au moins quatre observations et un IQR non nul.
- **Colonne constante** : une seule valeur distincte renseignée ; **quasi constante** : une valeur majoritaire au moins à 95 % (minimum 10 valeurs renseignées).
- **Formats suspects** : contrôle simple des dates et emails lorsque leur nom de colonne le suggère ; formats de dates mélangés ou dates invalides. Les formats de dates ambigus demandent une validation humaine.
- **Espaces parasites et casse** : espaces en début/fin de chaîne et catégories qui ne diffèrent que par les majuscules/minuscules.
- **Nombres négatifs et zéros** : comptages indicatifs sur les colonnes numériques, sans considérer ces valeurs automatiquement erronées.
- **Cardinalité élevée** : au moins 90 % de valeurs distinctes dans une colonne contenant 20 valeurs renseignées ou plus.
- **Analyse ciblée** : profils et anomalies par colonne pour la sélection ; recherche de doublons indépendante, sur le fichier complet et les clés choisies.
- **Recommandations** : règles explicites et prudentes, notamment pour identifiants, dates et montants. Aucune suppression, imputation ou conversion n'est appliquée.

## Sécurité, confidentialité et limites

- Traitement en mémoire ; les fichiers importés ne sont pas écrits sur disque par le code de l'application. Les paramètres de déploiement Streamlit peuvent avoir leurs propres règles d'hébergement.
- Ne jamais publier de fichiers confidentiels dans Git. `.gitignore` ignore les données ajoutées et les rapports exportés ; seule la donnée fictive `sample_data.csv` est suivie.
- Les exports incluent des **statistiques** et des **conseils**, pas les lignes brutes, mais les noms de colonnes et le nom du fichier peuvent eux-mêmes être sensibles.
- Le contrôle générique ne connaît ni les clés métier réelles, ni les règles comptables, ni les formats de dates propres à l'entreprise.
- Sur des très gros fichiers, la mémoire et le temps de traitement peuvent être limitants ; pour une V2, prévoir un mode volumétrie et des règles configurables.
- **Performances V1.4** : le chargement et les résultats de contrôle sont conservés pendant la session Streamlit, et les doublons sont calculés indépendamment. Changer un filtre d'affichage ne relance plus l'intégralité de l'analyse. La première importation Excel reste potentiellement longue et les résultats en mémoire occupent de la RAM ; un nouveau chargement de fichier invalide le cache de session.
- CSV : détection automatique du séparateur indicative ; choisir explicitement le séparateur en cas de doute. Certains encodages mono-octet peuvent masquer des erreurs d'encodage.
- Excel : `.xlsx` uniquement ; formules lues selon les valeurs mises en cache par le classeur.

## Évolutions possibles

V2 : nettoyage interactif, prévisualisation avant/après et journal des validations. V3 : contrôles statistiques plus avancés. V4 : traitement par lots et historique, selon besoin métier.

## GitHub

Avant un premier `git push`, vérifier avec `git status` et `git diff --cached --name-only` qu'aucune donnée réelle ou secret ne figure dans l'index. Le projet est livré sans dépôt distant configuré.
